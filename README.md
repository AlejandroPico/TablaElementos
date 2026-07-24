# TablaElementos

Tabla periódica científica, interactiva y completamente estática para explorar los 118 elementos químicos mediante zoom progresivo, filtros combinables, estructura electrónica, radios diferenciados, cristalografía 3D, física nuclear, termodinámica, espectros, rayos X, atenuación, neutrones y comparación entre elementos.

> **Versión:** `0.4.0`  
> **Tecnologías:** Svelte 5 · TypeScript · Vite · D3 · Python  
> **Despliegue:** GitHub Pages mediante GitHub Actions  
> **Ejecución:** sin backend y sin consultas científicas externas desde el navegador

## Demostración

**https://alejandropico.github.io/TablaElementos/**

## Objetivo

TablaElementos busca convertir la tabla periódica en un espacio de exploración científica, no solamente en una cuadrícula de símbolos.

La posición periódica es el punto de partida. Cada casilla puede crecer progresivamente con el zoom y abrirse después como una ficha documental con información atómica, química, nuclear, espectroscópica, cristalográfica, termodinámica y radiológica.

El proyecto mantiene una regla estructural estricta: **todos los datos de un elemento se almacenan dentro de su propia carpeta**.

```text
data/elements/026-Fe-iron/
data/elements/092-U-uranium/
...
```

## Funcionalidades principales

### Tabla periódica completa

- 118 elementos.
- Distribución corta de 18 columnas.
- Distribución larga de 32 columnas.
- Incorporación animada de lantánidos y actínidos en el cuerpo principal.
- Animación inversa en dos fases.
- Casillas-resumen `57 - 71` y `89 - 103`.
- Resaltado completo de la serie al situarse sobre su resumen.
- Geometría cuadrada y lenguaje visual uniforme.

### Zoom científico progresivo

La rueda del ratón amplía la tabla alrededor del cursor. El contenido de las casillas aparece por niveles:

1. **Vista general:** número atómico, símbolo y nombre.
2. **Datos intermedios:** masa atómica y estado estándar.
3. **Ficha ampliada:** configuración electrónica, electronegatividad, radio y densidad.
4. **Inspección:** ionización, afinidad, temperaturas, categoría y posición periódica.

El motor utiliza interpolación GPU, escalones de renderizado y repintado al finalizar el gesto para mantener nitidez sin desplazar la geometría de las fichas.

### Navegación

- Rueda: ampliar o reducir.
- Arrastre: desplazar el escenario.
- Clic limpio: abrir la ficha del elemento.
- Doble clic sobre el fondo: restablecer el encuadre.
- Clic sobre el porcentaje: restablecer y encajar.
- Cambio animado entre tabla corta y larga.

## Filtros científicos

El botón de embudo abre un panel independiente sin ocupar espacio permanente en la mesa.

Las opciones del mismo grupo se combinan mediante **O** y los grupos diferentes mediante **Y**.

Filtros disponibles:

- categoría química;
- bloque electrónico;
- metal, metaloide o no metal;
- estado estándar;
- grupo y periodo;
- estados de oxidación;
- número atómico;
- masa atómica;
- electronegatividad;
- primera ionización;
- afinidad electrónica;
- radio de Van der Waals;
- punto de fusión;
- punto de ebullición;
- densidad;
- calor específico;
- año de descubrimiento;
- líneas espectrales;
- isótopos;
- niveles NIST;
- dominios científicos disponibles.

Los rangos numéricos incluyen doble tirador, edición manual, unidad normalizada, inclusión opcional de elementos sin dato y restablecimiento individual.

## Ficha maestra

Al pulsar una casilla se abre una ficha con pestañas independientes:

- **Resumen**
- **Átomo 3D**
- **Electrones**
- **Radios**
- **Cristal 3D**
- **Nuclear**
- **Termodinámica**
- **Radiación**
- **Propiedades**
- **Isótopos**
- **Espectro**
- **Líneas**
- **Niveles**
- **Química**
- **Contexto**
- **Fuentes**

Los dominios extensos se cargan de forma diferida mediante un JSON independiente por elemento.

## Átomo 3D

Representación didáctica animada con:

- protones;
- neutrones estimados o derivados del isótopo disponible;
- electrones;
- distribución por capas;
- núcleo y trayectorias con profundidad;
- pausa y reanudación.

La visualización no representa órbitas cuánticas literales.

## Estructura electrónica y valencia

La pestaña **Electrones** diferencia:

- configuración completa;
- configuración abreviada;
- configuración de valencia;
- electrones de la capa exterior;
- electrones de valencia;
- valencias comunes;
- estados de oxidación;
- energías de ionización sucesivas.

Incluye una gráfica de ionizaciones sucesivas para visualizar los saltos asociados al cambio de capa electrónica.

Los valores derivados se etiquetan como derivados y no sustituyen mediciones experimentales.

