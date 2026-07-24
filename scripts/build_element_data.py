#!/usr/bin/env python3
"""Genera un JSON perezoso por elemento y amplía el índice principal.

Se ejecuta después de ``scripts/build_data.py``. Cada ficha descarga únicamente
``data/elements/<símbolo>.json``. El índice inicial conserva un resumen ligero
y un bloque de valores normalizados para filtros combinables sin cargar los CSV
completos de los 118 elementos.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

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

SUMMARY_FIELDS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("atomic_mass", "atomic", ("atomic_mass",)),
    ("standard_atomic_weight", "atomic", ("standard_atomic_weight",)),
    ("electron_configuration", "atomic", ("electron_configuration",)),
    ("electronegativity", "atomic", ("electronegativity",)),
    ("atomic_radius", "atomic", ("atomic_radius", "atomic_radius_empirical")),
    ("ionization_energy", "atomic", ("ionization_energy", "first_ionization_energy")),
    ("electron_affinity", "atomic", ("electron_affinity",)),
    ("standard_state", "physical", ("standard_state", "phase", "state")),
    ("density", "physical", ("density",)),
    ("melting_point", "physical", ("melting_point",)),
    ("boiling_point", "physical", ("boiling_point",)),
)

NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][-+]?\d+)?")


def clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").strip()
    if len(text) >= 3 and text.startswith('="') and text.endswith('"'):
        text = text[2:-1]
    return text.replace('""', '"').strip()


def normalized_key(value: Any) -> str:
    return clean(value).strip().lower().replace(" ", "_").replace("-", "_")


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


def property_row(
    domains: dict[str, dict[str, Any]],
    domain_id: str,
    property_names: Iterable[str],
) -> dict[str, str] | None:
    accepted = {normalized_key(name) for name in property_names}
    domain = domains.get(domain_id, {})
    for row in domain.get("rows", []):
        if normalized_key(row.get("property")) in accepted:
            return row
    return None


def property_value(
    domains: dict[str, dict[str, Any]],
    domain_id: str,
    property_names: Iterable[str],
) -> str:
    row = property_row(domains, domain_id, property_names)
    if not row:
        return ""
    value = clean(row.get("value"))
    unit = clean(row.get("unit"))
    if not value:
        return ""
    return f"{value} {unit}".strip()


def summary_values(domains: dict[str, dict[str, Any]]) -> dict[str, str]:
    values = {
        output_name: property_value(domains, domain_id, property_names)
        for output_name, domain_id, property_names in SUMMARY_FIELDS
    }

    if not values.get("standard_state"):
        identity_rows = domains.get("identity", {}).get("rows", [])
        if identity_rows:
            values["standard_state"] = clean(identity_rows[0].get("standard_state"))

    return values


def numeric_parts(value: Any) -> list[float]:
    text = clean(value).replace("−", "-")
    values: list[float] = []
    for match in NUMBER_RE.findall(text):
        try:
            values.append(float(match.replace(",", ".")))
        except ValueError:
            continue
    return values


def representative_number(value: Any) -> float | None:
    parts = numeric_parts(value)
    if not parts:
        return None
    text = clean(value)
    if len(parts) >= 2 and ("[" in text or "]" in text or "–" in text or " to " in text.lower()):
        return mean(parts[:2])
    return parts[0]


def row_number(row: dict[str, str] | None) -> float | None:
    if not row:
        return None
    return representative_number(row.get("value"))


def unit_key(row: dict[str, str] | None) -> str:
    if not row:
        return ""
    return clean(row.get("unit")).lower().replace(" ", "").replace("³", "3").replace("−", "-")


def temperature_kelvin(row: dict[str, str] | None) -> float | None:
    value = row_number(row)
    if value is None:
        return None
    unit = unit_key(row)
    if "°c" in unit or unit in {"c", "celsius"}:
        return value + 273.15
    if "°f" in unit or unit in {"f", "fahrenheit"}:
        return (value - 32.0) * 5.0 / 9.0 + 273.15
    return value


def density_g_cm3(row: dict[str, str] | None) -> float | None:
    value = row_number(row)
    if value is None:
        return None
    unit = unit_key(row)
    if any(token in unit for token in ("g/cm3", "g·cm-3", "gml-1", "g/ml")):
        return value
    if any(token in unit for token in ("kg/m3", "kg·m-3")):
        return value / 1000.0
    if any(token in unit for token in ("g/l", "g·l-1")):
        return value / 1000.0
    if any(token in unit for token in ("kg/l", "kg·l-1")):
        return value
    if any(token in unit for token in ("mg/cm3", "mg·cm-3")):
        return value / 1000.0
    if any(token in unit for token in ("mg/l", "mg·l-1")):
        return value / 1_000_000.0
    return value


def energy_kj_mol(row: dict[str, str] | None) -> float | None:
    value = row_number(row)
    if value is None:
        return None
    unit = unit_key(row)
    if "ev" in unit:
        return value * 96.48533212
    if "kcal/mol" in unit or "kcalmol-1" in unit:
        return value * 4.184
    if ("j/mol" in unit or "jmol-1" in unit) and "kj" not in unit:
        return value / 1000.0
    return value


def radius_pm(row: dict[str, str] | None) -> float | None:
    value = row_number(row)
    if value is None:
        return None
    unit = unit_key(row)
    if "angstrom" in unit or "å" in unit or unit == "a":
        return value * 100.0
    if "nm" in unit:
        return value * 1000.0
    if unit == "m":
        return value * 1_000_000_000_000.0
    return value


def specific_heat_j_gk(row: dict[str, str] | None) -> float | None:
    value = row_number(row)
    if value is None:
        return None
    unit = unit_key(row)
    if "j/(kg" in unit or "jkg-1" in unit:
        return value / 1000.0
    return value


def metal_type(category: str) -> str:
    normalized = normalized_key(category)
    if normalized == "metaloide":
        return "Metaloide"
    if normalized in {"no_metal", "halogeno", "gas_noble"}:
        return "No metal"
    if normalized in {"", "desconocido"}:
        return "Sin clasificar"
    return "Metal"


def filter_values(
    row: dict[str, str],
    domains: dict[str, dict[str, Any]],
    available_file_count: int,
) -> dict[str, Any]:
    atomic_mass_row = property_row(domains, "atomic", ("standard_atomic_weight", "atomic_mass"))
    electronegativity_row = property_row(domains, "atomic", ("electronegativity",))
    ionization_row = property_row(domains, "atomic", ("ionization_energy", "first_ionization_energy"))
    affinity_row = property_row(domains, "atomic", ("electron_affinity",))
    radius_row = property_row(domains, "atomic", ("atomic_radius", "atomic_radius_empirical"))
    state_row = property_row(domains, "physical", ("standard_state", "phase", "state"))
    density_row = property_row(domains, "physical", ("density",))
    melting_row = property_row(domains, "physical", ("melting_point",))
    boiling_row = property_row(domains, "physical", ("boiling_point",))
    heat_row = property_row(domains, "physical", ("specific_heat", "specific_heat_capacity"))
    oxidation_row = property_row(domains, "chemical", ("oxidation_states", "oxidation_state"))
    discovery_row = property_row(domains, "history", ("discovery_year", "year_discovered", "discovered", "year"))
    thermal_conductivity_row = property_row(domains, "materials", ("thermal_conductivity",))
    electrical_conductivity_row = property_row(domains, "materials", ("electrical_conductivity",))
    electrical_resistivity_row = property_row(domains, "materials", ("electrical_resistivity",))
    young_modulus_row = property_row(domains, "materials", ("young_modulus",))
    shear_modulus_row = property_row(domains, "materials", ("shear_modulus",))
    bulk_modulus_row = property_row(domains, "materials", ("bulk_modulus",))
    crust_abundance_row = property_row(domains, "geochemistry", ("abundance_crust",))
    ocean_abundance_row = property_row(domains, "geochemistry", ("abundance_ocean",))
    universe_abundance_row = property_row(domains, "astrophysics", ("abundance_universe",))
    human_abundance_row = property_row(domains, "biology", ("abundance_human",))
    supply_risk_row = property_row(domains, "industry", ("relative_supply_risk",))
    price_row = property_row(domains, "industry", ("price_per_kg",))

    standard_state = clean(state_row.get("value")) if state_row else ""
    if not standard_state:
        identity_rows = domains.get("identity", {}).get("rows", [])
        if identity_rows:
            standard_state = clean(identity_rows[0].get("standard_state"))

    return {
        "atomic_number": int(row["atomic_number"]),
        "group": int(row["group"]) if row.get("group") else 0,
        "period": int(row["period"]) if row.get("period") else 0,
        "block": row.get("block", ""),
        "standard_state": standard_state,
        "atomic_mass": row_number(atomic_mass_row),
        "electronegativity": row_number(electronegativity_row),
        "ionization_energy": energy_kj_mol(ionization_row),
        "electron_affinity": energy_kj_mol(affinity_row),
        "atomic_radius": radius_pm(radius_row),
        "melting_point": temperature_kelvin(melting_row),
        "boiling_point": temperature_kelvin(boiling_row),
        "density": density_g_cm3(density_row),
        "specific_heat": specific_heat_j_gk(heat_row),
        "discovery_year": row_number(discovery_row),
        "oxidation_states": clean(oxidation_row.get("value")) if oxidation_row else "",
        "isotope_count": domains.get("isotopes", {}).get("row_count", 0),
        "level_count": domains.get("nist_levels", {}).get("row_count", 0),
        "available_file_count": available_file_count,
        "thermal_conductivity": row_number(thermal_conductivity_row),
        "electrical_conductivity": row_number(electrical_conductivity_row),
        "electrical_resistivity": row_number(electrical_resistivity_row),
        "young_modulus": row_number(young_modulus_row),
        "shear_modulus": row_number(shear_modulus_row),
        "bulk_modulus": row_number(bulk_modulus_row),
        "abundance_crust": row_number(crust_abundance_row),
        "abundance_ocean": row_number(ocean_abundance_row),
        "abundance_universe": row_number(universe_abundance_row),
        "abundance_human": row_number(human_abundance_row),
        "relative_supply_risk": row_number(supply_risk_row),
        "price_per_kg": row_number(price_row),
    }


def write_json(path: Path, payload: Any, *, compact: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
    path.write_text(text + "\n", encoding="utf-8")


def enrich_index(index_path: Path, manifest: list[dict[str, str]], data_index: dict[str, Any]) -> None:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    manifest_by_symbol = {row["symbol"]: row for row in manifest}
    for element in payload.get("elements", []):
        symbol = element.get("symbol", "")
        row = manifest_by_symbol.get(symbol, {})
        element["block"] = row.get("block", "")
        element["folder"] = row.get("folder", "")
        if row.get("group"):
            element["group"] = int(row["group"])
        if row.get("period"):
            element["period"] = int(row["period"])

        index_entry = data_index.get(symbol, {})
        values = index_entry.setdefault("filter_values", {})
        category = clean(element.get("category")) or clean(row.get("category")) or "Desconocido"
        values["category"] = category
        values["metal_type"] = metal_type(category)
        values["block"] = element.get("block", "")
        values["group"] = element.get("group", 0)
        values["period"] = element.get("period", 0)
        values["spectral_line_count"] = len(element.get("lines", []))

    payload["data_index_by_element"] = data_index
    payload.setdefault("metadata", {})["element_data_strategy"] = "one-json-per-element-with-filter-index"
    payload["metadata"]["dataset"] = "elements-v7-scientific-filters"
    payload["metadata"]["filter_units"] = {
        "atomic_mass": "u",
        "electronegativity": "Pauling",
        "ionization_energy": "kJ/mol",
        "electron_affinity": "kJ/mol",
        "atomic_radius": "pm",
        "melting_point": "K",
        "boiling_point": "K",
        "density": "g/cm³",
        "specific_heat": "J/(g·K)",
    }
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
            "summary_values": summary_values(domains),
            "filter_values": filter_values(row, domains, len(available)),
        }

    enrich_index(PROCESSED / "spectra.sample.json", manifest, data_index)
    enrich_index(PUBLIC / "spectra.sample.json", manifest, data_index)

    populated = sum(1 for item in data_index.values() if item["available_file_count"])
    print(f"Datos detallados generados para 118 elementos; {populated} contienen al menos un bloque con registros.")
    print("El índice inicial incluye propiedades resumidas y valores normalizados para filtros.")
    print(f"- {public_elements.relative_to(ROOT)}/<símbolo>.json")


if __name__ == "__main__":
    main()
