#!/usr/bin/env python3
"""Importa termodinámica evaluada de NIST Chemistry WebBook por elemento.

La identidad CAS se resuelve desde el registro de elemento de PubChem PUG View.
Los datos se guardan exclusivamente en ``data/elements/<elemento>/thermodynamics.csv``.

Se importan, cuando existen:
- magnitudes tabuladas de fase condensada;
- entalpías y entropías estándar;
- temperaturas y entalpías de transición;
- coeficientes Shomate A-H, conservando fase e intervalo de temperatura.

Una respuesta vacía o un fallo de red nunca elimina registros NIST ya versionados.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_ROOT = ROOT / "data" / "elements"
MANIFEST_PATH = ELEMENTS_ROOT / "elements.manifest.csv"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

PUG_VIEW_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/element/{z}/JSON/"
WEBBOOK_URL = "https://webbook.nist.gov/cgi/cbook.cgi?ID=C{cas_digits}&Units=SI&Mask=2"
CAS_RE = re.compile(r"\b\d{2,7}-\d{2}-\d\b")
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][-+]?\d+)?")

FIELDS = [
    "property", "value", "unit", "temperature_k", "pressure", "phase",
    "source", "source_url", "retrieved_at", "notes",
]


class WebBookTableParser(HTMLParser):
    """Captura tablas y el encabezado H2/H3 que les da contexto científico."""

    def __init__(self) -> None:
        super().__init__()
        self.h2 = ""
        self.h3 = ""
        self._heading_tag = ""
        self._heading_parts: list[str] = []
        self._in_table = False
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._table_rows: list[list[str]] = []
        self._table_h2 = ""
        self._table_h3 = ""
        self.tables: list[tuple[str, str, list[list[str]]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"h2", "h3"}:
            self._heading_tag = lowered
            self._heading_parts = []
        elif lowered == "table":
            self._in_table = True
            self._table_rows = []
            self._table_h2 = self.h2
            self._table_h3 = self.h3
        elif lowered == "tr" and self._in_table:
            self._row = []
        elif lowered in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._heading_tag:
            self._heading_parts.append(data)
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == self._heading_tag:
            value = clean(" ".join(self._heading_parts))
            if lowered == "h2":
                self.h2 = value
                self.h3 = ""
            elif lowered == "h3":
                self.h3 = value
            self._heading_tag = ""
            self._heading_parts = []
        elif lowered in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(clean(" ".join(self._cell)))
            self._cell = None
        elif lowered == "tr" and self._row is not None:
            if any(self._row):
                self._table_rows.append(self._row)
            self._row = None
            self._cell = None
        elif lowered == "table" and self._in_table:
            if self._table_rows:
                self.tables.append((self._table_h2, self._table_h3, self._table_rows))
            self._in_table = False
            self._table_rows = []


def clean(value: Any) -> str:
    return "" if value is None else re.sub(r"\s+", " ", str(value).replace("\ufeff", "")).strip()


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        return [{clean(k): clean(v) for k, v in row.items() if k} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    extras = sorted({key for row in rows for key in row if key not in FIELDS})
    columns = FIELDS + extras
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean(row.get(column)) for column in columns})


def fetch(url: str, timeout: int = 60) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TablaElementos/0.4 NIST-WebBook-import"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def walk_strings(node: Any, path: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(node, dict):
        heading = clean(node.get("TOCHeading"))
        next_path = path + ((heading,) if heading else ())
        for key, value in node.items():
            if isinstance(value, str):
                result.append((" / ".join(next_path + (key,)), value))
            else:
                result.extend(walk_strings(value, next_path))
    elif isinstance(node, list):
        for value in node:
            result.extend(walk_strings(value, path))
    elif isinstance(node, str):
        result.append((" / ".join(path), node))
    return result


def resolve_cas(element: dict[str, str]) -> str:
    url = PUG_VIEW_URL.format(z=element["atomic_number"])
    try:
        payload = json.loads(fetch(url, timeout=45))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return ""

    candidates: list[tuple[int, str]] = []
    for path, text in walk_strings(payload):
        match = CAS_RE.search(clean(text))
        if not match:
            continue
        score = 0
        normalized_path = path.lower()
        if "cas" in normalized_path:
            score += 10
        if "identifier" in normalized_path:
            score += 3
        candidates.append((score, match.group(0)))
    if not candidates:
        return ""
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def phase_from_context(h2: str, h3: str, quantity: str = "") -> str:
    text = f"{h2} {h3} {quantity}".lower()
    if "liquid" in text:
        return "liquid"
    if "solid" in text or "condensed" in text or "crystal" in text:
        return "solid"
    if "gas" in text:
        return "gas"
    return ""


def normalized_scientific(value: str) -> str:
    text = clean(value).replace("−", "-")
    # NIST HTML puede representar 1.23×10^{-4} como texto visible.
    match = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)\s*[×x]\s*10\s*\^?\s*\{?([-+]?\d+)\}?", text)
    if match:
        return f"{match.group(1)}e{match.group(2)}"
    return text


def slug(text: str) -> str:
    value = text.lower()
    replacements = {
        "δ": "delta", "Δ": "delta", "°": "", "ₚ": "p", "ₗ": "l",
        "α": "alpha", "β": "beta", "γ": "gamma", "·": "_",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def property_id_for_quantity(quantity: str, phase: str) -> str:
    compact = quantity.lower().replace(" ", "")
    suffix = f"_{phase}" if phase else ""
    if "δfh" in compact or "deltafh" in compact:
        return f"standard_enthalpy_formation{suffix}"
    if compact.startswith("s") and ("1bar" in compact or "°" in quantity):
        return f"standard_molar_entropy{suffix}"
    if "δfush" in compact or "fus" in compact and "h" in compact:
        return "enthalpy_fusion"
    if "δvaph" in compact or "vap" in compact and "h" in compact:
        return "enthalpy_vaporization"
    if "δsubh" in compact or "sub" in compact and "h" in compact:
        return "enthalpy_sublimation"
    if "tboil" in compact or "boiling" in compact:
        return "boiling_point"
    if "tfus" in compact or "melting" in compact or "fusiontemperature" in compact:
        return "melting_point"
    if compact.startswith("cp") or "heatcapacity" in compact:
        return f"heat_capacity_cp{suffix}"
    return f"nist_webbook_{slug(quantity)}{suffix}"


def base_record(
    property_id: str,
    value: str,
    unit: str,
    phase: str,
    url: str,
    notes: str,
    *,
    temperature: str = "",
) -> dict[str, str]:
    return {
        "property": property_id,
        "value": normalized_scientific(value),
        "unit": clean(unit),
        "temperature_k": clean(temperature),
        "pressure": "",
        "phase": phase,
        "source": "NIST Chemistry WebBook",
        "source_url": url,
        "retrieved_at": NOW,
        "notes": clean(notes),
    }


def parse_quantity_table(
    h2: str,
    h3: str,
    rows: list[list[str]],
    url: str,
) -> list[dict[str, str]]:
    if not rows:
        return []
    header = [clean(cell).lower() for cell in rows[0]]
    if not any("quantity" in cell for cell in header) or not any("value" in cell for cell in header):
        return []

    result: list[dict[str, str]] = []
    for cells in rows[1:]:
        padded = cells + [""] * max(0, 6 - len(cells))
        quantity, value, unit, method, reference, comment = padded[:6]
        if not quantity or not value:
            continue
        phase = phase_from_context(h2, h3, quantity)
        property_id = property_id_for_quantity(quantity, phase)
        notes = " · ".join(
            part for part in [
                f"Cantidad NIST: {quantity}",
                f"Método: {method}" if method else "",
                f"Referencia: {reference}" if reference else "",
                comment,
            ] if part
        )
        result.append(base_record(property_id, value, unit, phase, url, notes))
    return result


def parse_shomate_table(
    h2: str,
    h3: str,
    rows: list[list[str]],
    url: str,
) -> list[dict[str, str]]:
    if not rows or "shomate" not in h3.lower():
        return []

    temperature_row_index = next(
        (index for index, row in enumerate(rows) if row and "temperature" in clean(row[0]).lower()),
        -1,
    )
    if temperature_row_index < 0:
        return []
    temperature_row = rows[temperature_row_index]
    ranges = temperature_row[1:]
    if not ranges:
        return []

    coefficient_rows: dict[str, list[str]] = {}
    reference_rows: dict[str, list[str]] = {}
    for row in rows[temperature_row_index + 1:]:
        if not row:
            continue
        key = clean(row[0])
        if key in set("ABCDEFGH"):
            coefficient_rows[key] = row[1:]
        elif key.lower() in {"reference", "comment"}:
            reference_rows[key.lower()] = row[1:]

    if not coefficient_rows:
        return []

    phase = phase_from_context(h2, h3)
    result: list[dict[str, str]] = []
    for index, temperature_range in enumerate(ranges, start=1):
        reference = reference_rows.get("reference", [])
        comments = reference_rows.get("comment", [])
        note = " · ".join(
            part for part in [
                "Coeficiente de la ecuación Shomate publicada por NIST.",
                f"Referencia: {reference[index - 1]}" if len(reference) >= index else "",
                comments[index - 1] if len(comments) >= index else "",
            ] if part
        )
        for coefficient, values in coefficient_rows.items():
            if len(values) < index or not clean(values[index - 1]):
                continue
            unit = "kJ/mol" if coefficient in {"F", "H"} else "J/(mol·K)"
            result.append(
                base_record(
                    f"shomate_{coefficient}_{phase or 'unspecified'}_{index}",
                    values[index - 1],
                    unit,
                    phase,
                    url,
                    note,
                    temperature=temperature_range,
                )
            )
    return result


def parse_webbook(data: bytes, url: str) -> list[dict[str, str]]:
    parser = WebBookTableParser()
    parser.feed(data.decode("utf-8", errors="replace"))
    result: list[dict[str, str]] = []
    for h2, h3, rows in parser.tables:
        result.extend(parse_quantity_table(h2, h3, rows, url))
        result.extend(parse_shomate_table(h2, h3, rows, url))
    return result


def enrich_element(element: dict[str, str]) -> tuple[str, int, str]:
    cas = resolve_cas(element)
    if not cas:
        return element["symbol"], 0, "sin CAS"
    url = WEBBOOK_URL.format(cas_digits=cas.replace("-", ""))
    try:
        generated = parse_webbook(fetch(url, timeout=70), url)
    except (urllib.error.URLError, TimeoutError):
        return element["symbol"], 0, "sin respuesta NIST"
    if not generated:
        return element["symbol"], 0, "sin termodinámica tabular"

    path = ELEMENTS_ROOT / element["folder"] / "thermodynamics.csv"
    rows = read_csv(path)
    # Solo se sustituye NIST cuando la nueva consulta produjo registros.
    rows = [row for row in rows if clean(row.get("source")) != "NIST Chemistry WebBook"]
    rows.extend(generated)
    write_csv(path, rows)
    return element["symbol"], len(generated), cas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    elements = read_manifest()
    total = 0
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as executor:
        futures = {executor.submit(enrich_element, element): element for element in elements}
        for index, future in enumerate(as_completed(futures), start=1):
            symbol, count, status = future.result()
            total += count
            print(f"[{index:03d}/118] {symbol} · {count} registros · {status}")
            time.sleep(0.02)

    print(f"NIST Chemistry WebBook: {total} registros termodinámicos importados.")


if __name__ == "__main__":
    main()
