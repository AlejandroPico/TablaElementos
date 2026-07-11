<script lang="ts">
  import { afterUpdate, onMount } from 'svelte';
  import type { SpectralLine } from '../lib/atomicTypes';
  import { getStrongestLines } from '../lib/filters';
  import { formatEv, formatNm, wavelengthRegion } from '../lib/wavelengthColor';

  export let lines: SpectralLine[] = [];

  let rootElement: HTMLElement;
  let tableViewport: HTMLDivElement;
  let page = 0;
  let pageSize = 14;
  let resizeObserver: ResizeObserver | null = null;
  let measurementFrame = 0;
  let lastLinesKey = '';

  $: linesKey = `${lines.length}:${lines[0]?.label ?? ''}:${lines.at(-1)?.label ?? ''}`;
  $: if (linesKey !== lastLinesKey) {
    lastLinesKey = linesKey;
    page = 0;
  }
  $: totalPages = Math.max(1, Math.ceil(lines.length / Math.max(1, pageSize)));
  $: if (page >= totalPages) page = totalPages - 1;
  $: visibleLines = lines.slice(page * pageSize, (page + 1) * pageSize);
  $: strongestLines = getStrongestLines(lines, 8);
  $: strongestIds = new Set(strongestLines.map(lineId));

  function lineId(line: SpectralLine): string {
    return [line.species, Number(line.wavelength_nm).toFixed(6), line.transition, line.label].join('|');
  }

  function energyJump(line: SpectralLine): number {
    return line.upper_level_ev - line.lower_level_ev;
  }

  function scheduleMeasurement(): void {
    cancelAnimationFrame(measurementFrame);
    measurementFrame = requestAnimationFrame(measurePageSize);
  }

  function measurePageSize(): void {
    if (!tableViewport) return;
    const head = tableViewport.querySelector('thead')?.getBoundingClientRect().height ?? 34;
    const row = tableViewport.querySelector('tbody tr')?.getBoundingClientRect().height ?? 34;
    const available = Math.max(120, tableViewport.clientHeight - head - 2);
    const next = Math.max(4, Math.min(50, Math.floor(available / Math.max(28, row))));
    if (next !== pageSize) pageSize = next;
  }

  afterUpdate(scheduleMeasurement);

  onMount(() => {
    resizeObserver = new ResizeObserver(scheduleMeasurement);
    resizeObserver.observe(rootElement);
    resizeObserver.observe(tableViewport);
    scheduleMeasurement();
    return () => {
      cancelAnimationFrame(measurementFrame);
      resizeObserver?.disconnect();
    };
  });
</script>

<section bind:this={rootElement} class="lines-data-view" aria-label="Líneas espectrales NIST">
  <header class="inline-domain-header">
    <div><h3>Líneas espectrales NIST</h3><span>—</span><small>{lines.length.toLocaleString('es-ES')} registros</small></div>
  </header>

  {#if strongestLines.length}
    <div class="featured-lines" aria-label="Líneas espectrales más intensas">
      <p>Líneas destacadas</p>
      <div>
        {#each strongestLines as line}
          <span class="featured-line">
            <i style={`--line-color:${line.approximate_color};`}></i>
            <b>{formatNm(line.wavelength_nm)}</b>
            <small>{line.label}</small>
          </span>
        {/each}
      </div>
    </div>
  {/if}

  <div bind:this={tableViewport} class="technical-table modal-table paginated-table lines-table-viewport">
    <table>
      <thead>
        <tr><th>Línea</th><th>Especie</th><th>λ</th><th>Región</th><th>Intensidad</th><th>Nivel inferior</th><th>Nivel superior</th><th>ΔE</th><th>Transición</th></tr>
      </thead>
      <tbody>
        {#each visibleLines as line}
          <tr class:featured={strongestIds.has(lineId(line))}>
            <td>{line.label}</td><td>{line.species}</td><td>{formatNm(line.wavelength_nm)}</td>
            <td>{wavelengthRegion(line.wavelength_nm)}</td><td>{line.intensity.toFixed(2)}</td>
            <td>{formatEv(line.lower_level_ev)}</td><td>{formatEv(line.upper_level_ev)}</td>
            <td>{formatEv(energyJump(line))}</td><td>{line.transition}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <footer class="adaptive-pagination" aria-label="Paginación de líneas espectrales">
    <button type="button" disabled={page === 0} on:click={() => (page -= 1)} aria-label="Página anterior" title="Página anterior">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 5-7 7 7 7"></path></svg>
    </button>
    <span>{page + 1} / {totalPages}</span>
    <button type="button" disabled={page >= totalPages - 1} on:click={() => (page += 1)} aria-label="Página siguiente" title="Página siguiente">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"></path></svg>
    </button>
  </footer>
</section>
