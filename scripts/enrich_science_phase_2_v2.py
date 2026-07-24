#!/usr/bin/env python3
"""Correcciones de normalización y persistencia para la fase científica 2.

Este lanzador conserva el importador principal y sustituye tres puntos sensibles:

- transiciones de rayos X con subcapas como K-L3 o L2-M4;
- tabla NCNR con filas naturales e isotópicas bajo rowspan;
- fusión conservadora: una consulta vacía no borra datos ya versionados.
"""

from __future__ import annotations

import re
import urllib.error

import enrich_science_phase_2 as phase2


# K-L3, L2-M4, M5-N7... después de eliminar signos y espacios.
phase2.TRANSITION_RE = re.compile(
    r"^(?:K|L[1-3]?|M[1-5]?|N[1-7]?)(?:K|L[1-3]?|M[1-5]?|N[1-7]?)$",
    re.IGNORECASE,
)


def _record(
    *,
    symbol: str,
    isotope: str,
    abundance: str,
    property_id: str,
    value: str,
    unit: str,
) -> dict[str, str]:
    return {
        **phase2.base_row(
            property_id,
            value,
            unit,
            "NIST NCNR Neutron Scattering Lengths and Cross Sections",
            phase2.NEUTRON_TABLE_URL,
            "Valor evaluado a 2200 m/s. Deben consultarse en la fuente las incertidumbres, valores complejos y excepciones resonantes.",
        ),
        "energy": "neutrón térmico · 2200 m/s",
        "particle_or_photon": "neutrón",
        "isotope": isotope or f"{symbol}-natural",
        "transition": "",
        "process": property_id.replace("neutron_", "").replace("_", " "),
        "abundance": abundance,
    }


def parse_neutron_table(elements: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Interpreta la tabla NCNR respetando sus celdas combinadas.

    Tras retirar el símbolo y Z, las columnas son:
    A, I(π), abundancia, bc, b+, b−, σc, σi, σs y σa.
    Las filas naturales tienen A vacío; las isotópicas conservan A.
    """

    try:
        html_rows = phase2.parse_html_rows(phase2.fetch(phase2.NEUTRON_TABLE_URL, timeout=90))
    except (urllib.error.URLError, TimeoutError):
        return {}

    atomic_number_by_symbol = {item["symbol"]: item["atomic_number"] for item in elements}
    valid_symbols = set(atomic_number_by_symbol)
    result: dict[str, list[dict[str, str]]] = {symbol: [] for symbol in valid_symbols}
    current_symbol = ""

    for original_cells in html_rows:
        cells = [phase2.clean(cell) for cell in original_cells]
        if not cells:
            continue

        # Las filas principales comienzan con el símbolo. Las filas isotópicas
        # heredan símbolo y Z mediante rowspan y comienzan directamente por A.
        if cells[0] in valid_symbols:
            current_symbol = cells.pop(0)
        if not current_symbol:
            continue

        z_text = atomic_number_by_symbol[current_symbol]
        if cells and phase2.clean(cells[0]) == phase2.clean(z_text):
            cells.pop(0)

        if not cells or phase2.clean(cells[0]).lower() in {"a", "isotope"}:
            continue

        # Los vacíos intermedios son significativos en las filas naturales.
        cells = cells + [""] * max(0, 10 - len(cells))
        mass_number, _spin, abundance, bc, _b_plus, _b_minus, sigma_c, sigma_i, sigma_s, sigma_a = cells[:10]

        isotope = f"{current_symbol}-{mass_number}" if phase2.numeric(mass_number) is not None else f"{current_symbol}-natural"
        fields = (
            ("neutron_coherent_scattering_length", bc, "fm"),
            ("neutron_coherent_cross_section", sigma_c, "barn"),
            ("neutron_incoherent_cross_section", sigma_i, "barn"),
            ("neutron_total_scattering_cross_section", sigma_s, "barn"),
            ("neutron_absorption_cross_section", sigma_a, "barn"),
        )
        for property_id, value, unit in fields:
            if phase2.numeric(value) is None:
                continue
            result[current_symbol].append(
                _record(
                    symbol=current_symbol,
                    isotope=isotope,
                    abundance=abundance,
                    property_id=property_id,
                    value=value,
                    unit=unit,
                )
            )

    return {symbol: records for symbol, records in result.items() if records}


def write_radiation(element: dict[str, str], generated: list[dict[str, str]]) -> None:
    """Reemplaza solo los proveedores que hayan devuelto datos nuevos.

    Si NIST X-Ray, NCNR o una importación XPS falla temporalmente, las filas
    oficiales ya guardadas en la carpeta del elemento permanecen intactas.
    """

    if not generated:
        return

    path = phase2.ELEMENTS_ROOT / element["folder"] / "radiation_interaction.csv"
    rows = phase2.read_csv(path)
    incoming_sources = {
        phase2.clean(row.get("source"))
        for row in generated
        if phase2.clean(row.get("source"))
    }
    if incoming_sources:
        rows = [
            row for row in rows
            if phase2.clean(row.get("source")) not in incoming_sources
        ]
    rows.extend(generated)
    phase2.write_csv(path, rows, phase2.RADIATION_FIELDS)


phase2.parse_neutron_table = parse_neutron_table
phase2.write_radiation = write_radiation


if __name__ == "__main__":
    phase2.main()
