# Ciencia avanzada · Fase 2

Fecha de implementación: 24 de julio de 2026.

Esta fase incorpora los puntos 4, 5 y 6 de la hoja de ruta científica:

1. visualización nuclear avanzada;
2. termodinámica y fases;
3. rayos X, XPS/Auger, atenuación y neutrones.

Toda la información se conserva por elemento dentro de:

```text
data/elements/<NNN-Símbolo-nombre>/
```

No existe una base científica paralela fuera de esta estructura.

## 1. Corrección del espectro óptico del hierro

El archivo canónico:

```text
data/elements/026-Fe-iron/spectra_nist_lines.csv
```

estaba vacío. El generador anterior interpretaba la mera presencia del archivo como suficiente para impedir las líneas educativas de respaldo. Por ello, Fe podía aparecer con cero líneas aunque `data/raw/sample-lines.csv` contuviera cuatro transiciones visibles.

La solución tiene dos niveles:

- `scripts/repair_spectral_fallbacks.py` garantiza que ningún CSV NIST vacío deje sin espectro a un elemento que tenga líneas locales de respaldo;
- `scripts/repair_iron_spectrum.py` intenta restaurar exclusivamente Fe I desde NIST ASD y guarda el CSV recuperado dentro de la carpeta del hierro.

Las líneas de respaldo se identifican como educativas y nunca se presentan como una descarga NIST completa.

## 2. Pestaña Nuclear

La pestaña `Nuclear` utiliza directamente `isotopes.csv`, descargado previamente desde IAEA LiveChart.

### Visualizaciones

- mapa de número de neutrones frente a vida media en escala logarítmica;
- código cromático por modo principal de desintegración;
- isótopos estables situados en la parte superior;
- barras de abundancia isotópica natural;
- selección interactiva de nucleído;
- ficha detallada del nucleído seleccionado.

### Datos mostrados

- protones Z;
- neutrones N;
- número másico A;
- estabilidad y vida media;
- abundancia;
- modo principal de desintegración;
- espín y paridad;
- momento dipolar magnético nuclear;
- momento cuadrupolar eléctrico;
- energía de enlace;
- energías Qα y QEC.

La ausencia de vida media no se interpreta como estabilidad. Solo se considera estable una fila cuyo campo IAEA indique expresamente `STABLE`.

## 3. Pestaña Termodinámica

Los registros se almacenan en:

```text
data/elements/<elemento>/thermodynamics.csv
```

### Consolidación local

El importador copia con trazabilidad desde `physical_properties.csv`:

- estado estándar;
- densidad;
- punto de fusión;
- punto de ebullición.

La fuente original se conserva en las notas.

### Ampliación remota

PubChem PUG View se consulta para localizar, cuando estén publicados:

- entalpía de fusión;
- entalpía de vaporización;
- entalpía de sublimación;
- capacidad calorífica;
- entropía molar;
- punto triple;
- temperatura y presión críticas;
- presión de vapor.

### Visualizaciones

- ficha de magnitudes principales;
- eje de temperaturas de transición;
- curva Cp frente a temperatura cuando existen varios puntos;
- curva de presión de vapor en escala logarítmica cuando existen varios puntos;
- lista completa de registros con temperatura, presión, fase y fuente.

No se dibuja una curva a partir de un único valor y no se inventan parámetros de Antoine.

## 4. Pestaña Radiación

Los datos se almacenan en:

```text
data/elements/<elemento>/radiation_interaction.csv
```

La pestaña contiene cuatro modos internos.

### Rayos X

Fuente prevista: NIST X-Ray Transition Energies.

Se almacenan:

- transición o borde;
- energía teórica;
- energía experimental cuando existe;
- unidad;
- fuente y fecha.

La interfaz utiliza un espectro de líneas características en escala energética logarítmica.

### Atenuación

Fuente: NIST X-Ray Mass Attenuation Coefficients.

Se almacenan por energía:

- coeficiente másico de atenuación `μ/ρ`;
- coeficiente másico de absorción de energía `μen/ρ`;
- bordes de absorción identificados;
- energía del fotón.

La interfaz muestra ambas curvas en escala logarítmica y señala los bordes publicados.

### XPS y Auger

El NIST XPS Database no se trata como una API masiva no documentada. Las exportaciones autorizadas se importan desde:

```text
data/import/xps/*.csv
```

Cada registro conserva:

- elemento;
- orbital o línea Auger;
- energía de enlace o cinética;
- compuesto;
- estado químico;
- procedencia.

La energía XPS depende del entorno químico y nunca se reduce a un valor universal del elemento.

### Neutrones

Fuente: tabla de longitudes de dispersión y secciones eficaces de NIST NCNR, evaluada para neutrones de 2200 m/s.

Se almacenan por elemento o isótopo:

- longitud coherente de dispersión;
- sección coherente;
- sección incoherente;
- sección total de dispersión;
- sección de absorción;
- abundancia cuando se publica.

Las barras resumen priorizan el registro natural; cuando no existe, muestran un promedio descriptivo de los registros disponibles y la tabla conserva todos los valores isotópicos.

## 5. Importadores

### Enriquecimiento normal

```bash
npm run enrich:science2
```

Consulta termodinámica, rayos X, atenuación y neutrones; también incorpora exportaciones XPS locales.

### Enriquecimiento completo de las fases 1 y 2

```bash
npm run enrich:all
```

### Reparación focalizada de Fe I

```bash
npm run repair:iron-spectrum
```

### Reparación óptica masiva

```bash
npm run repair:spectra:all
```

La reparación masiva es opcional porque puede generar miles de líneas por elemento y aumentar significativamente el tamaño del repositorio.

## 6. Despliegue reproducible

`npm run build` no consulta servicios externos. Utiliza únicamente los CSV versionados y genera:

```text
public/data/spectra.sample.json
public/data/elements/<símbolo>.json
```

Esto evita que una caída temporal de PubChem o NIST rompa GitHub Pages.

Las descargas y su persistencia se ejecutan manualmente mediante:

```text
.github/workflows/refresh-scientific-data.yml
```

Ese workflow:

1. descarga y normaliza los datos;
2. repara Fe I;
3. regenera los datasets;
4. ejecuta `svelte-check`;
5. valida el build de producción;
6. confirma únicamente cambios de `data/elements`;
7. provoca después el despliegue normal de Pages.

La descarga masiva de todos los espectros ópticos puede activarse como opción explícita del workflow.

## 7. Comparador y resumen

El comparador incorpora tres ámbitos nuevos:

- `Nuclear`;
- `Termodinámica`;
- `Radiación`.

El resumen de cada elemento añade indicadores de:

- nucleídos e isótopos estables;
- entalpías disponibles;
- líneas características de rayos X;
- puntos de atenuación;
- registros neutrónicos;
- líneas ópticas.

## 8. Limitaciones científicas

- Los datos nucleares corresponden a nucleídos concretos, no al elemento abstracto.
- La termodinámica depende de fase, presión, temperatura, pureza y método.
- XPS depende del compuesto y del estado químico.
- Las secciones neutrónicas térmicas no sustituyen curvas dependientes de energía.
- La atenuación elemental no describe automáticamente una aleación, compuesto o mezcla.
- Los elementos superpesados pueden carecer de datos experimentales en varios dominios.
- Una celda vacía significa «sin dato integrado», no valor cero.
