#!/usr/bin/env python3
"""Enriquece la fase científica 2 dentro de cada carpeta de elemento.

Ámbitos:
- termodinámica y transiciones de fase;
- energías características de rayos X;
- atenuación de fotones;
- dispersión y absorción de neutrones;
- importación de exportaciones XPS/Auger;
- reparación opcional de espectros ópticos NIST vacíos.

Los datos se escriben exclusivamente en ``data/elements/<elemento>/``. Las
consultas de red son opcionales y tolerantes a fallos; la construcción offline
continúa utilizando los CSV ya versionados.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_ROOT = ROOT / "data" / "elements"
MANIFEST_PATH = ELEMENTS_ROOT / "elements.manifest.csv"
XPS_IMPORT_ROOT = ROOT / "data" / "import" / "xps"

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][-+]?\d+)?")
TRANSITION_RE = re.compile(r"^[KLMN][KLMN]\d?$", re.IGNORECASE)

THERMO_FIELDS = [
    "property", "value", "unit", "temperature_k", "pressure", "phase",
    "source", "source_url", "retrieved_at", "notes",
]
RADIATION_FIELDS = [
    "property", "value", "unit", "energy", "particle_or_photon", "isotope",
    "transition", "process", "source", "source_url", "retrieved_at", "notes",
]
SPECTRAL_FIELDS = [
    "element", "species", "obs_wl_nm", "ritz_wl_nm", "intensity", "transition",
    "lower_level", "upper_level", "source", "source_url", "retrieved_at", "notes",
]

PUG_VIEW_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/element/{z}/JSON/"
XRAY_TRANSITION_URL = "https://physics.nist.gov/cgi-bin/XrayTrans/search.pl"
XRAY_ATTENUATION_URL = "https://physics.nist.gov/PhysRefData/XrayMassCoef/ElemTab/z{z:02d}.html"
NEUTRON_TABLE_URL = "https://www.ncnr.nist.gov/resources/activation/scattering_table.html"
NIST_LINES_URL = "https://physics.nist.gov/cgi-bin/ASD/lines1.pl"


class HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self._row = []
        elif tag.lower() in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(clean(" ".join(self._cell)))
            self._cell = None
        elif lowered == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None
            self._cell = None


def clean(value: Any) -> str:
    return "" if value is None else re.sub(r"\s+", " ", str(value).replace("\ufeff", "")).strip()


def numeric(value: Any) -> float | None:
    match = NUMBER_RE.search(clean(value).replace("−", "-").replace(" ", ""))
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", "."))
    except ValueError:
        return None


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        return [{clean(k): clean(v) for k, v in row.items() if k} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], preferred_fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    extras = sorted({key for row in rows for key in row if key not in preferred_fields})
    fields = preferred_fields + extras
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field)) for field in fields})


def replace_source_rows(rows: list[dict[str, str]], source: str, properties: set[str] | None = None) -> list[dict[str, str]]:
    return [
        row for row in rows
        if not (
            clean(row.get("source")) == source
            and (properties is None or clean(row.get("property")) in properties)
        )
    ]


def fetch(url: str, *, timeout: int = 70, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TablaElementos/0.4 scientific-enrichment", **(headers or {})},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def parse_html_rows(data: bytes) -> list[list[str]]:
    parser = HtmlTableParser()
    parser.feed(data.decode("utf-8", errors="replace"))
    return parser.rows


def base_row(property_id: str, value: Any, unit: str, source: str, url: str, notes: str = "") -> dict[str, str]:
    return {
        "property": property_id,
        "value": clean(value),
        "unit": unit,
        "source": source,
        "source_url": url,
        "retrieved_at": NOW,
        "notes": clean(notes),
    }


def copy_local_phase_landmarks(element: dict[str, str]) -> None:
    folder = ELEMENTS_ROOT / element["folder"]
    physical = read_csv(folder / "physical_properties.csv")
    thermo_path = folder / "thermodynamics.csv"
    rows = read_csv(thermo_path)
    ids = {"melting_point", "boiling_point", "standard_state", "density"}
    rows = [row for row in rows if not (row.get("source") == "TablaElementos · consolidación local" and row.get("property") in ids)]
    for row in physical:
        property_id = clean(row.get("property"))
        if property_id not in ids or not clean(row.get("value")):
            continue
        rows.append({
            **base_row(
                property_id,
                row.get("value"),
                row.get("unit", ""),
                "TablaElementos · consolidación local",
                row.get("source_url", ""),
                f"Copiado de physical_properties.csv. Fuente original: {row.get('source', 'no indicada')}. {row.get('notes', '')}",
            ),
            "temperature_k": row.get("temperature_k", ""),
            "pressure": row.get("pressure", ""),
            "phase": row.get("phase", ""),
        })
    write_csv(thermo_path, rows, THERMO_FIELDS)


def extract_pug_entries(node: Any, path: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(node, dict):
        heading = clean(node.get("TOCHeading"))
        next_path = path + ((heading,) if heading else ())
        information = node.get("Information")
        if isinstance(information, list):
            for item in information:
                if not isinstance(item, dict):
                    continue
                value = item.get("Value") or {}
                if isinstance(value, dict):
                    strings = value.get("StringWithMarkup")
                    if isinstance(strings, list):
                        for entry in strings:
                            text = clean(entry.get("String")) if isinstance(entry, dict) else ""
                            if text:
                                result.append((" / ".join(next_path), text))
                    number = value.get("Number")
                    if isinstance(number, list) and number:
                        unit = clean(value.get("Unit"))
                        result.append((" / ".join(next_path), f"{number[0]} {unit}".strip()))
        for child in node.values():
            result.extend(extract_pug_entries(child, next_path))
    elif isinstance(node, list):
        for child in node:
            result.extend(extract_pug_entries(child, path))
    return result


THERMO_HEADING_MAP = (
    (("heat of fusion", "enthalpy of fusion"), "enthalpy_fusion", "kJ/mol"),
    (("heat of vaporization", "enthalpy of vaporization", "heat of evaporation"), "enthalpy_vaporization", "kJ/mol"),
    (("heat of sublimation", "enthalpy of sublimation"), "enthalpy_sublimation", "kJ/mol"),
    (("heat capacity", "specific heat"), "heat_capacity_cp", "J/(mol·K)"),
    (("entropy",), "standard_molar_entropy", "J/(mol·K)"),
    (("triple point",), "triple_point", ""),
    (("critical temperature",), "critical_temperature", "K"),
    (("critical pressure",), "critical_pressure", "Pa"),
    (("vapor pressure", "vapour pressure"), "vapor_pressure", ""),
)


def enrich_pubchem_thermodynamics(element: dict[str, str]) -> None:
    z = int(element["atomic_number"])
    url = PUG_VIEW_URL.format(z=z)
    try:
        payload = json.loads(fetch(url, timeout=50))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return
    entries = extract_pug_entries(payload)
    path = ELEMENTS_ROOT / element["folder"] / "thermodynamics.csv"
    rows = replace_source_rows(read_csv(path), "PubChem PUG View · termodinámica")
    seen: dict[str, int] = {}
    for heading, text in entries:
        key = heading.lower()
        for needles, property_id, default_unit in THERMO_HEADING_MAP:
            if not any(needle in key for needle in needles):
                continue
            seen[property_id] = seen.get(property_id, 0) + 1
            suffix = f"_{seen[property_id]}" if seen[property_id] > 1 else ""
            number = numeric(text)
            value = number if number is not None else text
            unit_match = re.search(r"(?:kJ/mol|J/(?:mol|g)[·/]?K|J mol-1 K-1|K|°C|MPa|kPa|Pa|bar|atm)", text, re.I)
            unit = clean(unit_match.group(0)) if unit_match else default_unit
            rows.append({
                **base_row(f"{property_id}{suffix}", value, unit, "PubChem PUG View · termodinámica", url, text),
                "temperature_k": "",
                "pressure": "",
                "phase": "",
            })
            break
    write_csv(path, rows, THERMO_FIELDS)


def parse_xray_attenuation(element: dict[str, str]) -> list[dict[str, str]]:
    z = int(element["atomic_number"])
    if z > 92:
        return []
    url = XRAY_ATTENUATION_URL.format(z=z)
    try:
        table_rows = parse_html_rows(fetch(url, timeout=50))
    except (urllib.error.URLError, TimeoutError):
        return []
    result: list[dict[str, str]] = []
    for cells in table_rows:
        numbers = [numeric(cell) for cell in cells]
        numeric_values = [value for value in numbers if value is not None]
        if len(numeric_values) < 3:
            continue
        energy, mu, mu_en = numeric_values[:3]
        if energy <= 0 or mu < 0 or mu_en < 0:
            continue
        edge = next((cell for cell in cells if re.fullmatch(r"[KLMN]\d?", clean(cell), re.I)), "")
        common = {
            "energy": f"{energy:.12g} MeV",
            "particle_or_photon": "fotón",
            "isotope": "natural",
            "transition": edge,
            "process": "atenuación total",
            "source": "NIST X-Ray Mass Attenuation Coefficients",
            "source_url": url,
            "retrieved_at": NOW,
            "notes": f"Tabla elemental NIST; borde de absorción {edge}." if edge else "Tabla elemental NIST.",
        }
        result.append({**common, "property": "mass_attenuation_coefficient", "value": f"{mu:.12g}", "unit": "cm²/g"})
        result.append({**common, "property": "mass_energy_absorption_coefficient", "value": f"{mu_en:.12g}", "unit": "cm²/g", "process": "absorción de energía"})
    return result


def normalized_transition(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", clean(text)).upper()


def parse_xray_transitions(element: dict[str, str]) -> list[dict[str, str]]:
    z = int(element["atomic_number"])
    if z < 10 or z > 100:
        return []
    params = urllib.parse.urlencode({"element": element["symbol"], "trans": "All", "units": "eV"})
    url = f"{XRAY_TRANSITION_URL}?{params}"
    try:
        table_rows = parse_html_rows(fetch(url, timeout=50))
    except (urllib.error.URLError, TimeoutError):
        return []
    result: list[dict[str, str]] = []
    for cells in table_rows:
        transition = ""
        transition_index = -1
        for index, cell in enumerate(cells):
            candidate = normalized_transition(cell)
            if TRANSITION_RE.fullmatch(candidate) or candidate.endswith("EDGE"):
                transition, transition_index = candidate, index
                break
        if not transition:
            continue
        values = [numeric(cell) for cell in cells[transition_index + 1:]]
        energies = [value for value in values if value is not None and value > 0]
        if not energies:
            continue
        theoretical = energies[0]
        experimental = energies[1] if len(energies) > 1 else None
        chosen = experimental or theoretical
        result.append({
            **base_row("xray_transition_energy", chosen, "eV", "NIST X-Ray Transition Energies", url, "Se prioriza el valor experimental cuando está disponible."),
            "energy": f"{chosen:.10g} eV",
            "particle_or_photon": "rayos X",
            "isotope": "natural",
            "transition": transition,
            "process": "emisión característica",
            "theoretical_energy_ev": f"{theoretical:.10g}",
            "experimental_energy_ev": f"{experimental:.10g}" if experimental else "",
        })
    return result


def parse_neutron_table(elements: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    try:
        rows = parse_html_rows(fetch(NEUTRON_TABLE_URL, timeout=90))
    except (urllib.error.URLError, TimeoutError):
        return {}
    symbols = {element["symbol"] for element in elements}
    result: dict[str, list[dict[str, str]]] = {symbol: [] for symbol in symbols}
    current_symbol = ""
    for cells in rows:
        if len(cells) < 8:
            continue
        first = clean(cells[0])
        if first in symbols:
            current_symbol = first
            cells = cells[1:]
        elif not current_symbol:
            continue
        isotope = clean(cells[0]) if cells else ""
        if not isotope or isotope.lower() in {"a", "isotope"}:
            continue
        padded = cells + [""] * 12
        values = {
            "neutron_coherent_scattering_length": (padded[3], "fm"),
            "neutron_coherent_cross_section": (padded[6], "barn"),
            "neutron_incoherent_cross_section": (padded[7], "barn"),
            "neutron_total_scattering_cross_section": (padded[8], "barn"),
            "neutron_absorption_cross_section": (padded[9], "barn"),
        }
        for property_id, (value, unit) in values.items():
            if numeric(value) is None:
                continue
            result[current_symbol].append({
                **base_row(property_id, value, unit, "NIST NCNR Neutron Scattering Lengths and Cross Sections", NEUTRON_TABLE_URL, "Valores evaluados a 2200 m/s; consultar la fuente para incertidumbres y limitaciones."),
                "energy": "neutrón térmico · 2200 m/s",
                "particle_or_photon": "neutrón",
                "isotope": isotope,
                "transition": "",
                "process": property_id.replace("neutron_", "").replace("_", " "),
                "abundance": padded[2],
            })
    return {symbol: rows for symbol, rows in result.items() if rows}


def import_xps_exports(elements: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    if not XPS_IMPORT_ROOT.exists():
        return result
    valid_symbols = {element["symbol"] for element in elements}
    for path in sorted(XPS_IMPORT_ROOT.glob("*.csv")):
        for row in read_csv(path):
            symbol = clean(row.get("symbol") or row.get("element"))
            if symbol not in valid_symbols:
                continue
            energy = clean(row.get("binding_energy_ev") or row.get("kinetic_energy_ev") or row.get("energy_ev") or row.get("value"))
            if numeric(energy) is None:
                continue
            line_type = clean(row.get("line_type") or row.get("transition") or row.get("orbital") or "XPS")
            process = "Auger" if "auger" in line_type.lower() else "XPS"
            result.setdefault(symbol, []).append({
                **base_row("auger_line_energy" if process == "Auger" else "xps_binding_energy", energy, "eV", row.get("source") or "Importación XPS/Auger", row.get("source_url") or "", row.get("notes") or "Exportación local normalizada."),
                "energy": f"{energy} eV",
                "particle_or_photon": "electrón",
                "isotope": "",
                "transition": line_type,
                "process": process,
                "compound": row.get("compound", ""),
                "chemical_state": row.get("chemical_state", ""),
            })
    return result


def write_radiation(element: dict[str, str], generated: list[dict[str, str]]) -> None:
    path = ELEMENTS_ROOT / element["folder"] / "radiation_interaction.csv"
    sources = {
        "NIST X-Ray Mass Attenuation Coefficients",
        "NIST X-Ray Transition Energies",
        "NIST NCNR Neutron Scattering Lengths and Cross Sections",
        "Importación XPS/Auger",
    }
    rows = [row for row in read_csv(path) if clean(row.get("source")) not in sources]
    rows.extend(generated)
    write_csv(path, rows, RADIATION_FIELDS)


def nist_spectrum_url(symbol: str) -> str:
    params = {
        "spectra": f"{symbol} I", "limits_type": "0", "low_w": "", "upp_w": "",
        "unit": "1", "submit": "Retrieve Data", "de": "0", "format": "2",
        "line_out": "0", "remove_js": "on", "en_unit": "1", "output": "0",
        "bibrefs": "1", "page_size": "5000", "show_obs_wl": "1", "show_calc_wl": "1",
        "unc_out": "1", "order_out": "0", "show_av": "3", "A_out": "0",
        "f_out": "on", "S_out": "on", "loggf_out": "on", "intens_out": "on",
        "allowed_out": "1", "forbid_out": "1", "conf_out": "on", "term_out": "on",
        "enrg_out": "on", "J_out": "on", "g_out": "on",
    }
    return f"{NIST_LINES_URL}?{urllib.parse.urlencode(params)}"


def repair_nist_spectrum(element: dict[str, str]) -> bool:
    path = ELEMENTS_ROOT / element["folder"] / "spectra_nist_lines.csv"
    if path.exists() and path.stat().st_size > 80 and len(read_csv(path)) > 0:
        return False
    url = nist_spectrum_url(element["symbol"])
    try:
        data = fetch(url, timeout=100)
    except (urllib.error.URLError, TimeoutError):
        return False
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or len(reader.fieldnames) < 2:
        return False
    normalized = {field: re.sub(r"[^a-z0-9]", "", field.lower()) for field in reader.fieldnames}
    obs_col = next((field for field, key in normalized.items() if "observedwavelength" in key or key.startswith("obswl")), "")
    ritz_col = next((field for field, key in normalized.items() if "ritzwavelength" in key or key.startswith("ritzwl")), "")
    intensity_col = next((field for field, key in normalized.items() if "intens" in key), "")
    lower_col = next((field for field, key in normalized.items() if "lowerlevel" in key), "")
    upper_col = next((field for field, key in normalized.items() if "upperlevel" in key), "")
    if not obs_col and not ritz_col:
        return False
    rows: list[dict[str, str]] = []
    for row in reader:
        obs = clean(row.get(obs_col)) if obs_col else ""
        ritz = clean(row.get(ritz_col)) if ritz_col else ""
        if numeric(obs) is None and numeric(ritz) is None:
            continue
        lower = clean(row.get(lower_col)) if lower_col else ""
        upper = clean(row.get(upper_col)) if upper_col else ""
        rows.append({
            "element": element["symbol"],
            "species": f"{element['symbol']} I",
            "obs_wl_nm": obs,
            "ritz_wl_nm": ritz,
            "intensity": clean(row.get(intensity_col)) if intensity_col else "",
            "transition": f"{lower} → {upper}".strip(" →"),
            "lower_level": lower,
            "upper_level": upper,
            "source": "NIST Atomic Spectra Database",
            "source_url": url,
            "retrieved_at": NOW,
            "notes": "Descarga automática para reparar un CSV ausente o vacío.",
        })
        if len(rows) >= 5000:
            break
    if not rows:
        return False
    write_csv(path, rows, SPECTRAL_FIELDS)
    return True


def append_source(element: dict[str, str], provider: str, dataset: str, target: str, url: str, status: str, notes: str) -> None:
    path = ELEMENTS_ROOT / element["folder"] / "sources.csv"
    fields = ["provider", "dataset", "target_file", "source_url", "retrieved_at", "status", "sha256", "notes"]
    rows = read_csv(path)
    rows = [row for row in rows if not (row.get("provider") == provider and row.get("dataset") == dataset and row.get("target_file") == target)]
    rows.append({
        "provider": provider, "dataset": dataset, "target_file": target,
        "source_url": url, "retrieved_at": NOW, "status": status,
        "sha256": "", "notes": notes,
    })
    write_csv(path, rows, fields)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", action="store_true", help="Consulta fuentes oficiales remotas.")
    parser.add_argument("--repair-spectra", action="store_true", help="Descarga espectros NIST para CSV ausentes o vacíos.")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    elements = read_manifest()
    for element in elements:
        copy_local_phase_landmarks(element)

    neutron_by_symbol: dict[str, list[dict[str, str]]] = {}
    attenuation_by_symbol: dict[str, list[dict[str, str]]] = {}
    transitions_by_symbol: dict[str, list[dict[str, str]]] = {}
    xps_by_symbol = import_xps_exports(elements)

    if args.network:
        neutron_by_symbol = parse_neutron_table(elements)
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 10))) as executor:
            attenuation_futures = {executor.submit(parse_xray_attenuation, element): element["symbol"] for element in elements if int(element["atomic_number"]) <= 92}
            transition_futures = {executor.submit(parse_xray_transitions, element): element["symbol"] for element in elements if 10 <= int(element["atomic_number"]) <= 100}
            thermo_futures = {executor.submit(enrich_pubchem_thermodynamics, element): element["symbol"] for element in elements}
            for future in as_completed([*attenuation_futures, *transition_futures, *thermo_futures]):
                if future in attenuation_futures:
                    attenuation_by_symbol[attenuation_futures[future]] = future.result()
                elif future in transition_futures:
                    transitions_by_symbol[transition_futures[future]] = future.result()
                else:
                    future.result()

    repaired = 0
    if args.network and args.repair_spectra:
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 5))) as executor:
            futures = {executor.submit(repair_nist_spectrum, element): element for element in elements}
            for future in as_completed(futures):
                if future.result():
                    repaired += 1
                    element = futures[future]
                    append_source(element, "NIST ASD", "Atomic spectral lines repair", "spectra_nist_lines.csv", nist_spectrum_url(element["symbol"]), "ok", "CSV espectral reparado automáticamente.")

    for index, element in enumerate(elements, start=1):
        symbol = element["symbol"]
        generated = [
            *attenuation_by_symbol.get(symbol, []),
            *transitions_by_symbol.get(symbol, []),
            *neutron_by_symbol.get(symbol, []),
            *xps_by_symbol.get(symbol, []),
        ]
        write_radiation(element, generated)
        if generated:
            append_source(element, "TablaElementos", "Scientific phase 2 aggregation", "radiation_interaction.csv", "", "ok", "Rayos X, atenuación, neutrones y exportaciones XPS/Auger consolidados por elemento.")
        print(f"[{index:03d}/118] {symbol} · nuclear, termodinámica y radiación preparados")

    print(f"Fase científica 2 completada. Espectros NIST reparados: {repaired}.")


if __name__ == "__main__":
    main()