## Radios atómicos diferenciados

La pestaña **Radios** evita presentar un único “radio atómico” universal.

Puede representar:

- radio de Van der Waals;
- radio covalente;
- radio metálico;
- radio cristalino;
- radios iónicos por carga y coordinación.

La visualización utiliza círculos concéntricos proporcionales y conserva la definición y fuente de cada magnitud.

## Cristalografía y alótropos

La pestaña **Cristal 3D** incorpora:

- visor tridimensional de celda unidad;
- selector de fase o alótropo;
- estructura y sistema cristalino;
- grupo espacial;
- parámetros `a`, `b`, `c`;
- ángulos `α`, `β`, `γ`;
- estabilidad y procedencia cuando están disponibles.

La integración opcional con Materials Project requiere `MP_API_KEY`.

## Física nuclear avanzada

La pestaña **Nuclear** utiliza los CSV de IAEA LiveChart y presenta:

- mapa de número de neutrones frente a vida media;
- escala logarítmica;
- color por modo principal de desintegración;
- isótopos estables;
- abundancias naturales;
- selección interactiva de nucleído;
- protones, neutrones y número másico;
- espín y paridad;
- dipolo magnético nuclear;
- cuadrupolo eléctrico;
- energía de enlace;
- energías Q;
- modo de desintegración.

La ausencia de vida media no se interpreta como estabilidad. Solo se marca como estable un nucleído identificado expresamente como `STABLE` por la fuente.

## Termodinámica y fases

La pestaña **Termodinámica** puede mostrar:

- estado estándar;
- densidad;
- punto de fusión;
- punto de ebullición;
- entalpía de fusión;
- entalpía de vaporización;
- entalpía de sublimación;
- capacidad calorífica;
- entropía molar;
- punto triple;
- punto crítico;
- presión de vapor.

Visualizaciones:

- eje de transiciones de fase;
- curva `Cp(T)` cuando existen varios puntos;
- curva de presión de vapor en escala logarítmica;
- listado de registros con temperatura, presión, fase y fuente.

No se genera una curva a partir de un único dato.

## Espectros ópticos, líneas y niveles

- Espectro de emisión.
- Espectro de absorción.
- Regiones ultravioleta, visible e infrarroja.
- Líneas más intensas destacadas.
- Tabla técnica paginada.
- Niveles de energía NIST.
- Diagnóstico de integridad de CSV.
- Recuperación de respaldo cuando un CSV NIST está vacío.

### Caso del hierro

El CSV canónico de Fe I estaba vacío. La construcción incorpora ahora dos protecciones:

1. líneas educativas locales para que la ficha nunca quede sin espectro;
2. comando focalizado para volver a descargar Fe I desde NIST ASD.

```bash
npm run repair:iron-spectrum
```

Las líneas de respaldo se identifican como tales y no se presentan como una descarga NIST completa.

## Rayos X, atenuación, XPS y neutrones

La pestaña **Radiación** contiene cuatro modos.

### Rayos X

- transiciones características K, L, M y N;
- energía teórica;
- energía experimental cuando existe;
- espectro de líneas en escala energética logarítmica.

### Atenuación

- coeficiente másico de atenuación `μ/ρ`;
- coeficiente másico de absorción de energía `μen/ρ`;
- energía del fotón;
- bordes de absorción;
- gráfica logarítmica.

### XPS y Auger

- energías de enlace XPS;
- energías cinéticas Auger;
- orbital o transición;
- compuesto;
- estado químico;
- procedencia.

XPS no se reduce a una constante del elemento: cambia con el compuesto, el estado de oxidación, la coordinación y la calibración.

### Neutrones

- longitud coherente de dispersión;
- sección coherente;
- sección incoherente;
- sección total;
- sección de absorción;
- datos naturales e isotópicos;
- abundancia cuando la fuente la publica.

Los valores actuales corresponden a neutrones evaluados a 2200 m/s y no sustituyen curvas dependientes de energía.

## Isótopos y tablas técnicas

Las tablas de isótopos, líneas y niveles:

- ocupan el espacio útil disponible;
- calculan las filas visibles;
- utilizan paginación;
- conservan desplazamiento horizontal;
- mantienen la cabecera visible.

## Comparador total

La selección de elementos no tiene un límite impuesto por la aplicación.

Ámbitos disponibles:

- global;
- resumen;
- átomo;
- electrones;
- radios;
- cristal;
- nuclear;
- termodinámica;
- radiación;
- propiedades;
- isótopos;
- espectro;
- líneas;
- niveles;
- química;
- contexto;
- fuentes.

El botón de comparación abre inicialmente el ámbito de la pestaña activa.

## Temas

- claro;
- oscuro;
- automático;
- indicador dinámico del modo activo;
- paleta científica desaturada;
- contraste adaptado a las fichas y visualizaciones.

## Guía científica

