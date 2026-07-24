#!/usr/bin/env python3
"""Audita cobertura y estructura espectral sin confundir ausencia con cero."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_ROOT = ROOT / "data" / "elements"


def row_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> None:
    folders = sorted(folder for folder in ELEMENTS_ROOT.iterdir() if (folder / "identity.csv").exists())
    missing: list[str] = []
    with_lines = 0
    with_levels = 0
    levels_without_lines: list[str] = []

    for folder in folders:
        lines = row_count(folder / "spectra_nist_lines.csv")
        levels = row_count(folder / "spectra_nist_levels.csv")
        if lines < 0:
            missing.append(f"{folder.name}/spectra_nist_lines.csv")
        if levels < 0:
            missing.append(f"{folder.name}/spectra_nist_levels.csv")
        with_lines += lines > 0
        with_levels += levels > 0
        if lines == 0 and levels > 0:
            levels_without_lines.append(folder.name)

    print(f"Elementos: {len(folders)}")
    print(f"CSV canónicos ausentes: {len(missing)}")
    print(f"Con líneas publicadas: {with_lines}")
    print(f"Con niveles publicados: {with_levels}")
    print(f"Con niveles pero sin transiciones: {len(levels_without_lines)}")
    if levels_without_lines:
        print("  " + ", ".join(levels_without_lines))
    if missing:
        raise SystemExit("\n".join(missing))


if __name__ == "__main__":
    main()
