<script lang="ts">
  import type { DataRow, ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;
  export let loading = false;

  interface Nuclide {
    row: DataRow;
    z: number;
    n: number;
    a: number;
    label: string;
    stable: boolean;
    halfLifeSeconds: number | null;
    halfLifeText: string;
    abundance: number | null;
    decay: string;
    spin: string;
    magneticDipole: string;
    electricQuadrupole: string;
    binding: number | null;
    qAlpha: number | null;
    qEc: number | null;
  }

  let selectedLabel = '';
  let lastSymbol = '';

  function num(value: unknown): number | null {
    const text = String(value ?? '').replace(/−/g, '-').replace(/,/g, '.');
    const match = text.match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    if (!match) return null;
    const parsed = Number(match[0]);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function buildNuclides(sourceRows: DataRow[], currentElement: ElementWithLines | null): Nuclide[] {
    return sourceRows.flatMap((row) => {
      const z = num(row.z) ?? currentElement?.atomic_number ?? 0;
      const n = num(row.n);
      if (n === null) return [];
      const a = z + n;
      const halfLifeText = String(row.half_life ?? '').trim();
      const stable = halfLifeText.toUpperCase() === 'STABLE';
      const halfLifeSeconds = stable ? null : num(row.half_life_sec);
      const decay = String(row.decay_1 ?? '').trim() || (stable ? 'ESTABLE' : 'SIN DATO');
      return [{
        row,
        z,
        n,
        a,
        label: `${currentElement?.symbol ?? row.symbol ?? ''}-${a}`,
        stable,
        halfLifeSeconds,
        halfLifeText: stable ? 'Estable' : [halfLifeText, row.unit_hl].filter(Boolean).join(' ') || 'Sin dato',
        abundance: num(row.abundance),
        decay,
        spin: String(row.jp ?? '').trim() || '—',
        magneticDipole: String(row.magnetic_dipole ?? '').trim() || '—',
        electricQuadrupole: String(row.electric_quadrupole ?? '').trim() || '—',
        binding: num(row.binding),
        qAlpha: num(row.qa),
        qEc: num(row.qec),
      }];
    }).sort((a, b) => a.n - b.n);
  }

  function decayColor(decay: string): string {
    const normalized = decay.toUpperCase();
    if (normalized.includes('ESTABLE')) return '#6fc79a';
    if (normalized.includes('ALPHA') || normalized === 'A') return '#e0a865';
    if (normalized.includes('B-')) return '#79c5d9';
    if (normalized.includes('B+') || normalized.includes('EC')) return '#d87988';
    if (normalized.includes('SF')) return '#c58bd8';
    if (normalized.includes('N')) return '#8fc980';
    if (normalized.includes('P')) return '#a6a7dc';
    return '#8b95a7';
  }

  function logLife(nuclide: Nuclide): number {
    if (nuclide.stable) return 25;
    if (!nuclide.halfLifeSeconds || nuclide.halfLifeSeconds <= 0) return -6;
    return Math.max(-6, Math.min(25, Math.log10(nuclide.halfLifeSeconds)));
  }

  function xFor(nuclide: Nuclide, list: Nuclide[]): number {
    const min = Math.min(...list.map((item) => item.n));
    const max = Math.max(...list.map((item) => item.n));
    return max === min ? 360 : 38 + ((nuclide.n - min) / (max - min)) * 644;
  }

  function yFor(nuclide: Nuclide): number {
    return 238 - ((logLife(nuclide) + 6) / 31) * 204;
  }

  function preferredNuclide(list: Nuclide[]): Nuclide | null {
    if (!list.length) return null;
    return [...list].sort((a, b) => {
      const abundanceDelta = (b.abundance ?? -1) - (a.abundance ?? -1);
      if (abundanceDelta) return abundanceDelta;
      if (a.stable !== b.stable) return a.stable ? -1 : 1;
      return Math.abs(a.n - a.z) - Math.abs(b.n - b.z);
    })[0];
  }

  function selectOnKey(event: KeyboardEvent, label: string): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      selectedLabel = label;
    }
  }

  $: isotopeDataRows = elementData?.domains.isotopes?.rows ?? [];
  $: nuclides = buildNuclides(isotopeDataRows, element);
  $: if ((element?.symbol ?? '') !== lastSymbol) {
    lastSymbol = element?.symbol ?? '';
    selectedLabel = preferredNuclide(nuclides)?.label ?? '';
  }
  $: selected = nuclides.find((item) => item.label === selectedLabel) ?? preferredNuclide(nuclides);
  $: stableCount = nuclides.filter((item) => item.stable).length;
  $: naturalCount = nuclides.filter((item) => (item.abundance ?? 0) > 0).length;
  $: maxAbundance = Math.max(...nuclides.map((item) => item.abundance ?? 0), 1);
</script>

