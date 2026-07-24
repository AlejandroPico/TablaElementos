#!/usr/bin/env python3
"""Integra materiales, abundancias, biología e industria por elemento.

Los datos consumidos por la aplicación se escriben exclusivamente en
``data/elements/<elemento>/``. El importador usa dos compilaciones versionadas:

- Periodic Table Data Complete 1.0.1 (MIT), para propiedades de materiales,
  abundancias y clasificaciones de seguridad.
- Mendeleev, commit fijado, para geoquímica y riesgo de suministro publicado
  originalmente por la Royal Society of Chemistry.

Ambas son fuentes secundarias. Cada fila lo declara explícitamente y conserva
la URL de procedencia; no se presentan valores ausentes como cero.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sqlite3
import tarfile
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_ROOT = ROOT / "data" / "elements"
MANIFEST_PATH = ELEMENTS_ROOT / "elements.manifest.csv"

PTABLE_VERSION = "1.0.1"
PTABLE_URL = (
    "https://registry.npmjs.org/periodic-table-data-complete/-/"
    f"periodic-table-data-complete-{PTABLE_VERSION}.tgz"
)
MENDELEEV_COMMIT = "580e34010f5c90cf0a025d365948fd343670e9d2"
MENDELEEV_URL = (
    "https://raw.githubusercontent.com/lmmentel/mendeleev/"
    f"{MENDELEEV_COMMIT}/mendeleev/elements.db"
)
RSC_URL = "https://periodic-table.rsc.org/element/{atomic_number}/{slug}"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

SECONDARY_SOURCE = f"Periodic Table Data Complete {PTABLE_VERSION} · compilación secundaria"
MENDELEEV_SOURCE = f"Mendeleev · commit {MENDELEEV_COMMIT[:10]} · compilación secundaria"

PROPERTY_FIELDS = ["property", "value", "unit", "source", "source_url", "retrieved_at", "notes"]
MATERIAL_FIELDS = PROPERTY_FIELDS + [
    "material_id", "phase", "structure", "space_group",
    "lattice_a", "lattice_b", "lattice_c",
    "lattice_alpha", "lattice_beta", "lattice_gamma",
]
GEO_FIELDS = PROPERTY_FIELDS + ["environment"]
ASTRO_FIELDS = PROPERTY_FIELDS + ["context"]
BIO_FIELDS = PROPERTY_FIELDS + ["organism_or_use"]
ENV_FIELDS = PROPERTY_FIELDS + ["classification"]
INDUSTRY_FIELDS = PROPERTY_FIELDS + ["year", "region"]
RADIATION_FIELDS = [
    "property", "value", "unit", "energy", "particle_or_photon", "isotope",
    "transition", "process", "source", "source_url", "retrieved_at", "notes",
    "abundance", "experimental_energy_ev", "theoretical_energy_ev",
]
SOURCE_FIELDS = ["provider", "dataset", "target_file", "source_url", "retrieved_at", "status", "sha256", "notes"]

UNITS = {
    "thermal_conductivity": "W/(m·K)",
    "electrical_conductivity": "MS/m",
    "electrical_resistivity": "Ω·m",
    "magnetic_susceptibility_mass": "m³/kg",
    "magnetic_susceptibility_molar": "m³/mol",
    "magnetic_susceptibility_volume": "adimensional",
    "curie_point": "K",
    "neel_point": "K",
    "superconducting_point": "K",
    "bulk_modulus": "GPa",
    "shear_modulus": "GPa",
    "young_modulus": "GPa",
    "poisson_ratio": "adimensional",
    "mohs_hardness": "Mohs",
    "vickers_hardness": "MPa",
    "brinell_hardness": "MPa",
    "speed_of_sound": "m/s",
    "thermal_expansion": "K⁻¹",
}


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "sí" if value else "no"
    return str(value).replace("\ufeff", "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        return [{clean(k): clean(v) for k, v in row.items() if k} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    extras = sorted({key for row in rows for key in row if key not in fields})
    columns = fields + extras
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean(row.get(column)) for column in columns})


def replace_source_rows(
    path: Path,
    incoming: Iterable[dict[str, Any]],
    fields: list[str],
    sources: set[str],
) -> None:
    rows = [row for row in read_csv(path) if clean(row.get("source")) not in sources]
    rows.extend({key: clean(value) for key, value in row.items()} for row in incoming if clean(row.get("value")))
    write_csv(path, rows, fields)


def base_row(
    property_id: str,
    value: Any,
    unit: str,
    source: str,
    source_url: str,
    notes: str,
) -> dict[str, str]:
    return {
        "property": property_id,
        "value": clean(value),
        "unit": unit,
        "source": source,
        "source_url": source_url,
        "retrieved_at": NOW,
        "notes": notes,
    }


def download(url: str, timeout: int = 120) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TablaElementos/0.5 scientific importer"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def load_periodic_table(path: Path | None) -> list[dict[str, Any]]:
    if path:
        return json.loads(path.read_text(encoding="utf-8"))
    archive = tarfile.open(fileobj=io.BytesIO(download(PTABLE_URL)), mode="r:gz")
    member = next(item for item in archive.getmembers() if item.name.endswith("/pTable.json"))
    stream = archive.extractfile(member)
    if stream is None:
        raise RuntimeError("El paquete fijado no contiene pTable.json.")
    return json.loads(stream.read().decode("utf-8"))


def load_mendeleev(path: Path | None) -> sqlite3.Connection:
    if path:
        return sqlite3.connect(path)
    temp = tempfile.NamedTemporaryFile(prefix="tablaelementos-mendeleev-", suffix=".db", delete=False)
    temp.write(download(MENDELEEV_URL))
    temp.close()
    return sqlite3.connect(temp.name)


def manifest() -> list[dict[str, str]]:
    with MANIFEST_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def nested(record: dict[str, Any], group: str, key: str) -> Any:
    value = record.get(group)
    return value.get(key) if isinstance(value, dict) else None


def lattice_parts(value: Any) -> list[str]:
    if isinstance(value, list):
        return [clean(item) for item in value]
    return [part.strip() for part in clean(value).split(",") if part.strip()]


def material_rows(record: dict[str, Any]) -> list[dict[str, str]]:
    url = clean(record.get("source")) or "https://github.com/sweaver2112/periodic-table-data-complete"
    structure = clean(record.get("crystal_structure"))
    space_group = clean(record.get("space_group_name"))
    constants = lattice_parts(record.get("lattice_constants"))
    angles = lattice_parts(record.get("lattice_angles"))
    common = {
        "material_id": f"{clean(record.get('symbol'))}-reference",
        "phase": "elemento puro · condiciones de referencia",
        "structure": structure,
        "space_group": space_group,
        "lattice_a": constants[0] if len(constants) > 0 else "",
        "lattice_b": constants[1] if len(constants) > 1 else "",
        "lattice_c": constants[2] if len(constants) > 2 else "",
        "lattice_alpha": angles[0] if len(angles) > 0 else "",
        "lattice_beta": angles[1] if len(angles) > 1 else "",
        "lattice_gamma": angles[2] if len(angles) > 2 else "",
    }
    rows: list[dict[str, str]] = []

    def add(prop: str, value: Any, unit: str = "", notes: str = "") -> None:
        if value in (None, "", []):
            return
        rows.append({
            **base_row(
                prop, value, unit, SECONDARY_SOURCE, url,
                notes or "Valor de referencia secundario; puede depender de fase, pureza, orientación y temperatura.",
            ),
            **common,
        })

    add("crystal_structure", structure, "", "Estructura cristalina de referencia de la compilación.")
    add("space_group", space_group, "", f"Número de grupo espacial: {clean(record.get('space_group_number')) or 'no indicado'}.")
    if constants:
        add("lattice_constants", ", ".join(constants), "pm")
    if angles:
        add("lattice_angles", ", ".join(angles), "rad")
    add("thermal_conductivity", nested(record, "conductivity", "thermal"), UNITS["thermal_conductivity"])
    add("electrical_conductivity", nested(record, "conductivity", "electric"), UNITS["electrical_conductivity"])
    add("electrical_resistivity", record.get("resistivity"), UNITS["electrical_resistivity"])
    add("electrical_type", record.get("electrical_type"))
    add("magnetic_type", record.get("magnetic_type"))
    for key in ("mass", "molar", "volume"):
        add(
            f"magnetic_susceptibility_{key}",
            nested(record, "magnetic_susceptibility", key),
            UNITS[f"magnetic_susceptibility_{key}"],
        )
    for source_key, target_key in (
        ("curie_point", "curie_point"),
        ("neel_point", "neel_point"),
        ("superconducting_point", "superconducting_point"),
    ):
        add(target_key, record.get(source_key), UNITS[target_key])
    for source_key, target_key in (("bulk", "bulk_modulus"), ("shear", "shear_modulus"), ("young", "young_modulus")):
        add(target_key, nested(record, "modulus", source_key), UNITS[target_key])
    add("poisson_ratio", record.get("poisson_ratio"), UNITS["poisson_ratio"])
    for source_key, target_key in (("mohs", "mohs_hardness"), ("vickers", "vickers_hardness"), ("brinell", "brinell_hardness")):
        add(target_key, nested(record, "hardness", source_key), UNITS[target_key])
    add("speed_of_sound", record.get("speed_of_sound"), UNITS["speed_of_sound"])
    add("thermal_expansion", record.get("thermal_expansion"), UNITS["thermal_expansion"])
    return rows


def abundance_rows(record: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, str]]:
    url = clean(record.get("source")) or "https://github.com/sweaver2112/periodic-table-data-complete"
    return [
        base_row(
            f"abundance_{key}",
            nested(record, "abundance", key),
            "%",
            SECONDARY_SOURCE,
            url,
            "Fracción másica aproximada de la compilación; comparar en escala logarítmica.",
        )
        for key in keys
        if nested(record, "abundance", key) not in (None, "")
    ]


def append_source(folder: Path) -> None:
    path = folder / "sources.csv"
    rows = [
        row for row in read_csv(path)
        if row.get("provider") not in {"Periodic Table Data Complete", "Mendeleev"}
    ]
    rows.extend([
        {
            "provider": "Periodic Table Data Complete",
            "dataset": f"pTable.json {PTABLE_VERSION}",
            "target_file": "materials.csv; geochemistry.csv; astrophysics.csv; biology_medicine.csv; environment_safety.csv; radiation_interaction.csv",
            "source_url": PTABLE_URL,
            "retrieved_at": NOW,
            "status": "compilación secundaria versionada",
            "sha256": "",
            "notes": "Propiedades de materiales, abundancias y clasificaciones; cada fila conserva la URL original cuando existe.",
        },
        {
            "provider": "Mendeleev",
            "dataset": f"elements.db {MENDELEEV_COMMIT[:10]}",
            "target_file": "geochemistry.csv; industry_economy.csv",
            "source_url": MENDELEEV_URL,
            "retrieved_at": NOW,
            "status": "compilación secundaria versionada",
            "sha256": "",
            "notes": "Clasificación geoquímica y riesgo de suministro; los metadatos de Mendeleev remiten a CRC, RSC y bibliografía específica.",
        },
    ])
    write_csv(path, rows, SOURCE_FIELDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ptable-json", type=Path, help="Usar un pTable.json local en lugar del paquete fijado.")
    parser.add_argument("--mendeleev-db", type=Path, help="Usar un elements.db local en lugar del commit fijado.")
    args = parser.parse_args()

    elements = manifest()
    ptable = {clean(item.get("symbol")): item for item in load_periodic_table(args.ptable_json)}
    connection = load_mendeleev(args.mendeleev_db)
    connection.row_factory = sqlite3.Row

    for index, element in enumerate(elements, start=1):
        symbol = element["symbol"]
        folder = ELEMENTS_ROOT / element["folder"]
        record = ptable.get(symbol, {})
        source_url = clean(record.get("source")) or "https://github.com/sweaver2112/periodic-table-data-complete"

        replace_source_rows(folder / "materials.csv", material_rows(record), MATERIAL_FIELDS, {SECONDARY_SOURCE})

        geo = [
            {**row, "environment": "corteza" if row["property"] == "abundance_crust" else "océano"}
            for row in abundance_rows(record, ("crust", "ocean"))
        ]
        astro = [
            {**row, "context": row["property"].replace("abundance_", "")}
            for row in abundance_rows(record, ("universe", "solar", "meteor"))
        ]
        bio = [
            {**row, "organism_or_use": "cuerpo humano"}
            for row in abundance_rows(record, ("human",))
        ]
        classifications = record.get("classifications") if isinstance(record.get("classifications"), dict) else {}
        environment = []
        for prop, key, classification in (
            ("dot_hazard_class", "dot_hazard_class", "transporte DOT"),
            ("dot_number", "dot_numbers", "transporte DOT"),
            ("rtecs_identifier", "rtecs_number", "registro de efectos tóxicos"),
        ):
            value = classifications.get(key)
            if value not in (None, ""):
                environment.append({
                    **base_row(
                        prop, value, "", SECONDARY_SOURCE, source_url,
                        "Identificador o clasificación; no equivale por sí solo a una evaluación toxicológica.",
                    ),
                    "classification": classification,
                })

        replace_source_rows(folder / "geochemistry.csv", geo, GEO_FIELDS, {SECONDARY_SOURCE, MENDELEEV_SOURCE})
        replace_source_rows(folder / "astrophysics.csv", astro, ASTRO_FIELDS, {SECONDARY_SOURCE})
        replace_source_rows(folder / "biology_medicine.csv", bio, BIO_FIELDS, {SECONDARY_SOURCE})
        replace_source_rows(folder / "environment_safety.csv", environment, ENV_FIELDS, {SECONDARY_SOURCE})
        radiation = []
        for prop, source_key, unit in (
            ("neutron_cross_section_reference", "neutron_cross_section", "barn"),
            ("neutron_mass_absorption_reference", "neutron_mass_absorption", "m²/kg"),
        ):
            value = record.get(source_key)
            if value in (None, ""):
                continue
            radiation.append({
                **base_row(
                    prop, value, unit, SECONDARY_SOURCE, source_url,
                    "Valor neutrónico de referencia secundario; se conserva sin reinterpretarlo como una sección isotópica específica.",
                ),
                "energy": "neutrón térmico · referencia",
                "particle_or_photon": "neutrón",
                "isotope": f"{symbol}-natural",
                "transition": "",
                "process": prop.replace("neutron_", "").replace("_", " "),
                "abundance": "",
                "experimental_energy_ev": "",
                "theoretical_energy_ev": "",
            })
        replace_source_rows(folder / "radiation_interaction.csv", radiation, RADIATION_FIELDS, {SECONDARY_SOURCE})

        db_row = connection.execute("SELECT * FROM elements WHERE atomic_number = ?", (int(element["atomic_number"]),)).fetchone()
        if db_row:
            rsc_url = RSC_URL.format(atomic_number=element["atomic_number"], slug=element["folder"].split("-", 2)[-1])
            geo_extra = []
            for prop in ("geochemical_class", "goldschmidt_class"):
                if db_row[prop] not in (None, ""):
                    geo_extra.append({
                        **base_row(
                            prop, db_row[prop], "", MENDELEEV_SOURCE, rsc_url,
                            "Clasificación secundaria con bibliografía indicada en los metadatos de Mendeleev.",
                        ),
                        "environment": "clasificación",
                    })
            existing_geo = [row for row in read_csv(folder / "geochemistry.csv") if row.get("source") != MENDELEEV_SOURCE]
            write_csv(folder / "geochemistry.csv", existing_geo + geo_extra, GEO_FIELDS)

            industry = []
            for prop, unit in (
                ("relative_supply_risk", "índice 1–10"),
                ("production_concentration", "%"),
                ("reserve_distribution", "%"),
                ("recycling_rate", "%"),
                ("substitutability", ""),
                ("top_3_producers", ""),
                ("top_3_reserve_holders", ""),
                ("price_per_kg", "USD/kg"),
                ("uses", ""),
            ):
                value = db_row[prop]
                if value in (None, ""):
                    continue
                industry.append({
                    **base_row(
                        prop, value, unit, MENDELEEV_SOURCE, rsc_url,
                        "Dato secundario; el precio y los indicadores económicos requieren fecha y mercado para uso profesional.",
                    ),
                    "year": "",
                    "region": "global",
                })
            replace_source_rows(folder / "industry_economy.csv", industry, INDUSTRY_FIELDS, {MENDELEEV_SOURCE})

        append_source(folder)
        print(f"[{index:03d}/118] {symbol} · materiales y contexto integrados")

    connection.close()
    print("Integración completada dentro de data/elements/<elemento>/.")


if __name__ == "__main__":
    main()
