# `data/elements/`

Repositorio canónico de datos científicos de TablaElementos.

Cada uno de los 118 elementos dispone de una carpeta propia, ordenada por número atómico:

```text
data/elements/
├─ elements.manifest.csv
├─ 001-H-hydrogen/
├─ 002-He-helium/
├─ 003-Li-lithium/
├─ ...
├─ 092-U-uranium/
└─ 118-Og-oganesson/
```

## Convención

```text
NNN-Symbol-english-name
```

Ejemplos:

```text
001-H-hydrogen
008-O-oxygen
026-Fe-iron
092-U-uranium
118-Og-oganesson
```

## Regla principal

Toda propiedad asociada a un elemento debe terminar dentro de su carpeta. Los importadores pueden utilizar temporalmente `data/import/`, pero los valores consumidos por la aplicación se normalizan en los CSV del elemento correspondiente.

No se mantiene una base científica paralela para propiedades atómicas, nucleares, termodinámicas o radiológicas.

## Dominios por elemento

```text
identity.csv
spectra_nist_lines.csv
spectra_nist_levels.csv
atomic_properties.csv
isotopes.csv
physical_properties.csv
chemical_properties.csv
materials.csv
thermodynamics.csv
geochemistry.csv
astrophysics.csv
biology_medicine.csv
environment_safety.csv
industry_economy.csv
history.csv
compounds.csv
analytical_methods.csv
radiation_interaction.csv
photonics_color.csv
computational.csv
sources.csv
```

### Identidad y propiedades atómicas

`identity.csv` conserva nombres, símbolo, Z, posición periódica y clasificación.

`atomic_properties.csv` admite:

- masa y peso atómico;
- configuraciones electrónica y de valencia;
- electrones exteriores y de valencia;
- valencias y estados relacionados;
- afinidad y electronegatividad;
- ionizaciones sucesivas;
- radios de Van der Waals, covalentes, metálicos, cristalinos e iónicos.

### Cristalografía y materiales

`materials.csv` conserva cada fase o alótropo con:

- identificador;
- estructura;
- sistema y grupo espacial;
- parámetros y ángulos de red;
- estabilidad;
- procedencia.

### Física nuclear

`isotopes.csv` conserva los registros de IAEA LiveChart, incluidos, cuando existen:

- Z, N y masa;
- abundancia;
- vida media;
- modos de desintegración;
- espín y paridad;
- momentos dipolar y cuadrupolar;
- energías Q y de separación;
- energía de enlace y exceso de masa.

### Termodinámica

`thermodynamics.csv` utiliza el esquema:

```text
property,value,unit,temperature_k,pressure,phase,source,source_url,retrieved_at,notes
```

Cada valor debe conservar sus condiciones. Una magnitud dependiente de temperatura o fase no se reduce a una constante universal.

### Radiación

`radiation_interaction.csv` utiliza el esquema:

```text
property,value,unit,energy,particle_or_photon,isotope,transition,process,source,source_url,retrieved_at,notes
```

Puede contener:

- transiciones características de rayos X;
- coeficientes de atenuación y absorción;
- XPS y líneas Auger con estado químico;
- longitudes de dispersión neutrónica;
- secciones coherente, incoherente, total y de absorción.

## Procedencia

Cada importación debe registrarse en `sources.csv` con proveedor, dataset, archivo afectado, URL, fecha, estado y notas.

Los valores derivados deben identificarse como derivados; no pueden presentarse como mediciones experimentales.

## Generación de la aplicación

Los CSV se convierten en un JSON independiente por elemento:

```text
public/data/elements/H.json
public/data/elements/Fe.json
public/data/elements/U.json
...
```

El navegador solo descarga el JSON del elemento cuya ficha se abre.

## Actualización remota

El workflow manual:

```text
.github/workflows/refresh-scientific-data.yml
```

descarga, valida y confirma los cambios dentro de estas carpetas. El despliegue normal de Pages es offline y utiliza exclusivamente los CSV versionados.
