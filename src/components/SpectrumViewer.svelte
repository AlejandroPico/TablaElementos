<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import * as d3 from 'd3';
  import type { SpectrumMode, SpectralLine } from '../lib/atomicTypes';
  import { VISIBLE_MAX_NM, VISIBLE_MIN_NM, formatNm, wavelengthRegion } from '../lib/wavelengthColor';

  export let lines: SpectralLine[] = [];
  export let mode: SpectrumMode = 'emission';
  export let title = 'Espectro';
  export let rangeMode: 'complete' | 'visible' = 'complete';
  export let selectedLineId = '';

  const dispatch = createEventDispatcher<{ select: SpectralLine }>();

  $: sortedLines = [...lines].sort((a, b) => a.wavelength_nm - b.wavelength_nm);
  $: plottedLines = rangeMode === 'visible'
    ? sortedLines.filter((line) => line.wavelength_nm >= VISIBLE_MIN_NM && line.wavelength_nm <= VISIBLE_MAX_NM)
    : sortedLines;
  $: rawMin = plottedLines[0]?.wavelength_nm ?? VISIBLE_MIN_NM;
  $: rawMax = plottedLines.at(-1)?.wavelength_nm ?? VISIBLE_MAX_NM;
  $: padding = rawMax === rawMin ? Math.max(5, rawMin * 0.03) : (rawMax - rawMin) * 0.025;
  $: domainMin = rangeMode === 'visible' ? VISIBLE_MIN_NM : Math.max(0, rawMin - padding);
  $: domainMax = rangeMode === 'visible' ? VISIBLE_MAX_NM : rawMax + padding;
  $: x = d3.scaleLinear().domain([domainMin, domainMax]).range([0, 100]);
  $: ticks = x.ticks(10);
  $: hasLines = plottedLines.length > 0;
  $: visibleStart = Math.max(domainMin, VISIBLE_MIN_NM);
  $: visibleEnd = Math.min(domainMax, VISIBLE_MAX_NM);
  $: visibleWindowShown = visibleEnd > visibleStart;

  function lineId(line: SpectralLine): string {
    return [line.species, Number(line.wavelength_nm).toFixed(6), line.transition, line.label].join('|');
  }

  function leftPosition(wavelength: number): number {
    return x(wavelength);
  }

  function lineHeight(line: SpectralLine): number {
    return 38 + line.intensity * 98;
  }

  function lineOpacity(line: SpectralLine): number {
    return 0.42 + line.intensity * 0.58;
  }
</script>

<section class="spectrum-card">
  <div class="section-title-row compact">
    <div>
      <p class="eyebrow">Longitud de onda</p>
      <h2>{title}</h2>
    </div>
    <span class="range-pill">{hasLines ? `${sortedLines.length} líneas` : 'Sin líneas importadas'}</span>
  </div>

  <div class="region-labels" aria-hidden="true">
    <span>{rangeMode === 'complete' ? `${domainMin.toLocaleString('es-ES', { maximumFractionDigits: 1 })} nm` : 'Violeta'}</span>
    <span>{rangeMode === 'complete' ? 'Rango completo importado' : 'Visible 380–750 nm'}</span>
    <span>{domainMax.toLocaleString('es-ES', { maximumFractionDigits: 1 })} nm</span>
  </div>

  <div class:absorption={mode === 'absorption'} class:emission={mode === 'emission'} class:empty={!hasLines} class="spectrum-stage">
    {#if visibleWindowShown}
      <div
        class="visible-window"
        title="Rango visible aproximado: 380–750 nm. No es una línea espectral."
        style={`left:${leftPosition(visibleStart)}%;width:${leftPosition(visibleEnd) - leftPosition(visibleStart)}%;`}
      ></div>
    {/if}

    {#each ticks as tick}
      <div class="tick" style={`left:${leftPosition(tick)}%;`}>
        <span>{tick}</span>
      </div>
    {/each}

    {#if hasLines}
      {#each plottedLines as line}
        <button
          class:selected={selectedLineId === lineId(line)}
          class:outside-visible={!line.visible}
          class="spectral-line"
          style={`
            left:${leftPosition(line.wavelength_nm)}%;
            height:${lineHeight(line)}px;
            opacity:${lineOpacity(line)};
            --line-color:${mode === 'emission' ? line.approximate_color : '#101522'};
          `}
          type="button"
          title={`${line.label} · ${formatNm(line.wavelength_nm)} · ${wavelengthRegion(line.wavelength_nm)}`}
          aria-label={`Abrir ${line.label}, ${formatNm(line.wavelength_nm)}, en la tabla de líneas`}
          on:click={() => dispatch('select', line)}
        >
          <span></span>
        </button>
      {/each}
    {:else}
      <div class="spectrum-empty">
        <strong>No hay líneas espectrales representables</strong>
        <span>
          {rangeMode === 'visible' && sortedLines.length
            ? 'Este elemento tiene líneas importadas, pero ninguna cae en el intervalo visible. Cambia a «Completo».'
            : 'Cuando exista una tabla de transiciones publicada, aquí aparecerán sus líneas reales.'}
        </span>
      </div>
    {/if}
  </div>

  <div class="axis-footer">
    <span>{domainMin.toLocaleString('es-ES', { maximumFractionDigits: 1 })} nm</span>
    <span>{ticks[Math.floor(ticks.length / 3)]?.toLocaleString('es-ES') ?? ''}</span>
    <span>{ticks[Math.floor((ticks.length * 2) / 3)]?.toLocaleString('es-ES') ?? ''}</span>
    <span>{domainMax.toLocaleString('es-ES', { maximumFractionDigits: 1 })} nm</span>
  </div>
</section>
