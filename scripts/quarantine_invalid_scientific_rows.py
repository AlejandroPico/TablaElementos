#!/usr/bin/env python3
"""Retira del dataset las filas científicas conocidas como inválidas.

La primera versión del parser NCNR leyó una tabla con celdas combinadas y pudo
asignar masa, espín o abundancia a columnas de dispersión. Esas filas se
identifican de forma inequívoca por la URL antigua ``activation/scattering_table``.

La tabla corregida utiliza ``n-lengths/list.html`` y no se ve afectada.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_ROOT = ROOT / "data" / "elements"
INVALID_URL_FRAGMENT = "/activation/scattering_table.html"
INVALID_SOURCE = "NIST NCNR Neutron Scattering Lengths and Cross Sections"


def clean(value: Any) -> str:
    return "" if value is None else str(value).replace("\ufeff", "").strip()


def clean_file(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = [clean(field) for field in (reader.fieldnames or []) if field]
        rows = [{clean(k): clean(v) for k, v in row.items() if k} for row in reader]
    if not fieldnames:
        return 0

    retained = [
        row for row in rows
        if not (
            row.get("source") == INVALID_SOURCE
            and INVALID_URL_FRAGMENT in row.get("source_url", "")
        )
    ]
    removed = len(rows) - len(retained)
    if not removed:
        return 0

    extras = sorted({key for row in retained for key in row if key not in fieldnames})
    columns = fieldnames + extras
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in retained:
            writer.writerow({column: clean(row.get(column)) for column in columns})
    return removed


def main() -> None:
    removed = 0
    affected = 0
    for path in sorted(ELEMENTS_ROOT.glob("*/radiation_interaction.csv")):
        count = clean_file(path)
        if count:
            removed += count
            affected += 1
    print(f"Cuarentena científica: {removed} filas retiradas en {affected} elementos.")


if __name__ == "__main__":
    main()
