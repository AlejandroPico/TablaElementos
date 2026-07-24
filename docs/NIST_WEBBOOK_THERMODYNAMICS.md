# Termodinámica evaluada de NIST Chemistry WebBook

Esta integración amplía la pestaña **Termodinámica** con datos evaluados de NIST Chemistry WebBook, SRD 69.

## Arquitectura

No se crea una base separada. Todos los registros se escriben en:

```text
data/elements/<elemento>/thermodynamics.csv
```

La identidad CAS se resuelve desde el registro oficial del elemento en PubChem PUG View. Después se consulta la página NIST correspondiente mediante su identificador CAS.

## Datos importados

Cuando la página del elemento los contiene, el importador conserva:

- entalpía estándar de formación por fase;
- entropía molar estándar por fase;
- entalpías de fusión, vaporización y sublimación;
- capacidad calorífica tabulada;
- temperaturas de transición;
- coeficientes Shomate `A` a `H`;
- intervalo de temperatura de cada conjunto de coeficientes;
- fase sólida, líquida o gaseosa;
- método, referencia y comentario de NIST.

## Esquema Shomate

Los coeficientes se almacenan como:

```text
shomate_A_solid_1
shomate_B_solid_1
shomate_C_solid_1
shomate_D_solid_1
shomate_E_solid_1
...
shomate_A_liquid_1
...
```

El campo `temperature_k` conserva el intervalo de validez publicado.

La interfaz calcula la capacidad calorífica mediante:

```text
Cp° = A + B·t + C·t² + D·t³ + E/t²

t = T / 1000
```

La curva solo se dibuja cuando están presentes `A`, `B`, `C`, `D` y `E`, y se limita al intervalo NIST. No se extrapola fuera del rango publicado.

## Persistencia conservadora

Una respuesta vacía o un fallo temporal de red no elimina registros NIST ya versionados. Los datos de NIST Chemistry WebBook se sustituyen únicamente cuando la consulta produce un conjunto nuevo de filas válido.

## Ejecución

```bash
npm run enrich:webbook
```

También forma parte de:

```bash
npm run enrich:all
```

La construcción habitual de Pages permanece offline:

```bash
npm run build
```

El workflow manual o automático de actualización científica descarga, valida y confirma los CSV antes de relanzar Pages.

## Limitaciones

- No todos los elementos disponen de una ficha termodinámica condensada en WebBook.
- Las fases y alótropos pueden requerir varios intervalos Shomate.
- Los datos de especies moleculares o iones no se mezclan automáticamente con el elemento neutro.
- La ecuación Shomate describe el intervalo y la fase indicados; no es una ley universal fuera de ellos.
