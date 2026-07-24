#!/usr/bin/env python3
"""Descarga de nuevo el espectro Fe I cuando el CSV local está vacío.

La aplicación conserva además cuatro líneas educativas como respaldo. Este script
restaura la fuente NIST completa dentro de la carpeta canónica del hierro sin
forzar la descarga masiva de espectros para los 118 elementos.
"""

from __future__ import annotations

import enrich_science_phase_2 as phase2


def main() -> None:
    iron = next((item for item in phase2.read_manifest() if item["symbol"] == "Fe"), None)
    if iron is None:
        raise RuntimeError("No se encontró Fe en elements.manifest.csv")

    repaired = phase2.repair_nist_spectrum(iron)
    if repaired:
        phase2.append_source(
            iron,
            "NIST ASD",
            "Atomic spectral lines repair",
            "spectra_nist_lines.csv",
            phase2.nist_spectrum_url("Fe"),
            "ok",
            "Espectro Fe I recuperado porque el CSV canónico estaba ausente o vacío.",
        )
        print("Espectro Fe I reparado desde NIST ASD.")
    else:
        print("El espectro Fe I ya contenía datos o NIST no respondió; se conserva el respaldo local.")


if __name__ == "__main__":
    main()
