#!/usr/bin/env python3
"""Registra la cobertura NIST Chemistry WebBook en sources.csv por elemento."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_ROOT = ROOT / "data" / "elements"
MANIFEST_PATH = ELEMENTS_ROOT / "elements.manifest.csv"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
SOURCE_NAME = "NIST Chemistry WebBook"


def clean(value: Any) -> str:
    return "" if value is None else str(value).replace("\ufeff", "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        return [{clean(k): clean(v) for k, v in row.items() if k} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    extras = sorted({key for row in rows for key in row if key not in fields})
    columns = fields + extras
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean(row.get(column)) for column in columns})


def main() -> None:
    manifest = read_csv(MANIFEST_PATH)
    fields = ["provider", "dataset", "target_file", "source_url", "retrieved_at", "status", "sha256", "notes"]
    registered = 0

    for element in manifest:
        folder = ELEMENTS_ROOT / element["folder"]
        thermo_rows = [row for row in read_csv(folder / "thermodynamics.csv") if row.get("source") == SOURCE_NAME]
        if not thermo_rows:
            continue
        source_url = next((row.get("source_url", "") for row in thermo_rows if row.get("source_url")), "")
        source_path = folder / "sources.csv"
        rows = read_csv(source_path)
        rows = [
            row for row in rows
            if not (
                row.get("provider") == "NIST"
                and row.get("dataset") == "Chemistry WebBook"
                and row.get("target_file") == "thermodynamics.csv"
            )
        ]
        rows.append({
            "provider": "NIST",
            "dataset": "Chemistry WebBook",
            "target_file": "thermodynamics.csv",
            "source_url": source_url,
            "retrieved_at": NOW,
            "status": "ok",
            "sha256": "",
            "notes": f"{len(thermo_rows)} registros evaluados, incluidas magnitudes tabuladas o coeficientes Shomate cuando están disponibles.",
        })
        write_csv(source_path, rows, fields)
        registered += 1

    print(f"NIST Chemistry WebBook registrado en sources.csv para {registered} elementos.")


if __name__ == "__main__":
    main()
