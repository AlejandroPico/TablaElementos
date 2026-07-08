# Espectros Atómicos

Aplicación científica estática para explorar la huella luminosa de los elementos: líneas de emisión, absorción, longitud de onda, color visible aproximado, niveles de energía y comparación entre elementos.

> Estado: **V1.1 funcional**.  
> Tecnología: **Python + Svelte + TypeScript + Vite + D3**.  
> Despliegue: **GitHub Pages mediante GitHub Actions**.  
> Ejecución: **100% estática**, sin servidor externo y sin consultas remotas en tiempo de uso.

## Objetivo del proyecto

El objetivo de **Espectros Atómicos** es construir una interfaz visual y educativa donde cada elemento químico pueda consultarse como una firma espectral: una serie de líneas que aparecen en posiciones concretas del espectro electromagnético.

La V1.1 reorganiza la interfaz para que la tabla periódica sea el elemento principal de la pantalla. Al pulsar un elemento se abre una ficha flotante con pestañas:

- longitudes de onda, con interruptor interno de emisión/absorción;
- niveles de energía;
- información del elemento;
- tabla técnica de líneas espectrales.

También se mantiene un comparador multielemento con una fila final de fusión espectral, que suma visualmente las líneas de los elementos seleccionados.

## Arquitectura

```txt
Python        → procesa datos locales CSV y genera JSON público
TypeScript    → modelado tipado de elementos, líneas y transiciones
Svelte        → componentes visuales de la interfaz
Vite          → build estático para GitHub Pages
D3            → escalas científicas, ejes y representación espectral
GitHub Actions → build y despliegue automático
```

## Estructura del repositorio

```txt
.
├─ data/
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
│  └─ build_data.py
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

Esta V1.1 no hace llamadas externas. Los datos de muestra están dentro del repositorio en `data/raw/`.

El script `scripts/build_data.py`:

1. lee los CSV locales;
2. agrupa las líneas por elemento;
3. calcula el color visible aproximado de cada longitud de onda;
4. genera un JSON de trabajo en `data/processed/`;
5. copia el JSON final a `public/data/`, que es lo que consume la web.

Más adelante se podrán añadir datos procedentes de fuentes abiertas como NIST Atomic Spectra Database, siempre descargados y versionados localmente en el repositorio.

## Instalación local

Requisitos:

- Node.js 22 o superior recomendado;
- Python 3.12 recomendado.

```bash
npm install
npm run dev
```

## Generar datos

```bash
npm run build:data
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

## Funcionalidades V1.1

- Tabla periódica espectral como vista principal.
- Ficha flotante por elemento.
- Pestañas internas: longitudes de onda, niveles de energía, elemento y datos técnicos.
- Interruptor emisión/absorción dentro de la pestaña de longitudes de onda.
- Comparador multielemento sin límite artificial de 4 elementos.
- Fila Σ de fusión espectral en el comparador.
- Favicon SVG propio.
- Dataset local y estático.

## Licencia

Pendiente de decisión. Para proyectos abiertos y educativos, Apache-2.0 o MIT son opciones razonables.
