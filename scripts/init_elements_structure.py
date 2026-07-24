from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS_ROOT = ROOT / "data" / "elements"
MANIFEST_PATH = ELEMENTS_ROOT / "elements.manifest.csv"

PROPERTY_HEADER = "property,value,unit,source,source_url,retrieved_at,notes\n"

CSV_TEMPLATES: dict[str, str] = {
    "identity.csv": "atomic_number,symbol,name_en,name_es,group,period,block,category,folder,pubchem_name,standard_state,group_block,source,source_url,retrieved_at\n",
    "spectra_nist_lines.csv": "element,species,obs_wl_nm,ritz_wl_nm,intensity,transition,lower_level,upper_level,source,source_url,retrieved_at,notes\n",
    "spectra_nist_levels.csv": "level_id,energy,energy_unit,configuration,term,j,source,source_url,retrieved_at,notes\n",
    "atomic_properties.csv": PROPERTY_HEADER,
    "isotopes.csv": "isotope,mass_number,atomic_mass_u,abundance_percent,half_life,decay_mode,spin,source,source_url,retrieved_at,notes\n",
    "physical_properties.csv": PROPERTY_HEADER,
    "chemical_properties.csv": PROPERTY_HEADER,
    "materials.csv": "property,value,unit,source,source_url,retrieved_at,notes,material_id,phase,structure,space_group,lattice_a,lattice_b,lattice_c,lattice_alpha,lattice_beta,lattice_gamma\n",
    "thermodynamics.csv": "property,value,unit,temperature_k,pressure,phase,source,source_url,retrieved_at,notes\n",
    "geochemistry.csv": "property,value,unit,environment,source,source_url,retrieved_at,notes\n",
    "astrophysics.csv": "property,value,unit,context,source,source_url,retrieved_at,notes\n",
    "biology_medicine.csv": "property,value,unit,organism_or_use,source,source_url,retrieved_at,notes\n",
    "environment_safety.csv": "property,value,unit,classification,source,source_url,retrieved_at,notes\n",
    "industry_economy.csv": "property,value,unit,year,region,source,source_url,retrieved_at,notes\n",
    "history.csv": "property,value,unit,source,source_url,retrieved_at,notes\n",
    "compounds.csv": "formula,name,compound_type,oxidation_state,source,source_url,retrieved_at,notes\n",
    "analytical_methods.csv": "method,signal,limit_of_detection,unit,source,source_url,retrieved_at,notes\n",
    "radiation_interaction.csv": "property,value,unit,energy,particle_or_photon,isotope,transition,process,source,source_url,retrieved_at,notes\n",
    "photonics_color.csv": "property,value,unit,wavelength_nm,color,source,source_url,retrieved_at,notes\n",
    "computational.csv": "property,value,unit,method,basis_or_model,source,source_url,retrieved_at,notes\n",
    "sources.csv": "provider,dataset,target_file,source_url,retrieved_at,status,sha256,notes\n",
}

README_TEMPLATE = """# {atomic_number} · {symbol} · {name_en} / {name_es}

Carpeta de datos brutos, normalizados y derivados para el elemento **{name_es}** (`{symbol}`).

## Reglas obligatorias

- Mantener aquí todos los CSV específicos de este elemento.
- Guardar datos descargados de fuentes oficiales con el menor procesado posible.
- Añadir cada descarga o fuente a `sources.csv`.
- Marcar explícitamente cualquier valor derivado, calculado, estimado o predicho.
- Conservar condiciones: temperatura, presión, fase, isótopo, carga, coordinación y método cuando sean relevantes.
- No borrar archivos originales si después se generan versiones normalizadas.

## Dominios principales

- `identity.csv`: identidad y posición periódica.
- `atomic_properties.csv`: configuración, valencia, ionización, afinidad y radios diferenciados.
- `chemical_properties.csv`: estados de oxidación y comportamiento químico.
- `physical_properties.csv`: estado, densidad y cambios de fase.
- `materials.csv`: alótropos, fases, estructuras, grupos espaciales y parámetros de red.
- `isotopes.csv`: nucleídos y propiedades nucleares.
- `thermodynamics.csv`: entalpías, capacidades caloríficas, presión de vapor y transiciones de fase.
- `radiation_interaction.csv`: rayos X, XPS/Auger, atenuación y datos neutrónicos.
- `spectra_nist_lines.csv` y `spectra_nist_levels.csv`: espectroscopia óptica NIST.
- Resto de CSV: contexto, biología, industria, análisis y fuentes.

## Campos avanzados incorporados

`atomic_properties.csv` puede contener, entre otros:

- `electron_configuration_abbreviated`;
- `valence_shell_configuration`;
- `outer_shell_electron_count`;
- `valence_electron_count`;
- `common_valences`;
- `ionization_energy_1`, `ionization_energy_2`, ...;
- `van_der_waals_radius`;
- `covalent_radius`;
- `metallic_radius`;
- `ionic_radius_<carga>_<coordinación>`.

`materials.csv` conserva cada fase con `material_id`, `phase`, `structure`, `space_group` y parámetros de red.

`radiation_interaction.csv` conserva cada magnitud con su energía, partícula, isótopo, transición, proceso y procedencia.
"""


def read_manifest() -> list[dict[str, str]]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"No existe el manifiesto: {MANIFEST_PATH}")

    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False

    path.write_text(content, encoding="utf-8")
    return True


def init_element_folder(element: dict[str, str]) -> tuple[int, int]:
    folder = ELEMENTS_ROOT / element["folder"]
    folder.mkdir(parents=True, exist_ok=True)

    created_files = 0
    skipped_files = 0

    readme_content = README_TEMPLATE.format(**element)
    if write_if_missing(folder / "README.md", readme_content):
        created_files += 1
    else:
        skipped_files += 1

    for filename, header in CSV_TEMPLATES.items():
        if write_if_missing(folder / filename, header):
            created_files += 1
        else:
            skipped_files += 1

    return created_files, skipped_files


def main() -> None:
    elements = read_manifest()
    created_total = 0
    skipped_total = 0

    for element in elements:
        created, skipped = init_element_folder(element)
        created_total += created
        skipped_total += skipped

    print(f"Elementos procesados: {len(elements)}")
    print(f"Archivos creados:     {created_total}")
    print(f"Archivos existentes:  {skipped_total}")
    print(f"Carpeta raíz:         {ELEMENTS_ROOT}")


if __name__ == "__main__":
    main()
