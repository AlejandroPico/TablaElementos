from __future__ import annotations

import argparse
import csv
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_ROOT = ROOT / "data" / "elements"
MANIFEST_PATH = ELEMENTS_ROOT / "elements.manifest.csv"
DEFAULT_IMPORT_DIR = ROOT / "data" / "import" / "nist"

NIST_FILE_RE = re.compile(
    r"^(?P<atomic_number>\d{1,3})_(?P<symbol>[A-Z][a-z]?)_(?P<kind>espectro|niveles)\.csv$",
    re.IGNORECASE,
)

CANONICAL_FILENAMES = {
    "espectro": "spectra_nist_lines.csv",
    "niveles": "spectra_nist_levels.csv",
}


@dataclass(frozen=True)
class ElementTarget:
    atomic_number: str
    symbol: str
    folder: Path


def normalized_atomic_number(value: str) -> str:
    return str(int(value))


def read_manifest() -> dict[tuple[str, str], ElementTarget]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"No existe el manifiesto: {MANIFEST_PATH}")

    targets: dict[tuple[str, str], ElementTarget] = {}
    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            atomic_number = normalized_atomic_number(row["atomic_number"])
            symbol = row["symbol"]
            targets[(atomic_number, symbol.lower())] = ElementTarget(
                atomic_number=atomic_number,
                symbol=symbol,
                folder=ELEMENTS_ROOT / row["folder"],
            )

    return targets


def classify_file(path: Path) -> tuple[str, str, str] | None:
    match = NIST_FILE_RE.match(path.name)
    if not match:
        return None

    atomic_number = normalized_atomic_number(match.group("atomic_number"))
    symbol = match.group("symbol")
    kind = match.group("kind").lower()
    return atomic_number, symbol, kind


def import_file(source: Path, target: ElementTarget, kind: str, *, move: bool, overwrite: bool) -> tuple[str, Path]:
    target.folder.mkdir(parents=True, exist_ok=True)
    destination = target.folder / CANONICAL_FILENAMES[kind]

    if destination.exists() and not overwrite:
        return "skipped", destination

    if move:
        shutil.move(str(source), str(destination))
    else:
        shutil.copy2(source, destination)

    return ("moved" if move else "copied"), destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mueve o copia CSVs exportados desde NIST ASD a data/elements/<elemento>/ con nombres canónicos.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_IMPORT_DIR,
        help=f"Carpeta de entrada. Por defecto: {DEFAULT_IMPORT_DIR}",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Mover archivos en vez de copiarlos.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescribir archivos existentes en la carpeta del elemento.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar qué se haría sin copiar ni mover archivos.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir: Path = args.source.resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de entrada: {source_dir}")

    targets = read_manifest()
    csv_files = sorted(source_dir.glob("*.csv"))

    copied = 0
    moved = 0
    skipped = 0
    unknown = 0
    unmatched = 0

    for source in csv_files:
        classified = classify_file(source)
        if classified is None:
            unknown += 1
            print(f"[IGNORADO] Nombre no reconocido: {source.name}")
            continue

        atomic_number, symbol, kind = classified
        target = targets.get((atomic_number, symbol.lower()))
        if target is None:
            unmatched += 1
            print(f"[SIN ELEMENTO] {source.name} no coincide con el manifiesto")
            continue

        destination = target.folder / CANONICAL_FILENAMES[kind]
        if args.dry_run:
            print(f"[DRY] {source.name} -> {destination.relative_to(ROOT)}")
            continue

        result, destination = import_file(source, target, kind, move=args.move, overwrite=args.overwrite)
        if result == "copied":
            copied += 1
            print(f"[COPIADO] {source.name} -> {destination.relative_to(ROOT)}")
        elif result == "moved":
            moved += 1
            print(f"[MOVIDO] {source.name} -> {destination.relative_to(ROOT)}")
        else:
            skipped += 1
            print(f"[EXISTE] {destination.relative_to(ROOT)}")

    print()
    print("Resumen de importación NIST")
    print(f"Carpeta de entrada: {source_dir}")
    print(f"CSVs detectados:    {len(csv_files)}")
    print(f"Copiados:           {copied}")
    print(f"Movidos:            {moved}")
    print(f"Ya existentes:      {skipped}")
    print(f"Ignorados:          {unknown}")
    print(f"Sin elemento:       {unmatched}")


if __name__ == "__main__":
    main()