<div class="advanced-science-pane nuclear-physics-pane">
  {#if loading}
    <div class="modal-load-state"><span></span><p>Cargando física nuclear…</p></div>
  {:else}
    <section class="science-inline-stats" aria-label="Resumen nuclear">
      <span><small>Nucleídos</small><strong>{nuclides.length}</strong></span>
      <span><small>Estables</small><strong>{stableCount}</strong></span>
      <span><small>Abundancia natural</small><strong>{naturalCount}</strong></span>
      <span><small>Intervalo N</small><strong>{nuclides.length ? `${nuclides[0].n}–${nuclides[nuclides.length - 1].n}` : '—'}</strong></span>
    </section>

    {#if nuclides.length}
      <section class="flat-science-section nuclide-map-card">
        <header>
          <div><small>Número de neutrones frente a vida media</small><h3>Cartografía isotópica</h3></div>
          <span>Escala vertical log₁₀(s) · los estables se sitúan arriba</span>
        </header>
        <div class="nuclear-chart-scroll">
          <svg class="nuclear-half-life-chart" viewBox="0 0 720 270" role="img" aria-label={`Vida media de los isótopos de ${element?.name_es}`}>
            <g class="chart-grid">
              {#each [-6, 0, 6, 12, 18, 24] as tick}
                {@const y = 238 - ((tick + 6) / 31) * 204}
                <line x1="38" x2="682" y1={y} y2={y}></line>
                <text x="32" y={y + 4} text-anchor="end">10^{tick}</text>
              {/each}
            </g>
            {#each nuclides as nuclide}
              <g
                class:active={selected?.label === nuclide.label}
                role="button"
                tabindex="0"
                aria-label={`Seleccionar ${nuclide.label}`}
                on:click={() => (selectedLabel = nuclide.label)}
                on:keydown={(event) => selectOnKey(event, nuclide.label)}
              >
                <circle cx={xFor(nuclide, nuclides)} cy={yFor(nuclide)} r={selected?.label === nuclide.label ? 7 : 5} style={`--nuclide-color:${decayColor(nuclide.decay)};`}>
                  <title>{nuclide.label} · {nuclide.halfLifeText} · {nuclide.decay}</title>
                </circle>
              </g>
            {/each}
            <text class="axis-caption" x="360" y="265" text-anchor="middle">Número de neutrones N</text>
          </svg>
        </div>
        <div class="decay-legend">
          {#each [['Estable', '#6fc79a'], ['α', '#e0a865'], ['β−', '#79c5d9'], ['β+/EC', '#d87988'], ['Fisión', '#c58bd8'], ['Otros', '#8b95a7']] as item}
            <span><i style={`--nuclide-color:${item[1]};`}></i>{item[0]}</span>
          {/each}
        </div>
      </section>

      <div class="nuclear-lower-grid flat-split-workspace">
        <section class="flat-science-section abundance-card">
          <header><div><small>Composición natural</small><h3>Abundancias isotópicas</h3></div><span>%</span></header>
          <div class="abundance-bars">
            {#each nuclides.filter((item) => (item.abundance ?? 0) > 0) as nuclide}
              <button type="button" class:active={selected?.label === nuclide.label} on:click={() => (selectedLabel = nuclide.label)}>
                <span>{nuclide.label}</span>
                <i><b style={`width:${((nuclide.abundance ?? 0) / maxAbundance) * 100}%;--nuclide-color:${decayColor(nuclide.decay)};`}></b></i>
                <strong>{nuclide.abundance?.toLocaleString('es-ES', { maximumFractionDigits: 6 })}%</strong>
              </button>
            {/each}
            {#if !nuclides.some((item) => (item.abundance ?? 0) > 0)}<p>IAEA no publica abundancia natural para los nucleídos disponibles.</p>{/if}
          </div>
        </section>

        <section class="flat-science-section nuclide-detail-card">
          <header><div><small>Nucleído seleccionado</small><h3>{selected?.label ?? '—'}</h3></div><span>{selected?.stable ? 'Estable' : selected?.decay}</span></header>
          {#if selected}
            <dl class="nuclide-detail-grid">
              <div><dt>Protones</dt><dd>{selected.z}</dd></div>
              <div><dt>Neutrones</dt><dd>{selected.n}</dd></div>
              <div><dt>Número másico</dt><dd>{selected.a}</dd></div>
              <div><dt>Vida media</dt><dd>{selected.halfLifeText}</dd></div>
              <div><dt>Espín y paridad</dt><dd>{selected.spin}</dd></div>
              <div><dt>Abundancia</dt><dd>{selected.abundance === null ? '—' : `${selected.abundance}%`}</dd></div>
              <div><dt>Dipolo magnético</dt><dd>{selected.magneticDipole}</dd></div>
              <div><dt>Cuadrupolo eléctrico</dt><dd>{selected.electricQuadrupole}</dd></div>
              <div><dt>Energía de enlace</dt><dd>{selected.binding === null ? '—' : `${selected.binding.toLocaleString('es-ES')} keV`}</dd></div>
              <div><dt>Qα</dt><dd>{selected.qAlpha === null ? '—' : `${selected.qAlpha.toLocaleString('es-ES')} keV`}</dd></div>
              <div><dt>QEC</dt><dd>{selected.qEc === null ? '—' : `${selected.qEc.toLocaleString('es-ES')} keV`}</dd></div>
              <div><dt>Modo principal</dt><dd>{selected.decay}</dd></div>
            </dl>
          {/if}
        </section>
      </div>
    {:else}
      <div class="science-empty-state"><strong>Sin nucleídos interpretables</strong><p>La carpeta del elemento todavía no contiene filas válidas de IAEA LiveChart.</p></div>
    {/if}

    <p class="science-method-note">La estabilidad se toma del campo IAEA <code>half_life = STABLE</code>. Las vidas medias se representan logarítmicamente; la ausencia de un dato no implica estabilidad.</p>
  {/if}
</div>
