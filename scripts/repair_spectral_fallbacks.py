#!/usr/bin/env python3
"""Recupera líneas de respaldo cuando un CSV NIST existe pero no aporta datos.

El generador principal distingue entre archivo ausente y archivo presente. Un CSV
vacío de NIST no debe bloquear las líneas educativas locales: esta pasada revisa
los JSON generados y utiliza ``data/raw/sample-lines.csv`` exclusivamente cuando
el elemento sigue teniendo cero líneas interpretables.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = ROOT / "data" / "raw" / "sample-lines.csv"
TARGETS = (
    ROOT / "data" / "processed" / "spectra.sample.json",
    ROOT / "public" / "data" / "spectra.sample.json",
)
VISIBLE_MIN_NM = 380.0
VISIBLE_MAX_NM = 750.0


def wavelength_to_hex(wavelength_nm: float) -> str:
    gamma = 0.8
    wavelength = float(wavelength_nm)
    if wavelength < 380 or wavelength > 750:
        return "#8b95a7"
    if wavelength < 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / 60
        red, green, blue = (-(wavelength - 440) / 60 * attenuation) ** gamma, 0.0, attenuation ** gamma
    elif wavelength < 490:
        red, green, blue = 0.0, ((wavelength - 440) / 50) ** gamma, 1.0
    elif wavelength < 510:
        red, green, blue = 0.0, 1.0, (-(wavelength - 510) / 20) ** gamma
    elif wavelength < 580:
        red, green, blue = ((wavelength - 510) / 70) ** gamma, 1.0, 0.0
    elif wavelength < 645:
        red, green, blue = 1.0, (-(wavelength - 645) / 65) ** gamma, 0.0
    else:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / 105
        red, green, blue = attenuation ** gamma, 0.0, 0.0
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, round(red * 255))),
        max(0, min(255, round(green * 255))),
        max(0, min(255, round(blue * 255))),
    )


def region(wavelength: float) -> str:
    if wavelength < VISIBLE_MIN_NM:
        return "ultravioleta"
    if wavelength > VISIBLE_MAX_NM:
        return "infrarrojo"
    return "visible"


def load_samples() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    if not SAMPLE_PATH.exists():
        return grouped
    with SAMPLE_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            wavelength = float(row["wavelength_nm"])
            grouped.setdefault(row["element"], []).append({
                "element": row["element"],
                "species": row["species"],
                "wavelength_nm": wavelength,
                "intensity": float(row["intensity"]),
                "kind": row["kind"],
                "lower_level_ev": float(row["lower_level_ev"]),
                "upper_level_ev": float(row["upper_level_ev"]),
                "transition": row["transition"],
                "label": row["label"],
                "source_note": f"{row['source_note']} · respaldo local porque el CSV NIST no produjo líneas.",
                "visible": VISIBLE_MIN_NM <= wavelength <= VISIBLE_MAX_NM,
                "approximate_color": wavelength_to_hex(wavelength),
                "spectral_region": region(wavelength),
            })
    return grouped


def repair(path: Path, samples: dict[str, list[dict[str, Any]]]) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    grouped = payload.setdefault("spectral_lines_by_element", {})
    nist = payload.get("nist_by_element", {})
    repaired = 0
    for symbol, fallback in samples.items():
        if grouped.get(symbol):
            continue
        grouped[symbol] = fallback
        repaired += 1
        status = nist.get(symbol, {}).get("espectro")
        if isinstance(status, dict):
            previous = str(status.get("notes") or "").strip()
            status["notes"] = (
                f"{previous} Se muestran {len(fallback)} líneas educativas de respaldo; "
                "el CSV NIST local no produjo registros interpretables."
            ).strip()
    payload.setdefault("metadata", {})["spectral_fallback_elements"] = repaired
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return repaired


def main() -> None:
    samples = load_samples()
    repaired = 0
    for target in TARGETS:
        repaired = max(repaired, repair(target, samples))
    print(f"Recuperación espectral: {repaired} elementos recibieron líneas locales de respaldo.")


if __name__ == "__main__":
    main()
