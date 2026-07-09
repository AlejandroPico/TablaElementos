# `data/import/`

Zona temporal de entrada para archivos descargados manualmente antes de colocarlos en su carpeta definitiva por elemento.

## NIST ASD

Los CSV descargados desde NIST Atomic Spectra Database pueden copiarse primero en:

```txt
data/import/nist/
```

Nombres esperados actualmente:

```txt
001_H_espectro.csv
001_H_niveles.csv
002_He_espectro.csv
002_He_niveles.csv
...
118_Og_espectro.csv
118_Og_niveles.csv
```

Después, ejecutar:

```bash
npm run import:nist
```

El script localizará la carpeta correcta de cada elemento usando `data/elements/elements.manifest.csv` y copiará los archivos a rutas como:

```txt
data/elements/001-H-hydrogen/001_H_espectro.csv
data/elements/001-H-hydrogen/001_H_niveles.csv
```

## Reglas

- Esta carpeta es solo una bandeja de entrada.
- Los archivos originales se conservan salvo que se use explícitamente una opción de movimiento.
- Los datos definitivos deben quedar en `data/elements/<elemento>/`.
- Añadir las fuentes utilizadas a `sources.csv` cuando se normalicen los datos.
