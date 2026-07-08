<script lang="ts">
  import * as d3 from 'd3';
  import type { SpectrumMode, SpectralLine } from '../lib/atomicTypes';
  import { VISIBLE_MAX_NM, VISIBLE_MIN_NM, formatNm, wavelengthRegion } from '../lib/wavelengthColor';

  export let lines: SpectralLine[] = [];
  export let mode: SpectrumMode = 'emission';
  export let title = 'Espectro';

  const width = 940;
  const x = d3.scaleLinear().domain([320, 780]).range([0, width]);

  $: ticks = x.ticks(10);
  $: sortedLines = [...lines].sort((a, b) => a.wavelength_nm - b.wavelength_nm);

  function leftPosition(wavelength: number): number {
    return x(wavelength);
  }

  function lineHeight(line: SpectralLine): number {
    return 38 + line.intensity * 82;
  }

  function lineOpacity(line: SpectralLine): number {
    return 0.42 + line.intensity * 0.58;
  }
</script>

<section class="spectrum-card">
  <div class="section-title-row">
    <div>
      <p class="eyebrow">Longitud de onda</p>
      <h2>{title}</h2>
    </div>
    <span class="range-pill">320–780 nm</span>
  </div>

  <div class="region-labels" aria-hidden="true">
    <span>UV cercano</span>
    <span>Visible</span>
    <span>IR cercano</span>
  </div>

  <div class:absorption={mode === 'absorption'} class:emission={mode === 'emission'} class="spectrum-stage">
    <div
      class="visible-window"
      style={`left:${leftPosition(VISIBLE_MIN_NM)}px;width:${leftPosition(VISIBLE_MAX_NM) - leftPosition(VISIBLE_MIN_NM)}px;`}
    ></div>

    {#each ticks as tick}
      <div class="tick" style={`left:${leftPosition(tick)}px;`}>
        <span>{tick}</span>
      </div>
    {/each}

    {#each sortedLines as line}
      <button
        class:outside-visible={!line.visible}
        class="spectral-line"
        style={`
          left:${leftPosition(line.wavelength_nm)}px;
          height:${lineHeight(line)}px;
          opacity:${lineOpacity(line)};
          --line-color:${mode === 'emission' ? line.approximate_color : '#101522'};
        `}
        type="button"
        title={`${line.label} · ${formatNm(line.wavelength_nm)} · ${wavelengthRegion(line.wavelength_nm)}`}
      >
        <span></span>
      </button>
    {/each}
  </div>

  <div class="axis-footer">
    <span>320 nm</span>
    <span>{VISIBLE_MIN_NM} nm</span>
    <span>{VISIBLE_MAX_NM} nm</span>
    <span>780 nm</span>
  </div>
</section>
