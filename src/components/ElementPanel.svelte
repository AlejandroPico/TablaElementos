<script lang="ts">
  import type { ElementWithLines } from '../lib/atomicTypes';
  import { formatEv, formatNm, wavelengthRegion } from '../lib/wavelengthColor';
  import { getStrongestLines } from '../lib/filters';

  export let element: ElementWithLines | null = null;

  $: strongest = element ? getStrongestLines(element.lines, 5) : [];
  $: spectrumState = element?.lines.length
    ? 'Disponible'
    : element?.nist?.espectro.present
      ? element.nist.espectro.table_like
        ? 'Sin líneas interpretadas'
        : 'Requiere nueva exportación'
      : 'Pendiente';
  $: levelsState = element?.nist?.niveles.present
    ? element.nist.niveles.table_like
      ? 'Disponible'
      : 'Requiere nueva exportación'
    : 'Pendiente';
</script>

<aside class="element-panel master-summary">
  {#if element}
    <div class="element-hero">
      <div class="element-symbol">
        <span>{element.atomic_number}</span>
        <strong>{element.symbol}</strong>
      </div>
      <div>
        <p class="eyebrow">Ficha maestra · {element.category}</p>
        <h2>{element.name_es}</h2>
        <p>{element.summary}</p>
      </div>
    </div>

    <div class="stat-grid master-stats">
      <div><span>Número atómico</span><strong>{element.atomic_number}</strong></div>
      <div><span>Grupo</span><strong>{element.group}</strong></div>
      <div><span>Periodo</span><strong>{element.period}</strong></div>
      <div><span>Categoría</span><strong>{element.category}</strong></div>
    </div>

    <section class="coverage-section">
      <div class="section-title-row compact">
        <div>
          <p class="eyebrow">Cobertura del elemento</p>
          <h3>Bloques de información</h3>
        </div>
      </div>

      <div class="coverage-grid">
        <article class="available"><span>Identidad</span><strong>Disponible</strong></article>
        <article class:available={element.lines.length > 0} class:problem={spectrumState.includes('exportación')}>
          <span>Espectro</span><strong>{spectrumState}</strong>
        </article>
        <article class:available={levelsState === 'Disponible'} class:problem={levelsState.includes('exportación')}>
          <span>Niveles</span><strong>{levelsState}</strong>
        </article>
        <article><span>Isótopos</span><strong>Pendiente</strong></article>
        <article><span>Propiedades físicas</span><strong>Pendiente</strong></article>
        <article><span>Química y materiales</span><strong>Pendiente</strong></article>
      </div>
    </section>

    <section class="strong-lines-section">
      <div class="section-title-row compact">
        <div>
          <p class="eyebrow">Vista rápida</p>
          <h3>Líneas más intensas</h3>
        </div>
        <span class="range-pill">{element.lines.length} líneas</span>
      </div>

      {#if strongest.length}
        <div class="line-table">
          {#each strongest as line}
            <article>
              <span class="line-swatch" style={`background:${line.approximate_color};`}></span>
              <div>
                <strong>{line.label}</strong>
                <small>{formatNm(line.wavelength_nm)} · {wavelengthRegion(line.wavelength_nm)} · ΔE {formatEv(line.upper_level_ev - line.lower_level_ev)}</small>
              </div>
            </article>
          {/each}
        </div>
      {:else}
        <p class="empty-copy master-empty">
          Aún no hay líneas espectrales científicas interpretables. La ficha conserva su estructura y se completará en cuanto se
          importen CSV tabulares correctos.
        </p>
      {/if}
    </section>
  {:else}
    <div class="empty-panel">
      <h2>Selecciona un elemento</h2>
      <p>La ficha maestra reunirá identidad, propiedades, isótopos, espectros, materiales, seguridad, historia y fuentes.</p>
    </div>
  {/if}
</aside>
