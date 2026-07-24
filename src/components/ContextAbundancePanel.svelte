<script lang="ts">
  import type { DataRow, ElementDataPayload } from '../lib/atomicTypes';

  export let elementData: ElementDataPayload | null = null;
  export let loading = false;

  type Mode = 'abundance' | 'biology' | 'industry';
  let mode: Mode = 'abundance';

  const abundanceDefinitions = [
    { domain: 'astrophysics', property: 'abundance_universe', label: 'Universo' },
    { domain: 'geochemistry', property: 'abundance_crust', label: 'Corteza terrestre' },
    { domain: 'geochemistry', property: 'abundance_ocean', label: 'Océano' },
    { domain: 'biology', property: 'abundance_human', label: 'Cuerpo humano' },
  ];

  const industryLabels: Record<string, string> = {
    relative_supply_risk: 'Riesgo relativo de suministro',
    production_concentration: 'Concentración de producción',
    reserve_distribution: 'Concentración de reservas',
    recycling_rate: 'Tasa de reciclaje',
    substitutability: 'Sustituibilidad',
    top_3_producers: 'Principales productores',
    top_3_reserve_holders: 'Principales reservas',
    price_per_kg: 'Precio orientativo',
    uses: 'Usos',
  };

  function find(domain: string, property: string): DataRow | null {
    return elementData?.domains[domain]?.rows.find((row) => row.property === property) ?? null;
  }

  function number(value: unknown): number | null {
    const match = String(value ?? '').replace(/−/g, '-').replace(/,/g, '.').match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    const parsed = match ? Number(match[0]) : Number.NaN;
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  }

  function formatted(row: DataRow | null): string {
    if (!row?.value) return 'Sin dato';
    return `${row.value}${row.unit ? ` ${row.unit}` : ''}`;
  }

  $: abundances = abundanceDefinitions.map((item) => ({ ...item, row: find(item.domain, item.property) }));
  $: abundanceNumbers = abundances.map((item) => number(item.row?.value)).filter((value): value is number => value !== null);
  $: minLog = abundanceNumbers.length ? Math.min(...abundanceNumbers.map(Math.log10)) : -12;
  $: maxLog = abundanceNumbers.length ? Math.max(...abundanceNumbers.map(Math.log10)) : 0;
  $: biologicalRows = elementData?.domains.biology?.rows ?? [];
  $: safetyRows = elementData?.domains.environment?.rows ?? [];
  $: industryRows = elementData?.domains.industry?.rows ?? [];

  function abundanceWidth(value: number | null): number {
    if (value === null) return 0;
    const log = Math.log10(value);
    return maxLog === minLog ? 100 : 8 + ((log - minLog) / (maxLog - minLog)) * 92;
  }
</script>

<div class="advanced-science-pane context-science-pane">
  {#if loading}
    <div class="modal-load-state"><span></span><p>Cargando abundancia y contexto…</p></div>
  {:else}
    <nav class="science-mode-tabs context-mode-tabs" aria-label="Ámbitos de abundancia y contexto">
      <button class:active={mode === 'abundance'} type="button" on:click={() => (mode = 'abundance')}>Abundancia</button>
      <button class:active={mode === 'biology'} type="button" on:click={() => (mode = 'biology')}>Biología y seguridad</button>
      <button class:active={mode === 'industry'} type="button" on:click={() => (mode = 'industry')}>Industria</button>
    </nav>

    {#if mode === 'abundance'}
      <section class="abundance-context-chart">
        <header><div><small>Fracción másica aproximada</small><h3>Presencia en cuatro entornos</h3></div><span>Escala logarítmica · %</span></header>
        <div>
          {#each abundances as item}
            {@const value = number(item.row?.value)}
            <article class:missing={value === null}>
              <span>{item.label}</span>
              <i><b style={`width:${abundanceWidth(value)}%;`}></b></i>
              <strong>{formatted(item.row)}</strong>
            </article>
          {/each}
        </div>
        <p>La escala logarítmica permite comparar proporciones separadas por muchos órdenes de magnitud. “Sin dato” no se interpreta como ausencia.</p>
      </section>
    {:else if mode === 'biology'}
      <section class="context-table-sheet">
        <header><div><small>Organismo, exposición y clasificación</small><h3>Biología y seguridad</h3></div><span>{biologicalRows.length + safetyRows.length} registros</span></header>
        <dl>
          {#each biologicalRows as row}
            <div><dt>{row.property.replaceAll('_', ' ')}</dt><dd><strong>{formatted(row)}</strong><small>{row.organism_or_use || row.notes}</small></dd></div>
          {/each}
          {#each safetyRows as row}
            <div><dt>{row.property.replaceAll('_', ' ')}</dt><dd><strong>{formatted(row)}</strong><small>{row.classification || row.notes}</small></dd></div>
          {/each}
        </dl>
        {#if !biologicalRows.length && !safetyRows.length}<div class="science-empty-state compact"><strong>Sin registros trazables</strong><p>No se deduce toxicidad a partir del elemento aislado ni de un identificador vacío.</p></div>{/if}
      </section>
    {:else}
      <section class="context-table-sheet industry-sheet">
        <header><div><small>Uso, criticidad y suministro</small><h3>Industria y economía</h3></div><span>{industryRows.length} registros</span></header>
        <dl>
          {#each industryRows as row}
            <div class:wide={row.property === 'uses'}><dt>{industryLabels[row.property] ?? row.property.replaceAll('_', ' ')}</dt><dd><strong>{formatted(row)}</strong><small>{[row.region, row.year].filter(Boolean).join(' · ') || row.notes}</small></dd></div>
          {/each}
        </dl>
        {#if !industryRows.length}<div class="science-empty-state compact"><strong>Sin indicadores industriales</strong><p>La ausencia de precio o riesgo no equivale a valor cero.</p></div>{/if}
      </section>
    {/if}

    <p class="science-method-note">Abundancia, toxicidad, precio y criticidad no son constantes universales. Deben conservar contexto, fecha, especie química, vía de exposición, mercado y fuente.</p>
  {/if}
</div>
