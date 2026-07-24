#!/usr/bin/env python3
"""Correcciones de normalización y persistencia para la fase científica 2.

Este lanzador conserva el importador principal y sustituye tres puntos sensibles:

- transiciones de rayos X con subcapas como K-L3 o L2-M4;
- neutrones desde la tabla NCNR estable de ocho columnas;
- fusión conservadora: una consulta vacía no borra datos ya versionados.
"""

from __future__ import annotations

import re
import urllib.error

import enrich_science_phase_2 as phase2


phase2.TRANSITION_RE = re.compile(
    r"^(?:K|L[1-3]?|M[1-5]?|N[1-7]?)(?:K|L[1-3]?|M[1-5]?|N[1-7]?)$",
    re.IGNORECASE,
)

# Columnas oficiales: isotope, conc, Coh b, Inc b, Coh xs, Inc xs,
# Scatt xs y Abs xs. Esta variante no depende de rowspan HTML.
SIMPLE_NEUTRON_URL = "https://ncnr.nist.gov/resources/n-lengths/list.html"
phase2.NEUTRON_TABLE_URL = SIMPLE_NEUTRON_URL
ISOTOPE_RE = re.compile(r"^(?:(\d+))?([A-Z][a-z]?)$")


def _record(
    *,
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
            SIMPLE_NEUTRON_URL,
            "Valor evaluado para neutrones de 2200 m/s. Los valores entre paréntesis son incertidumbres; las cantidades complejas se conservan como texto.",
        ),
        "energy": "neutrón térmico · 2200 m/s",
        "particle_or_photon": "neutrón",
        "isotope": isotope,
        "transition": "",
        "process": property_id.replace("neutron_", "").replace("_", " "),
        "abundance": abundance,
    }


def parse_neutron_table(elements: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Interpreta la lista NCNR de ocho columnas sin depender de celdas combinadas."""

    try:
        html_rows = phase2.parse_html_rows(phase2.fetch(SIMPLE_NEUTRON_URL, timeout=90))
    except (urllib.error.URLError, TimeoutError):
        return {}

    valid_symbols = {element["symbol"] for element in elements}
    result: dict[str, list[dict[str, str]]] = {symbol: [] for symbol in valid_symbols}

    for original_cells in html_rows:
        cells = [phase2.clean(cell) for cell in original_cells]
        if len(cells) < 8:
            continue

        isotope_text = cells[0].replace(" ", "")
        match = ISOTOPE_RE.fullmatch(isotope_text)
        if not match:
            continue
        mass_number, symbol = match.groups()
        if symbol not in valid_symbols:
            continue

        isotope = f"{symbol}-{mass_number}" if mass_number else f"{symbol}-natural"
        abundance, coherent_b, incoherent_b, coherent_xs, incoherent_xs, total_xs, absorption_xs = cells[1:8]
        fields = (
            ("neutron_coherent_scattering_length", coherent_b, "fm"),
            ("neutron_incoherent_scattering_length", incoherent_b, "fm"),
            ("neutron_coherent_cross_section", coherent_xs, "barn"),
            ("neutron_incoherent_cross_section", incoherent_xs, "barn"),
            ("neutron_total_scattering_cross_section", total_xs, "barn"),
            ("neutron_absorption_cross_section", absorption_xs, "barn"),
        )
        for property_id, value, unit in fields:
            if phase2.numeric(value) is None:
                continue
            result[symbol].append(
                _record(
                    isotope=isotope,
                    abundance=abundance,
                    property_id=property_id,
                    value=value,
                    unit=unit,
                )
            )

    return {symbol: records for symbol, records in result.items() if records}


def write_radiation(element: dict[str, str], generated: list[dict[str, str]]) -> None:
    """Reemplaza solo los proveedores que hayan devuelto datos nuevos."""

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
