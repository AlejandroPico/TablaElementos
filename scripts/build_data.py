#!/usr/bin/env python3
"""Genera el dataset estático de Espectros Atómicos.

La aplicación final no consulta servicios externos. Este script trabaja solo con
CSV locales versionados en el repositorio y produce un JSON optimizado para la web.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PUBLIC_DATA_DIR = ROOT / "public" / "data"

VISIBLE_MIN_NM = 380.0
VISIBLE_MAX_NM = 750.0


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


def wavelength_to_hex(wavelength_nm: float) -> str:
    """Aproximación RGB educativa para el rango visible.

    Fuera de 380-750 nm devolvemos un gris técnico porque UV/IR no tienen color
    visible directo para el ojo humano.
    """

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


def load_elements() -> dict[str, Element]:
    elements: dict[str, Element] = {}

    with (RAW_DIR / "elements.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            element = Element(
                symbol=row["symbol"],
                name_es=row["name_es"],
                name_en=row["name_en"],
                atomic_number=int(row["atomic_number"]),
                group=int(row["group"]),
                period=int(row["period"]),
                category=row["category"],
                summary=row["summary"],
            )
            elements[element.symbol] = element

    return elements


def load_lines(elements: dict[str, Element]) -> list[SpectralLine]:
    lines: list[SpectralLine] = []

    with (RAW_DIR / "sample-lines.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            symbol = row["element"]
            if symbol not in elements:
                raise ValueError(f"La línea espectral usa un elemento desconocido: {symbol}")

            wavelength = float(row["wavelength_nm"])
            line = SpectralLine(
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
            lines.append(line)

    return lines


def build_payload() -> dict[str, Any]:
    elements = load_elements()
    lines = load_lines(elements)

    grouped_lines: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in elements}

    for line in sorted(lines, key=lambda item: (item.element, item.wavelength_nm)):
        grouped_lines[line.element].append(asdict(line))

    ordered_elements = sorted(elements.values(), key=lambda item: item.atomic_number)

    return {
        "metadata": {
            "project": "Espectros Atómicos",
            "dataset": "sample-v1",
            "description": "Dataset local de muestra para validar arquitectura, visualización e interfaz.",
            "external_runtime_requests": False,
            "visible_range_nm": [VISIBLE_MIN_NM, VISIBLE_MAX_NM],
            "generated_by": "scripts/build_data.py",
        },
        "elements": [asdict(element) for element in ordered_elements],
        "spectral_lines_by_element": grouped_lines,
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
    print(f"Dataset generado: {element_count} elementos, {line_count} líneas espectrales.")
    print(f"- {processed_path.relative_to(ROOT)}")
    print(f"- {public_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
