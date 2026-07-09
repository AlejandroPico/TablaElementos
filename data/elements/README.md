# `data/elements/`

Carpeta raíz para la futura tabla periódica ampliada.

La estructura prevista es una carpeta por elemento, ordenada por número atómico y símbolo:

```txt
data/elements/
├─ elements.manifest.csv
├─ 001-H-hydrogen/
├─ 002-He-helium/
├─ 003-Li-lithium/
└─ ...
```

Git no conserva carpetas vacías. Por eso el repositorio incluye el manifiesto `elements.manifest.csv` y el script `scripts/init_elements_structure.py`, que genera localmente las 118 carpetas con plantillas CSV.

## Convención de carpetas

```txt
NNN-Symbol-english-name
```

Ejemplos:

```txt
001-H-hydrogen
008-O-oxygen
026-Fe-iron
092-U-uranium
118-Og-oganesson
```

## Archivos previstos por elemento

Cada carpeta de elemento podrá contener CSVs independientes por dominio científico:

```txt
identity.csv                    # Identidad básica, posición, nombres, bloque, grupo, periodo
spectra_nist_lines.csv          # Líneas espectrales descargadas de NIST ASD
spectra_nist_levels.csv         # Niveles de energía / transiciones si se separan de líneas
atomic_properties.csv           # Radio, configuración electrónica, electronegatividad, ionización, etc.
isotopes.csv                    # Isótopos, vida media, abundancia, modos de decaimiento
physical_properties.csv         # Densidad, puntos de fusión/ebullición, conductividad, dureza
chemical_properties.csv         # Estados de oxidación, reactividad, compuestos comunes
materials.csv                   # Cristalografía, fases, aleaciones, magnetismo, superconductividad
thermodynamics.csv              # Entalpías, entropía, calor específico, energía libre
geochemistry.csv                # Abundancia terrestre, minerales, extracción
astrophysics.csv                # Abundancia cósmica, nucleosíntesis, presencia estelar
biology_medicine.csv            # Función biológica, toxicidad, usos médicos
environment_safety.csv          # Medio ambiente, peligros, manipulación, regulación
industry_economy.csv            # Usos industriales, producción, reservas, criticidad, reciclaje
history.csv                     # Descubrimiento, etimología, contexto histórico
compounds.csv                   # Compuestos, sales, óxidos, minerales, moléculas relevantes
analytical_methods.csv          # Métodos de detección: XRF, ICP-MS, absorción atómica, etc.
radiation_interaction.csv       # Rayos X, neutrones, activación, secciones eficaces
photonics_color.csv             # Color de llama, fluorescencia, pigmentos, LEDs, láseres
computational.csv               # Datos calculados, DFT, potenciales interatómicos
sources.csv                     # Fuente, URL, fecha de descarga, licencia/notas
```

## Reglas de trabajo

- Los datos descargados deben guardarse en bruto siempre que sea posible.
- No se consultarán APIs externas en tiempo de ejecución de la web.
- Todo dato usado por la aplicación debe estar versionado dentro del repositorio.
- `data/raw/` se mantiene temporalmente por compatibilidad con la V1 actual.
- La migración completa se hará en fases: primero estructura, luego normalización, después consumo desde frontend.
