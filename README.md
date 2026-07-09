# Espectros Atómicos

Aplicación científica estática para explorar la huella luminosa de los elementos: líneas de emisión, absorción, longitud de onda, color visible aproximado, niveles de energía y comparación entre elementos.

> Estado: **V1.6 estructural**.  
> Tecnología: **Python + Svelte + TypeScript + Vite + D3**.  
> Despliegue: **GitHub Pages mediante GitHub Actions**.  
> Ejecución: **100% estática**, sin servidor externo y sin consultas remotas en tiempo de uso.

## Objetivo del proyecto

El objetivo de **Espectros Atómicos** evoluciona hacia una tabla periódica ampliada: una interfaz visual y educativa donde cada elemento químico pueda consultarse como una ficha científica completa.

La V1.6 carga ya los 118 elementos desde el manifiesto maestro, mantiene la visualización espectral de muestra como respaldo y añade un diagnóstico NIST provisional dentro de cada ficha. El generador analiza si los CSV de `data/import/nist/` son tablas legibles o si parecen exportaciones no tabulares, HTML o JavaScript guardado como CSV.

Cada ficha muestra:

- número atómico;
- símbolo;
- nombre del elemento.

Al pulsar un elemento se abre una ficha flotante con pestañas:

- longitudes de onda, con interruptor interno de emisión/absorción;
- niveles de energía;
- NIST, con diagnóstico provisional de archivos importados;
- información del elemento;
- tabla técnica de líneas espectrales.

El comparador aparece solo cuando se añaden elementos con el botón `+`. Se muestra como una bandeja inferior que ocupa parte de la pantalla sin superponerse a la tabla.

## Arquitectura

```txt
Python         → procesa datos locales CSV y genera JSON público
TypeScript     → modelado tipado de elementos, líneas, transiciones y estado NIST
Svelte         → componentes visuales de la interfaz
Vite           → build estático para GitHub Pages
D3             → escalas científicas, ejes y representación espectral
GitHub Actions → build y despliegue automático
```

## Estructura del repositorio

```txt
.
├─ data/
│  ├─ elements/
│  │  ├─ README.md
│  │  └─ elements.manifest.csv
│  ├─ import/
│  │  ├─ README.md
│  │  └─ nist/
│  │     └─ .gitkeep
│  ├─ raw/
│  │  ├─ elements.csv
│  │  └─ sample-lines.csv
│  ├─ processed/
│  │  └─ spectra.sample.json
│  └─ schema/
│     └─ spectral-line.schema.json
├─ public/
│  ├─ data/
│  │  └─ spectra.sample.json
│  └─ favicon.svg
├─ scripts/
│  ├─ build_data.py
│  ├─ import_nist_exports.py
│  └─ init_elements_structure.py
├─ src/
│  ├─ app/
│  ├─ components/
│  ├─ lib/
│  ├─ styles/
│  │  ├─ expanded.css
│  │  └─ global.css
│  └─ main.ts
├─ .github/
│  └─ workflows/
│     └─ deploy.yml
├─ package.json
├─ vite.config.ts
└─ README.md
```

## Datos

Esta V1.6 no hace llamadas externas. Los datos de muestra antiguos siguen dentro de `data/raw/` por compatibilidad visual, pero la tabla principal se genera desde:

```txt
data/elements/elements.manifest.csv
```

La nueva estructura de datos vive en:

```txt
data/elements/
```

Contiene:

- `elements.manifest.csv`: manifiesto maestro con los 118 elementos y la carpeta prevista para cada uno;
- `README.md`: reglas de estructura, nombres de CSVs y dominios científicos previstos;
- `scripts/init_elements_structure.py`: generador local de las 118 carpetas de elementos y sus plantillas CSV.

Para generar localmente todas las carpetas:

```bash
npm run init:elements
```

Git no conserva carpetas vacías, por eso las subcarpetas se generan mediante script antes de empezar a cargar datos reales.

## Importar CSVs de NIST ASD

Coloca todos los CSV descargados de NIST en:

```txt
data/import/nist/
```

Nombres esperados:

```txt
001_H_espectro.csv
001_H_niveles.csv
002_He_espectro.csv
002_He_niveles.csv
...
118_Og_espectro.csv
118_Og_niveles.csv
```

Primero genera las carpetas si no existen:

```bash
npm run init:elements
```

Luego prueba la importación sin copiar nada:

```bash
npm run import:nist:dry
```

Si la salida es correcta, ejecuta la importación real:

```bash
npm run import:nist
```

El script copiará, por ejemplo:

```txt
data/import/nist/001_H_espectro.csv
```

a:

```txt
data/elements/001-H-hydrogen/001_H_espectro.csv
```

Por defecto copia los archivos y conserva la bandeja de entrada. Para moverlos en vez de copiarlos, se puede ejecutar directamente:

```bash
python scripts/import_nist_exports.py --move
```

## Diagnóstico NIST provisional

`scripts/build_data.py` analiza los archivos NIST en cada build y añade un bloque `nist_by_element` al JSON público. La pestaña **NIST** de cada ficha muestra:

- si existe el archivo de espectro;
- si existe el archivo de niveles;
- columnas detectadas;
- número de filas;
- ruta del archivo;
- advertencia si el CSV parece HTML, JavaScript o una sola columna no tabular.

Si los CSV no son tablas limpias, el build no falla: lo marca como diagnóstico para poder corregir la exportación.

## Instalación local

Requisitos:

- Node.js 22 o superior recomendado;
- Python 3.12 recomendado.

```bash
npm install
npm run dev
```

## Generar datos actuales de la aplicación

```bash
npm run build:data
```

## Inicializar estructura ampliada de elementos

```bash
npm run init:elements
```

## Build de producción

```bash
npm run build
```

El resultado queda en:

```txt
dist/
```

## Publicación en GitHub Pages

El workflow `.github/workflows/deploy.yml` publica automáticamente la carpeta `dist` cuando se hace push a `main`.

En GitHub, revisa:

```txt
Settings → Pages → Build and deployment → Source → GitHub Actions
```

## Funcionalidades V1.6

- Tabla periódica con los 118 elementos desde `data/elements/elements.manifest.csv`.
- Lantánidos y actínidos visibles en filas separadas.
- Pantalla principal sin cabeceras, subtítulos ni textos guía.
- Tabla periódica como elemento visual dominante.
- Contenedor visual de la tabla eliminado: solo se ven las fichas.
- Fichas cuadradas con ángulos de 90 grados.
- Celdas con número atómico, símbolo y nombre.
- Coloración por categoría química.
- Botón `+` por elemento para activar el comparador.
- Ficha flotante por elemento al pulsar la celda.
- Pestañas internas: longitudes de onda, niveles de energía, NIST, elemento y datos técnicos.
- Diagnóstico provisional de archivos NIST por elemento.
- Interruptor emisión/absorción dentro de la pestaña de longitudes de onda.
- Comparador inferior tipo bandeja deslizable.
- Fila Σ de fusión espectral en el comparador.
- Nueva estructura `data/elements/` para 118 elementos.
- Bandeja `data/import/nist/` para subir CSVs planos de NIST.
- Importador `npm run import:nist` para repartir espectros y niveles por elemento.
- Dataset local y estático.

## Licencia

Pendiente de decisión. Para proyectos abiertos y educativos, Apache-2.0 o MIT son opciones razonables.
