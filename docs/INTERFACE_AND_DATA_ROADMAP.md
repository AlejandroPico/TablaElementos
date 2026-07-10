# Hoja de ruta de interfaz y datos

## Visión

Tabla elementos debe funcionar como un escenario científico continuo: vista general de los 118 elementos, zoom progresivo con información adicional y ficha maestra ampliable por dominios.

## Niveles de zoom

1. **Vista general**: número atómico, símbolo y nombre.
2. **Datos intermedios**: categoría, grupo y periodo.
3. **Ficha ampliada**: cobertura disponible de identidad, espectro y fuentes.
4. **Inspección**: resumen del elemento y espacio preparado para propiedades adicionales.

El contenido se representa con HTML/CSS vectorial, por lo que texto, bordes e iconos se vuelven a renderizar durante el zoom y no dependen de una imagen ráster ampliada.

## Ficha maestra

La ficha se organiza inicialmente en:

- Resumen.
- Espectro.
- Niveles.
- Líneas.
- Fuentes / NIST.

La arquitectura deberá admitir después:

- Isótopos.
- Propiedades atómicas.
- Propiedades físicas.
- Química.
- Materiales y cristalografía.
- Termodinámica.
- Geoquímica y abundancia.
- Astrofísica y nucleosíntesis.
- Biología y medicina.
- Industria y economía.
- Medio ambiente y seguridad.
- Historia.
- Compuestos.
- Métodos analíticos.
- Radiación y fotónica.
- Datos computacionales.

## Regla de datos

`data/import/` es exclusivamente una bandeja temporal. Todo archivo aceptado debe validarse, normalizarse y terminar en `data/elements/<elemento>/`.

La interfaz nunca debe representar como científico un archivo que no haya superado validación estructural.
