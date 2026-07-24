<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ElementDataDomain, SpectralLine } from '../lib/atomicTypes';
  import { getStrongestLines } from '../lib/filters';
  import { formatEv, formatNm } from '../lib/wavelengthColor';

  export let lines: SpectralLine[] = [];
  export let domain: ElementDataDomain | null = null;
  export let selectedLineId = '';

  interface Level {
    energyEv: number;
    energyCm: number;
    configuration: string;
    term: string;
    j: string;
  }

  const dispatch = createEventDispatcher<{ select: SpectralLine }>();
  const CM_PER_EV = 8065.544;

  function numeric(value: unknown): number | null {
    const match = String(value ?? '').replace(/−/g, '-').replace(/,/g, '.').match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    const parsed = match ? Number(match[0]) : Number.NaN;
    return Number.isFinite(parsed) ? parsed : null;
  }

  function lineId(line: SpectralLine): string {
    return [line.species, Number(line.wavelength_nm).toFixed(6), line.transition, line.label].join('|');
  }

  function sample<T>(values: T[], limit: number): T[] {
    if (values.length <= limit) return values;
    return Array.from({ length: limit }, (_, index) => values[Math.round((index / (limit - 1)) * (values.length - 1))]);
  }

  function yFor(energy: number): number {
    return maxEnergy <= 0 ? 255 : 255 - (energy / maxEnergy) * 220;
  }

  $: nistLevels = (domain?.rows ?? []).flatMap((row) => {
    const energyCm = numeric(row['Level (cm-1)']);
    if (energyCm === null) return [];
    return [{
      energyEv: energyCm / CM_PER_EV,
      energyCm,
      configuration: row.Configuration || '—',
      term: row.Term || '—',
      j: row.J || '—',
    }];
  }).sort((a, b) => a.energyEv - b.energyEv);
  $: lineLevels = Array.from(new Set(lines.flatMap((line) => [line.lower_level_ev, line.upper_level_ev]).filter((value) => value >= 0).map((value) => Number(value.toFixed(5)))))
    .sort((a, b) => a - b)
    .map((energyEv) => ({ energyEv, energyCm: energyEv * CM_PER_EV, configuration: 'Derivado de líneas', term: '—', j: '—' }));
  $: allLevels = nistLevels.length ? nistLevels : lineLevels;
  $: displayedLevels = sample(allLevels, 18);
  $: transitions = getStrongestLines(lines.filter((line) => line.upper_level_ev > line.lower_level_ev), 12);
  $: maxEnergy = Math.max(...allLevels.map((level) => level.energyEv), ...transitions.map((line) => line.upper_level_ev), 1);
</script>

<section class="flat-science-section energy-levels-visual">
  <header>
    <div><small>Niveles publicados y transiciones importadas</small><h3>Diagrama de energía</h3></div>
    <span>{allLevels.length.toLocaleString('es-ES')} niveles · {lines.length.toLocaleString('es-ES')} líneas</span>
  </header>

  {#if allLevels.length}
    <svg viewBox="0 0 720 290" role="img" aria-label="Diagrama visual de niveles de energía">
      {#each displayedLevels as level}
        <g class="energy-level-row">
          <line x1="64" x2="390" y1={yFor(level.energyEv)} y2={yFor(level.energyEv)}></line>
          <text x="56" y={yFor(level.energyEv) + 3} text-anchor="end">{level.energyEv.toLocaleString('es-ES', { maximumFractionDigits: 2 })}</text>
          <title>{level.configuration} · {level.term} · J={level.j} · {level.energyCm.toLocaleString('es-ES')} cm⁻¹</title>
        </g>
      {/each}

      {#each transitions as line, index}
        {@const x = 430 + index * 21}
        <g
          class="energy-transition-line"
          class:selected={selectedLineId === lineId(line)}
          role="button"
          tabindex="0"
          aria-label={`Abrir transición ${line.label}`}
          on:click={() => dispatch('select', line)}
          on:keydown={(event) => (event.key === 'Enter' || event.key === ' ') && dispatch('select', line)}
        >
          <line x1={x} x2={x} y1={yFor(line.upper_level_ev)} y2={yFor(line.lower_level_ev)} style={`--transition-color:${line.approximate_color};`}></line>
          <circle cx={x} cy={yFor(line.upper_level_ev)} r="3" style={`--transition-color:${line.approximate_color};`}></circle>
          <title>{line.label} · {formatNm(line.wavelength_nm)} · {formatEv(line.lower_level_ev)} → {formatEv(line.upper_level_ev)}</title>
        </g>
      {/each}

      <text class="energy-axis-label" x="228" y="282" text-anchor="middle">Energía (eV) · se muestran hasta 18 niveles representativos</text>
      <text class="energy-axis-label" x="552" y="282" text-anchor="middle">Transiciones más intensas · seleccionables</text>
    </svg>
  {:else}
    <div class="science-empty-state compact">
      <strong>Sin niveles publicados</strong>
      <p>No se dibuja un diagrama teórico cuando NIST no aporta niveles o transiciones evaluadas.</p>
    </div>
  {/if}
</section>
