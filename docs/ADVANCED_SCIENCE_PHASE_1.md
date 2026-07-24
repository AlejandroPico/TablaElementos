# Ampliación científica · fase 1

Fecha: 24 de julio de 2026.

Esta fase implementa los tres primeros bloques de la hoja de ruta científica de TablaElementos:

1. valencia, electrones de valencia e ionizaciones sucesivas;
2. separación de radios atómicos;
3. estructuras cristalinas, alótropos y visor 3D.

## Arquitectura respetada

No se ha creado una base de datos paralela. Toda la información se lee o escribe dentro de:

```text
data/elements/<NNN-Símbolo-nombre>/
├─ atomic_properties.csv
├─ chemical_properties.csv
├─ materials.csv
└─ sources.csv
```

El build genera después un JSON diferido por elemento en `public/data/elements/<símbolo>.json`.

## Estructura electrónica

La nueva pestaña **Electrones** muestra:

- configuración electrónica;
- configuración abreviada;
- configuración de valencia;
- distribución por capas;
- electrones de la capa exterior;
- electrones de valencia con método documentado;
- valencias comunes;
- estados de oxidación;
- término fundamental cuando está disponible;
- gráfica y tabla de energías de ionización sucesivas.

### Derivaciones

Los campos derivados se marcan como `TablaElementos · derivación` o `TablaElementos · convención documentada`.

No se equipara de forma silenciosa:

- valencia;
- electrones de valencia;
- estados de oxidación.

Para bloques d y f se añade una advertencia porque el conteo depende del criterio químico.

### NIST ASD

El script realiza una consulta masiva a **NIST Atomic Spectra Database · Ground States and Ionization Energies** y almacena:

```text
ionization_energy_1
ionization_energy_2
ionization_energy_3
...
```

Cada fila conserva:

- etapa de ionización;
- energía en eV;
- incertidumbre;
- calidad evaluada, semiempírica o teórica;
- configuración y nivel cuando se publican;
- fuente y fecha de consulta.

Si NIST no responde, el build conserva los CSV existentes y continúa.

## Radios diferenciados

La nueva pestaña **Radios** distingue:

- Van der Waals;
- covalente;
- covalente por orden de enlace;
- metálico;
- cristalino;
- iónico por carga y coordinación.

El antiguo `atomic_radius` de PubChem se replica como `van_der_waals_radius` con una nota explícita sobre la definición. No se presenta ya como un radio universal.

La visualización utiliza circunferencias concéntricas proporcionales y una leyenda con contexto y fuente.

## Cristalografía y alótropos

La nueva pestaña **Cristal 3D** incluye:

- visor tridimensional giratorio;
- topologías FCC, BCC, HCP, diamante y genérica;
- selector de fase o alótropo;
- estructura cristalina;
- grupo espacial;
- parámetros de red a, b y c;
- ángulos α, β y γ;
- identificador de material;
- procedencia.

El visor es didáctico. La reproducción exacta futura utilizará coordenadas fraccionarias o CIF.

## Fuentes y niveles de cobertura

### Sin credenciales

Durante `npm run build:data` se incorporan:

- derivaciones electrónicas desde los CSV locales;
- estados de oxidación PubChem ya almacenados;
- ionizaciones sucesivas NIST ASD cuando el servicio está disponible;
- anotaciones de radios, estructuras y alótropos desde PubChem PUG View.

### Con Materials Project

Para ampliar estructuras y parámetros de red, crear el secreto del repositorio:

```text
MP_API_KEY
```

El workflow lo pasa al importador. Se consultan únicamente materiales elementales y se almacenan hasta doce fases por elemento con:

- `material_id`;
- fórmula;
- sistema cristalino;
- grupo espacial;
- parámetros de red;
- energía sobre el convex hull;
- estabilidad calculada.

La selección de la fase físicamente representativa debe revisarse: Materials Project contiene estructuras calculadas y fases metaestables, no una única respuesta universal por elemento.

## Comandos

Enriquecimiento completo:

```bash
npm run enrich:advanced
```

Solo derivaciones locales, sin red:

```bash
npm run enrich:advanced:offline
```

Build completo:

```bash
npm run build
```

## Alcance conseguido

- Interfaz y estructura de datos: completadas para los tres bloques.
- Valencia y electrones de valencia: disponibles para los 118 elementos con método indicado cuando existe configuración electrónica.
- Ionizaciones sucesivas: cobertura dependiente de NIST ASD; se descarga de forma masiva en el build.
- Radio Van der Waals: migración explícita desde el dato PubChem existente.
- Otros radios: preparados y poblados cuando PubChem PUG View publica la anotación correspondiente.
- Cristales y alótropos: anotaciones PubChem sin clave; estructuras calculadas y parámetros completos con `MP_API_KEY`.

No se han inventado valores ausentes ni se ha asignado una fase única cuando la fuente ofrece varias alternativas.