El icono de información abre una guía de 30 capítulos con índice lateral, explicaciones, tablas conceptuales y fuentes de ampliación.

`Alt + clic` abre el diagnóstico interno de elementos, líneas, CSV, distribución, tema y filtros.

## Fuentes científicas

El dataset consolida principalmente:

- **PubChem PUG REST y PUG View:** identidad, propiedades generales, radios, anotaciones y termodinámica disponible.
- **CIAAW:** pesos atómicos estándar.
- **NIST Atomic Spectra Database:** líneas, niveles, estados fundamentales e ionizaciones.
- **IAEA LiveChart:** nucleídos y propiedades nucleares.
- **NIST X-Ray Transition Energies:** transiciones características.
- **NIST X-Ray Mass Attenuation Coefficients:** `μ/ρ` y `μen/ρ`.
- **NIST NCNR:** dispersión y absorción neutrónica.
- **NIST XPS Database:** exportaciones XPS y Auger.
- **Materials Project:** fases y cristalografía calculada cuando existe clave.

Cada valor debe interpretarse junto con su unidad, condiciones, incertidumbre, fecha y fuente.

## Arquitectura de datos

```text
Python         → descarga, normaliza y genera datasets
TypeScript     → tipos, cámara, filtros, comparación e interacción
Svelte         → interfaz y paneles científicos
D3 / SVG       → escalas y visualizaciones
Vite           → aplicación estática
GitHub Actions → actualización de datos, validación y Pages
```

La aplicación no necesita servidor ni base de datos remota durante el uso.

## Estructura por elemento

Convención:

```text
NNN-Symbol-english-name
```

Ejemplos:

```text
001-H-hydrogen
026-Fe-iron
092-U-uranium
118-Og-oganesson
```

Archivos admitidos:

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

Los importadores pueden utilizar `data/import/` como zona temporal, pero los datos consumidos por la aplicación deben terminar en `data/elements/<elemento>/`.

## Carga diferida

El índice principal contiene solamente los datos necesarios para dibujar, filtrar y localizar cada elemento.

Los dominios completos se generan como:

```text
public/data/elements/H.json
public/data/elements/Fe.json
public/data/elements/U.json
...
```

El navegador descarga únicamente el JSON de la ficha abierta.

## Instalación

Requisitos recomendados:

- Node.js 24;
- Python 3.13.

```bash
git clone https://github.com/AlejandroPico/TablaElementos.git
cd TablaElementos
npm install
npm run dev
```

## Comandos principales

### Validación

```bash
npm run check
```

### Build reproducible y offline

```bash
npm run build
```

El build no consulta fuentes externas. Utiliza los CSV versionados y genera `dist/`.

### Regenerar datasets locales

```bash
npm run build:data
```

### Actualizar ciencia avanzada

```bash
npm run enrich:advanced
npm run enrich:science2
npm run enrich:all
```

### Reparar Fe I

```bash
npm run repair:iron-spectrum
```

### Reparación óptica masiva

```bash
npm run repair:spectra:all
```

La reparación masiva es opcional porque puede generar miles de líneas por elemento.

## GitHub Actions

### Despliegue

```text
.github/workflows/deploy-pages.yml
```

Valida, construye offline y publica GitHub Pages.

### Actualización científica

```text
.github/workflows/refresh-scientific-data.yml
```

Workflow manual que:

1. descarga datos oficiales;
2. actualiza los CSV dentro de las 118 carpetas;
3. repara el espectro del hierro;
4. regenera datasets;
5. ejecuta `svelte-check`;
6. valida el build;
7. confirma los cambios científicos;
8. activa después el despliegue normal.

La reparación masiva de todos los espectros puede habilitarse como opción explícita.

## Documentación científica

- `docs/PROPERTY_COVERAGE.md`
- `docs/ADVANCED_SCIENCE_PHASE_1.md`
- `docs/ADVANCED_SCIENCE_PHASE_2.md`
- `data/import/xps/README.md`
- `data/elements/README.md`

## Principios de calidad

1. No inventar valores ausentes.
2. No confundir cero con falta de dato.
3. Distinguir medición, cálculo, estimación y derivación.
4. Conservar temperatura, presión, fase, isótopo, carga y estado químico.
5. Mantener fuente y fecha.
6. No mezclar radios definidos mediante criterios distintos.
7. No presentar XPS sin entorno químico.
8. No presentar una propiedad de un isótopo como universal del elemento.
9. No dibujar curvas cuando la fuente solo proporciona un punto.
10. Mantener todos los datos del elemento dentro de su carpeta canónica.

## Estado

La infraestructura y las visualizaciones de las fases científicas 1 y 2 están implementadas. La cobertura efectiva de cada propiedad depende de la disponibilidad y calidad de las fuentes oficiales; una celda vacía significa que el dato todavía no está integrado, no que su valor sea cero.
