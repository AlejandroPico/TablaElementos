# Espectros Atómicos

Aplicación científica estática para explorar la huella luminosa de los elementos: líneas de emisión, absorción, longitud de onda, color visible aproximado, niveles de energía y comparación entre elementos.

> Estado: **V1.4 estructural**.  
> Tecnología: **Python + Svelte + TypeScript + Vite + D3**.  
> Despliegue: **GitHub Pages mediante GitHub Actions**.  
> Ejecución: **100% estática**, sin servidor externo y sin consultas remotas en tiempo de uso.

## Objetivo del proyecto

El objetivo de **Espectros Atómicos** evoluciona hacia una tabla periódica ampliada: una interfaz visual y educativa donde cada elemento químico pueda consultarse como una ficha científica completa.

La V1.3 ajustó la estética de la tabla principal hacia un sistema de fichas cuadradas, anguladas y coloreadas por categoría. La V1.4 añade la primera estructura de datos para convertir el proyecto en una tabla periódica total, preparada para almacenar por elemento espectros, isótopos, propiedades físicas, química, materiales, historia, industria y otros dominios.

Cada ficha muestra:

- número atómico;
- símbolo;
- nombre del elemento.

Al pulsar un elemento se abre una ficha flotante con pestañas:

- longitudes de onda, con interruptor interno de emisión/absorción;
- niveles de energía;
- información del elemento;
- tabla técnica de líneas espectrales.

El comparador aparece solo cuando se añaden elementos con el botón `+`. Se muestra como una bandeja inferior que ocupa parte de la pantalla sin superponerse a la tabla.

## Arquitectura

```txt
Python         → procesa datos locales CSV y genera JSON público
TypeScript     → modelado tipado de elementos, líneas y transiciones
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
│  └─ init_elements_structure.py
├─ src/
│  ├─ app/
│  ├─ components/
│  ├─ lib/
│  ├─ styles/
│  └─ main.ts
├─ .github/
│  └─ workflows/
│     └─ deploy.yml
├─ package.json
├─ vite.config.ts
└─ README.md
```

## Datos

Esta V1.4 no hace llamadas externas. Los datos de muestra antiguos siguen dentro de `data/raw/` por compatibilidad con la V1 actual.

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

El script actual `scripts/build_data.py` todavía alimenta la web desde `data/raw/` y `public/data/`. La migración a `data/elements/` se hará en una fase posterior para no romper el despliegue existente.

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

## Funcionalidades V1.4

- Pantalla principal sin cabeceras, subtítulos ni textos guía.
- Tabla periódica como elemento visual dominante.
- Contenedor visual de la tabla eliminado: solo se ven las fichas.
- Fichas cuadradas con ángulos de 90 grados.
- Celdas con número atómico, símbolo y nombre.
- Coloración por categoría química.
- Botón `+` por elemento para activar el comparador.
- Ficha flotante por elemento al pulsar la celda.
- Pestañas internas: longitudes de onda, niveles de energía, elemento y datos técnicos.
- Interruptor emisión/absorción dentro de la pestaña de longitudes de onda.
- Comparador inferior tipo bandeja deslizable.
- Fila Σ de fusión espectral en el comparador.
- Nueva estructura `data/elements/` para 118 elementos.
- Manifiesto maestro `data/elements/elements.manifest.csv`.
- Generador `npm run init:elements` para crear carpetas y CSVs por elemento.
- Dataset local y estático.

## Licencia

Pendiente de decisión. Para proyectos abiertos y educativos, Apache-2.0 o MIT son opciones razonables.
