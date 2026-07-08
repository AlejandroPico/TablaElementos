<script lang="ts">
  import type { SpectralLine } from '../lib/atomicTypes';
  import { formatEv, formatNm } from '../lib/wavelengthColor';

  export let lines: SpectralLine[] = [];

  $: levels = Array.from(
    new Set(lines.flatMap((line) => [line.lower_level_ev, line.upper_level_ev]).map((value) => Number(value.toFixed(2))))
  ).sort((a, b) => a - b);

  $: minLevel = levels[0] ?? 0;
  $: maxLevel = levels[levels.length - 1] ?? 1;

  function levelPosition(level: number): number {
    if (maxLevel === minLevel) {
      return 50;
    }

    return 92 - ((level - minLevel) / (maxLevel - minLevel)) * 78;
  }

  function transitionColor(line: SpectralLine): string {
    return line.visible ? line.approximate_color : '#8b95a7';
  }
</script>

<section class="energy-card">
  <div class="section-title-row">
    <div>
      <p class="eyebrow">Modelo educativo</p>
      <h2>Niveles de energía</h2>
    </div>
    <span class="range-pill">{levels.length} niveles</span>
  </div>

  <div class="energy-stage">
    {#each levels as level}
      <div class="energy-level" style={`top:${levelPosition(level)}%;`}>
        <span>{formatEv(level)}</span>
      </div>
    {/each}

    {#each lines.slice(0, 8) as line, index}
      <div
        class="energy-transition"
        style={`
          left:${12 + index * 10}%;
          top:${levelPosition(line.upper_level_ev)}%;
          height:${levelPosition(line.lower_level_ev) - levelPosition(line.upper_level_ev)}%;
          --transition-color:${transitionColor(line)};
        `}
        title={`${line.label}: ${formatNm(line.wavelength_nm)}`}
      >
        <span></span>
      </div>
    {/each}
  </div>

  <p class="energy-note">
    Diagrama simplificado: sirve para visualizar saltos entre niveles, no como sustituto de un diagrama espectroscópico
    completo de términos atómicos.
  </p>
</section>
