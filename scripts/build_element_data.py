#!/usr/bin/env python3
"""Genera un JSON perezoso por elemento y amplía el índice principal.

Se ejecuta después de ``scripts/build_data.py``. No duplica todos los CSV dentro
del índice inicial: cada ficha descarga únicamente ``data/elements/<símbolo>.json``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_DIR = ROOT / "data" / "elements"
MANIFEST = ELEMENTS_DIR / "elements.manifest.csv"
PROCESSED = ROOT / "data" / "processed"
PUBLIC = ROOT / "public" / "data"

DOMAINS: tuple[tuple[str, str, str], ...] = (
    ("identity", "identity.csv", "Identidad"),
    ("atomic", "atomic_properties.csv", "Propiedades atómicas"),
    ("physical", "physical_properties.csv", "Propiedades físicas"),
    ("chemical", "chemical_properties.csv", "Propiedades químicas"),
    ("isotopes", "isotopes.csv", "Isótopos"),
    ("nist_levels", "spectra_nist_levels.csv", "Niveles NIST"),
    ("materials", "materials.csv", "Materiales"),
    ("thermodynamics", "thermodynamics.csv", "Termodinámica"),
    ("compounds", "compounds.csv", "Compuestos"),
    ("photonics", "photonics_color.csv", "Fotónica y color"),
    ("radiation", "radiation_interaction.csv", "Interacción con radiación"),
    ("analytical", "analytical_methods.csv", "Métodos analíticos"),
    ("computational", "computational.csv", "Datos computacionales"),
    ("geochemistry", "geochemistry.csv", "Geoquímica"),
    ("astrophysics", "astrophysics.csv", "Astrofísica"),
    ("biology", "biology_medicine.csv", "Biología y medicina"),
    ("environment", "environment_safety.csv", "Medioambiente y seguridad"),
    ("industry", "industry_economy.csv", "Industria y economía"),
    ("history", "history.csv", "Historia"),
    ("sources", "sources.csv", "Fuentes"),
)


def clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").strip()
    if len(text) >= 3 and text.startswith('="') and text.endswith('"'):
        text = text[2:-1]
    return text.replace('""', '"').strip()


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def read_domain(folder: Path, domain_id: str, filename: str, label: str) -> dict[str, Any]:
    path = folder / filename
    result: dict[str, Any] = {
        "id": domain_id,
        "label": label,
        "file": filename,
        "present": path.exists(),
        "available": False,
        "columns": [],
        "row_count": 0,
        "rows": [],
    }
    if not path.exists():
        return result

    try:
        with path.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            result["columns"] = [clean(column) for column in (reader.fieldnames or []) if column]
            rows = []
            for raw in reader:
                row = {clean(key): clean(value) for key, value in raw.items() if key}
                if any(row.values()):
                    rows.append(row)
            result["rows"] = rows
            result["row_count"] = len(rows)
            result["available"] = bool(rows)
    except (OSError, csv.Error) as error:
        result["error"] = str(error)
    return result


def write_json(path: Path, payload: Any, *, compact: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def enrich_index(index_path: Path, manifest: list[dict[str, str]], data_index: dict[str, Any]) -> None:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    manifest_by_symbol = {row["symbol"]: row for row in manifest}
    for element in payload.get("elements", []):
        row = manifest_by_symbol.get(element.get("symbol"), {})
        element["block"] = row.get("block", "")
        element["folder"] = row.get("folder", "")
        if row.get("group"):
            element["group"] = int(row["group"])
        if row.get("period"):
            element["period"] = int(row["period"])
    payload["data_index_by_element"] = data_index
    payload.setdefault("metadata", {})["element_data_strategy"] = "one-json-per-element"
    payload["metadata"]["dataset"] = "elements-v5-lazy-domains"
    write_json(index_path, payload)


def main() -> None:
    manifest = read_manifest()
    data_index: dict[str, Any] = {}
    processed_elements = PROCESSED / "elements"
    public_elements = PUBLIC / "elements"

    for row in manifest:
        symbol = row["symbol"]
        folder = ELEMENTS_DIR / row["folder"]
        domains = {
            domain_id: read_domain(folder, domain_id, filename, label)
            for domain_id, filename, label in DOMAINS
        }
        payload = {
            "symbol": symbol,
            "atomic_number": int(row["atomic_number"]),
            "folder": row["folder"],
            "domains": domains,
        }
        write_json(processed_elements / f"{symbol}.json", payload)
        write_json(public_elements / f"{symbol}.json", payload)

        available = [domain_id for domain_id, domain in domains.items() if domain["available"]]
        data_index[symbol] = {
            "data_url": f"./data/elements/{symbol}.json",
            "available_domains": available,
            "domain_counts": {domain_id: domain["row_count"] for domain_id, domain in domains.items()},
            "available_file_count": len(available),
        }

    enrich_index(PROCESSED / "spectra.sample.json", manifest, data_index)
    enrich_index(PUBLIC / "spectra.sample.json", manifest, data_index)

    populated = sum(1 for item in data_index.values() if item["available_file_count"])
    print(f"Datos detallados generados para 118 elementos; {populated} contienen al menos un bloque con registros.")
    print(f"- {public_elements.relative_to(ROOT)}/<símbolo>.json")


if __name__ == "__main__":
    main()
