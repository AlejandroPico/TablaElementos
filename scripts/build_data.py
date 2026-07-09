#!/usr/bin/env python3
"""Genera el dataset estático de Tabla elementos.

La aplicación no consulta servicios externos en tiempo de ejecución. Este script
lee datos locales versionados y genera el JSON que consume el frontend.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
ELEMENTS_DIR = ROOT / "data" / "elements"
IMPORT_NIST_DIR = ROOT / "data" / "import" / "nist"
MANIFEST_PATH = ELEMENTS_DIR / "elements.manifest.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
PUBLIC_DATA_DIR = ROOT / "public" / "data"

VISIBLE_MIN_NM = 380.0
VISIBLE_MAX_NM = 750.0
MAX_IMPORTED_LINES_PER_ELEMENT = 700

CATEGORY_ES = {
    "nonmetal": "no metal",
    "noble gas": "gas noble",
    "alkali metal": "metal alcalino",
    "alkaline earth metal": "metal alcalinotérreo",
    "metalloid": "metaloide",
    "halogen": "halógeno",
    "post-transition metal": "metal post-transición",
    "transition metal": "metal de transición",
    "lanthanide": "lantánido",
    "actinide": "actínido",
    "unknown": "desconocido",
}

CANONICAL_NIST_FILES = {
    "espectro": "spectra_nist_lines.csv",
    "niveles": "spectra_nist_levels.csv",
}

LEGACY_NIST_FILES = {
    "espectro": "{atomic_number:03d}_{symbol}_espectro.csv",
    "niveles": "{atomic_number:03d}_{symbol}_niveles.csv",
}


@dataclass(frozen=True)
class Element:
    symbol: str
    name_es: str
    name_en: str
    atomic_number: int
    group: int
    period: int
    category: str
    summary: str


@dataclass(frozen=True)
class SpectralLine:
    element: str
    species: str
    wavelength_nm: float
    intensity: float
    kind: str
    lower_level_ev: float
    upper_level_ev: float
    transition: str
    label: str
    source_note: str
    visible: bool
    approximate_color: str
    spectral_region: str


@dataclass(frozen=True)
class NistFileStatus:
    file: str
    path: str
    present: bool
    table_like: bool
    status: str
    columns: list[str]
    row_count: int
    preview: str
    notes: str


@dataclass(frozen=True)
class NistElementStatus:
    espectro: NistFileStatus
    niveles: NistFileStatus
    imported_line_count: int


def wavelength_to_hex(wavelength_nm: float) -> str:
    gamma = 0.8
    wavelength = float(wavelength_nm)

    if wavelength < 380 or wavelength > 750:
        return "#8b95a7"

    if wavelength < 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        red = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        green = 0.0
        blue = (1.0 * attenuation) ** gamma
    elif wavelength < 490:
        red = 0.0
        green = ((wavelength - 440) / (490 - 440)) ** gamma
        blue = 1.0
    elif wavelength < 510:
        red = 0.0
        green = 1.0
        blue = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif wavelength < 580:
        red = ((wavelength - 510) / (580 - 510)) ** gamma
        green = 1.0
        blue = 0.0
    elif wavelength < 645:
        red = 1.0
        green = (-(wavelength - 645) / (645 - 580)) ** gamma
        blue = 0.0
    else:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        red = (1.0 * attenuation) ** gamma
        green = 0.0
        blue = 0.0

    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, round(red * 255))),
        max(0, min(255, round(green * 255))),
        max(0, min(255, round(blue * 255))),
    )


def spectral_region(wavelength_nm: float) -> str:
    if wavelength_nm < VISIBLE_MIN_NM:
        return "ultravioleta"
    if wavelength_nm > VISIBLE_MAX_NM:
        return "infrarrojo"
    return "visible"


def normalize_category(category: str) -> str:
    return CATEGORY_ES.get(category.strip().lower(), category.strip())


def display_position(atomic_number: int, group: int, period: int) -> tuple[int, int]:
    if 58 <= atomic_number <= 71:
        return atomic_number - 54, 8
    if 90 <= atomic_number <= 103:
        return atomic_number - 86, 9
    return group, period


def load_raw_summaries() -> dict[str, str]:
    path = RAW_DIR / "elements.csv"
    if not path.exists():
        return {}

    summaries: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            summaries[row["symbol"]] = row.get("summary", "")
    return summaries


def load_elements() -> dict[str, Element]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"No existe el manifiesto maestro: {MANIFEST_PATH}")

    summaries = load_raw_summaries()
    elements: dict[str, Element] = {}

    with MANIFEST_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            atomic_number = int(row["atomic_number"])
            group, period = display_position(atomic_number, int(row["group"]), int(row["period"]))
            symbol = row["symbol"]
            element = Element(
                symbol=symbol,
                name_es=row["name_es"],
                name_en=row["name_en"],
                atomic_number=atomic_number,
                group=group,
                period=period,
                category=normalize_category(row["category"]),
                summary=summaries.get(
                    symbol,
                    f"Elemento químico {row['name_es']} ({symbol}), número atómico {atomic_number}.",
                ),
            )
            elements[element.symbol] = element

    return elements


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", ".")
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def load_sample_lines(elements: dict[str, Element]) -> list[SpectralLine]:
    path = RAW_DIR / "sample-lines.csv"
    if not path.exists():
        return []

    lines: list[SpectralLine] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            symbol = row["element"]
            if symbol not in elements:
                continue

            wavelength = float(row["wavelength_nm"])
            lines.append(
                SpectralLine(
                    element=symbol,
                    species=row["species"],
                    wavelength_nm=wavelength,
                    intensity=float(row["intensity"]),
                    kind=row["kind"],
                    lower_level_ev=float(row["lower_level_ev"]),
                    upper_level_ev=float(row["upper_level_ev"]),
                    transition=row["transition"],
                    label=row["label"],
                    source_note=row["source_note"],
                    visible=VISIBLE_MIN_NM <= wavelength <= VISIBLE_MAX_NM,
                    approximate_color=wavelength_to_hex(wavelength),
                    spectral_region=spectral_region(wavelength),
                )
            )

    return lines


def element_folder(element: Element) -> Path:
    return ELEMENTS_DIR / f"{element.atomic_number:03d}-{element.symbol}-{element.name_en.lower()}"


def nist_filename(element: Element, kind: str, legacy: bool = False) -> str:
    if legacy:
        return LEGACY_NIST_FILES[kind].format(atomic_number=element.atomic_number, symbol=element.symbol)
    return CANONICAL_NIST_FILES[kind]


def find_nist_file(element: Element, kind: str) -> Path | None:
    legacy_name = nist_filename(element, kind, legacy=True)
    canonical_name = nist_filename(element, kind)

    candidates = [
        element_folder(element) / canonical_name,
        element_folder(element) / legacy_name,
        IMPORT_NIST_DIR / legacy_name,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def analyze_csv(path: Path | None, expected_name: str) -> NistFileStatus:
    if path is None:
        return NistFileStatus(
            file=expected_name,
            path="",
            present=False,
            table_like=False,
            status="missing",
            columns=[],
            row_count=0,
            preview="",
            notes="No se encontró archivo CSV para este bloque.",
        )

    columns: list[str] = []
    row_count = 0
    preview = ""
    status = "valid_table"
    table_like = True
    notes = "CSV tabular detectado."

    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            columns = [cell.strip() for cell in header]

            for index, row in enumerate(reader, start=1):
                row_count = index
                if not preview and row:
                    preview = " | ".join(cell[:160] for cell in row[:4])[:500]
    except csv.Error as error:
        status = "csv_error"
        table_like = False
        notes = f"Error al leer CSV: {error}"

    if len(columns) <= 1:
        table_like = False
        haystack = f"{' '.join(columns)} {preview}".lower()
        if "newrelic" in haystack or "(()=>{var" in haystack or "javascript" in haystack:
            status = "invalid_single_column_script"
            notes = "El archivo existe, pero parece contener JavaScript de la página en una sola columna, no una tabla NIST limpia."
        elif "<html" in haystack or "<!doctype" in haystack:
            status = "invalid_html_export"
            notes = "El archivo existe, pero parece ser HTML guardado como CSV."
        elif row_count == 0:
            status = "empty_or_header_only"
            notes = "El archivo existe, pero no contiene filas de datos."
        else:
            status = "single_column_csv"
            notes = "El archivo existe, pero solo tiene una columna; se requiere revisión manual del formato."

    return NistFileStatus(
        file=expected_name,
        path=str(path.relative_to(ROOT)),
        present=True,
        table_like=table_like,
        status=status,
        columns=columns[:32],
        row_count=row_count,
        preview=preview,
        notes=notes,
    )


def normalized_header_map(row: dict[str, str]) -> dict[str, str]:
    return {key.lower().strip(): value for key, value in row.items() if key is not None}


def pick_value(row: dict[str, str], needles: list[str]) -> str | None:
    normalized = normalized_header_map(row)
    for key, value in normalized.items():
        compact = key.replace(" ", "").replace(".", "")
        if any(needle in compact for needle in needles):
            return value
    return None


def parse_nist_spectral_lines(element: Element, path: Path | None, status: NistFileStatus) -> list[SpectralLine]:
    if path is None or not status.table_like:
        return []

    lines: list[SpectralLine] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for row in csv.DictReader(handle):
                wavelength_raw = pick_value(row, ["wavelength", "ritz", "observed", "obs"])
                wavelength = parse_float(wavelength_raw)
                if wavelength is None:
                    continue

                intensity_raw = pick_value(row, ["intens", "relint", "rel"])
                intensity = parse_float(intensity_raw) or 0.55
                if intensity > 1:
                    intensity = min(1.0, intensity / 1000 if intensity > 100 else intensity / 100)
                intensity = max(0.08, min(1.0, intensity))

                lower = parse_float(pick_value(row, ["lower", "ei"])) or 0.0
                upper = parse_float(pick_value(row, ["upper", "ek"])) or 0.0
                transition = pick_value(row, ["transition", "term", "config"]) or "Transición NIST"
                species = pick_value(row, ["spectrum", "species", "sp"]) or f"{element.symbol} I"

                lines.append(
                    SpectralLine(
                        element=element.symbol,
                        species=species,
                        wavelength_nm=wavelength,
                        intensity=intensity,
                        kind="emission",
                        lower_level_ev=lower,
                        upper_level_ev=upper,
                        transition=transition,
                        label=f"NIST {wavelength:.3f} nm",
                        source_note="NIST ASD importado desde CSV local.",
                        visible=VISIBLE_MIN_NM <= wavelength <= VISIBLE_MAX_NM,
                        approximate_color=wavelength_to_hex(wavelength),
                        spectral_region=spectral_region(wavelength),
                    )
                )

                if len(lines) >= MAX_IMPORTED_LINES_PER_ELEMENT:
                    break
    except csv.Error:
        return []

    return lines


def analyze_nist_for_element(element: Element) -> tuple[NistElementStatus, list[SpectralLine]]:
    spectrum_path = find_nist_file(element, "espectro")
    levels_path = find_nist_file(element, "niveles")

    spectrum_status = analyze_csv(spectrum_path, CANONICAL_NIST_FILES["espectro"])
    levels_status = analyze_csv(levels_path, CANONICAL_NIST_FILES["niveles"])
    imported_lines = parse_nist_spectral_lines(element, spectrum_path, spectrum_status)

    return (
        NistElementStatus(
            espectro=spectrum_status,
            niveles=levels_status,
            imported_line_count=len(imported_lines),
        ),
        imported_lines,
    )


def build_payload() -> dict[str, Any]:
    elements = load_elements()
    sample_lines = load_sample_lines(elements)

    grouped_lines: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in elements}
    nist_by_element: dict[str, dict[str, Any]] = {}

    imported_total = 0
    malformed_files = 0
    present_files = 0

    for element in sorted(elements.values(), key=lambda item: item.atomic_number):
        nist_status, imported_lines = analyze_nist_for_element(element)
        nist_by_element[element.symbol] = asdict(nist_status)
        imported_total += len(imported_lines)

        for file_status in (nist_status.espectro, nist_status.niveles):
            if file_status.present:
                present_files += 1
            if file_status.present and not file_status.table_like:
                malformed_files += 1

        for line in imported_lines:
            grouped_lines[element.symbol].append(asdict(line))

    for line in sorted(sample_lines, key=lambda item: (item.element, item.wavelength_nm)):
        if not grouped_lines[line.element]:
            grouped_lines[line.element].append(asdict(line))

    ordered_elements = sorted(elements.values(), key=lambda item: item.atomic_number)

    return {
        "metadata": {
            "project": "Tabla elementos",
            "dataset": "elements-v3-nist-by-element",
            "description": "Dataset local con 118 elementos y datos NIST buscados dentro de data/elements/<elemento>/.",
            "external_runtime_requests": False,
            "visible_range_nm": [VISIBLE_MIN_NM, VISIBLE_MAX_NM],
            "generated_by": "scripts/build_data.py",
            "source_layout": "data/elements/<elemento>/",
            "nist_files_present": present_files,
            "nist_files_malformed_or_non_tabular": malformed_files,
            "nist_imported_spectral_lines": imported_total,
        },
        "elements": [asdict(element) for element in ordered_elements],
        "spectral_lines_by_element": grouped_lines,
        "nist_by_element": nist_by_element,
    }


def main() -> None:
    payload = build_payload()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

    processed_path = PROCESSED_DIR / "spectra.sample.json"
    public_path = PUBLIC_DATA_DIR / "spectra.sample.json"

    content = json.dumps(payload, ensure_ascii=False, indent=2)
    processed_path.write_text(content + "\n", encoding="utf-8")
    public_path.write_text(content + "\n", encoding="utf-8")

    element_count = len(payload["elements"])
    line_count = sum(len(lines) for lines in payload["spectral_lines_by_element"].values())
    print(f"Dataset generado: {element_count} elementos, {line_count} líneas espectrales visibles en app.")
    print(f"Archivos NIST presentes: {payload['metadata']['nist_files_present']}")
    print(f"Archivos NIST no tabulares/malformados: {payload['metadata']['nist_files_malformed_or_non_tabular']}")
    print(f"Líneas NIST importadas: {payload['metadata']['nist_imported_spectral_lines']}")
    print(f"- {processed_path.relative_to(ROOT)}")
    print(f"- {public_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
