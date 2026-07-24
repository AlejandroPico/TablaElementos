# Importación XPS y Auger

El NIST X-ray Photoelectron Spectroscopy Database ofrece consulta y exportación, pero no se utiliza aquí una API masiva no documentada. Las exportaciones autorizadas pueden depositarse en esta carpeta y serán distribuidas automáticamente a `radiation_interaction.csv` dentro de la carpeta de cada elemento.

## Formato CSV recomendado

```csv
symbol,line_type,binding_energy_ev,kinetic_energy_ev,compound,chemical_state,source,source_url,notes
Fe,Fe 2p3/2,710.8,,Fe2O3,Fe(III),NIST XPS Database,https://srdata.nist.gov/xps/,Ejemplo de estructura; sustituir por una exportación real.
Cu,Cu L3M45M45,,918.6,Cu,metal,NIST XPS Database,https://srdata.nist.gov/xps/,Línea Auger.
```

## Campos

- `symbol`: símbolo químico exacto del elemento.
- `line_type`: orbital XPS o denominación de la línea Auger.
- `binding_energy_ev`: energía de enlace para XPS.
- `kinetic_energy_ev`: energía cinética para Auger.
- `compound`: fórmula o sustancia medida.
- `chemical_state`: estado químico, oxidación o entorno local.
- `source`: nombre de la fuente.
- `source_url`: registro o consulta de procedencia.
- `notes`: condiciones, incertidumbre, calibración o comentarios.

El importador también acepta `element`, `transition`, `orbital`, `energy_ev` y `value` como nombres alternativos.

## Regla científica

Una energía XPS no es una constante única del elemento. Cambia con el compuesto, el estado de oxidación, la coordinación, la referencia de calibración y el instrumento. Por este motivo, nunca debe guardarse solamente como «energía XPS del hierro» sin especificar el entorno químico.

## Ejecución

```bash
npm run enrich:science2
npm run build:data
```

Los datos terminan en:

```text
data/elements/<elemento>/radiation_interaction.csv
```
