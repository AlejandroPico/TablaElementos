# Tabla elementos

Tabla periódica ampliada y estática para explorar elementos químicos, espectros, niveles electrónicos, propiedades físicas, química, isótopos, materiales, usos, historia y futuros bloques de datos científicos.

> Estado: **V1.10 encaje vertical completo**.  
> Tecnología: **Python + Svelte + TypeScript + Vite + D3**.  
> Despliegue: **GitHub Pages mediante GitHub Actions**.  
> Ejecución: **100% estática**, sin servidor externo y sin consultas remotas en tiempo de uso.

## Objetivo del proyecto

**Tabla elementos** nace como una tabla periódica ampliada: una interfaz visual y educativa donde cada elemento químico pueda consultarse como una ficha científica completa.

El proyecto empezó centrado en espectros atómicos, pero ahora queda preparado para crecer hacia una tabla periódica total. La V1.10 corrige el encaje vertical de la vista inicial para que las 9 filas de la tabla, incluidos lantánidos y actínidos, entren completas al cargar la página.

Cada ficha de la tabla muestra de base:

- número atómico;
- símbolo;
- nombre del elemento.

Al hacer zoom empiezan a aparecer detalles adicionales provisionales, como categoría, grupo, periodo y recuento de líneas espectrales disponibles. Esta capa está pensada para ir incorporando más datos conforme avance el dataset.

Al pulsar un elemento se abre una ficha flotante con pestañas:

- longitudes de onda, con interruptor interno de emisión/absorción;
- niveles de energía;
- NIST, con diagnóstico provisional de archivos importados;
- información del elemento;
- tabla técnica de líneas espectrales.

El comparador se gestiona desde la ficha de cada elemento. La tabla principal queda limpia, sin icono `+` en cada celda. El comparador permite quitar elementos individualmente o limpiar toda la selección.

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

La aplicación no hace llamadas externas en tiempo de ejecución. Los datos se versionan dentro del repositorio y el build genera un JSON estático en `public/data/`.

La tabla principal se genera desde:

```txt
data/elements/elements.manifest.csv
```

La estructura ampliada vive en:

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

Coloca los CSV descargados de NIST en:

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

Por defecto copia los archivos y conserva la bandeja de entrada. Para moverlos en vez de copiarlos:

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

## Interacción de la tabla

- Rueda del ratón: zoom sobre el canvas.
- Doble clic: restablece zoom y posición.
- Clic sobre un elemento: abre ficha completa.
- Añadir al comparador: desde la ficha del elemento.
- Quitar del comparador: desde la bandeja inferior.
- Zoom máximo: modo inspección, pensado para que una ficha pueda ocupar casi toda la pantalla.

## Instalación local

Requisitos:

- Node.js 22 o superior recomendado;
- Python 3.12 recomendado.

```bash
npm install
npm run dev
```

## Comandos útiles

Generar datos actuales de la aplicación:

```bash
npm run build:data
```

Inicializar estructura ampliada de elementos:

```bash
npm run init:elements
```

Build de producción:

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

La base pública configurada para Vite es:

```txt
/TablaElementos/
```

## Funcionalidades V1.10

- Encaje vertical corregido para que las 9 filas entren completas al cargar.
- Actínidos visibles completos en la vista inicial.
- Cálculo de celda ajustado para descontar padding, gaps y margen del canvas.
- Padding interno reducido en `periodic-card` y `periodic-grid`.
- Tabla inicial calculada según ancho y alto de pantalla.
- Zoom máximo ampliado a `14`.
- Pasos de zoom potentes con rueda del ratón.
- Modo `zoom-inspect` para inspección profunda de una ficha.
- Tipografía interna ajustada para soportar más datos dentro de cada celda.
- Detalles progresivos: categoría, grupo/periodo y líneas espectrales.
- Canvas interactivo para la tabla periódica.
- Reset de vista con doble clic.
- Margen invisible y `overflow` controlado para evitar microbarras laterales.
- Comparador gestionado desde la ficha del elemento.
- Comparador con eliminación individual y limpieza completa.
- Tabla periódica con los 118 elementos desde `data/elements/elements.manifest.csv`.
- Lantánidos y actínidos visibles en filas separadas.
- Fichas cuadradas con ángulos de 90 grados.
- Pestañas internas: longitudes de onda, niveles de energía, NIST, elemento y datos técnicos.
- Diagnóstico provisional de archivos NIST por elemento.
- Dataset local y estático.

## Licencia

Pendiente de decisión. Para proyectos abiertos y educativos, Apache-2.0 o MIT son opciones razonables.
