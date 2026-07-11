<script lang="ts">
  import { afterUpdate, onMount } from 'svelte';
  import type { DataRow, ElementDataDomain } from '../lib/atomicTypes';

  interface PropertyItem {
    label: string;
    value: string;
    unit: string;
    source: string;
    sourceUrl: string;
    tooltip: string;
  }

  export let domain: ElementDataDomain | null = null;
  export let pageSize = 24;
  export let fitHeight = false;

  let sectionElement: HTMLElement;
  let tableViewport: HTMLDivElement;
  let page = 0;
  let measuredPageSize = pageSize;
  let lastDomainId = '';
  let resizeObserver: ResizeObserver | null = null;
  let measurementFrame = 0;

  $: if ((domain?.id ?? '') !== lastDomainId) {
    lastDomainId = domain?.id ?? '';
    page = 0;
  }

  $: propertyItems = buildPropertyItems(domain);
  $: isPropertyList = propertyItems.length > 0;
  $: displayColumns = (domain?.columns ?? []).filter(
    (column) => !['source_url', 'retrieved_at', 'notes'].includes(column.toLowerCase())
  );
  $: effectivePageSize = fitHeight && !isPropertyList ? measuredPageSize : pageSize;
  $: totalPages = isPropertyList
    ? 1
    : Math.max(1, Math.ceil((domain?.rows.length ?? 0) / Math.max(1, effectivePageSize)));
  $: if (page >= totalPages) page = totalPages - 1;
  $: visibleRows = domain?.rows.slice(page * effectivePageSize, (page + 1) * effectivePageSize) ?? [];

  function isUrl(value: string): boolean {
    return /^https?:\/\//i.test(value);
  }

  function columnLabel(column: string): string {
    const labels: Record<string, string> = {
      property: 'Propiedad', value: 'Valor', unit: 'Unidad', source: 'Fuente',
      atomic_number: 'Z', symbol: 'Símbolo', name_en: 'Nombre (EN)', name_es: 'Nombre',
      standard_state: 'Estado estándar', group_block: 'Clasificación', half_life: 'Vida media',
      half_life_sec: 'Vida media (s)', decay_1: 'Decaimiento principal', abundance: 'Abundancia',
      Configuration: 'Configuración', Term: 'Término', 'Level (cm-1)': 'Nivel (cm⁻¹)',
      'Uncertainty (cm-1)': 'Incertidumbre (cm⁻¹)'
    };
    return labels[column] ?? column.replaceAll('_', ' ');
  }

  function tooltipFor(row: DataRow): string {
    return [row.notes, row.source ? `Fuente: ${row.source}` : '', row.retrieved_at ? `Consultado: ${row.retrieved_at}` : '']
      .filter(Boolean)
      .join('\n');
  }

  function buildPropertyItems(current: ElementDataDomain | null): PropertyItem[] {
    if (!current?.available || !current.rows.length) return [];
    const hasPropertyValue = current.columns.includes('property') && current.columns.includes('value');
    if (hasPropertyValue) {
      return current.rows.map((row) => ({
        label: columnLabel(row.property || 'property'), value: row.value || '—', unit: row.unit || '',
        source: row.source || '', sourceUrl: row.source_url || '', tooltip: tooltipFor(row)
      }));
    }
    if (current.id !== 'identity') return [];
    const row = current.rows[0];
    const metadata = new Set(['source', 'source_url', 'retrieved_at', 'notes']);
    return current.columns
      .filter((column) => !metadata.has(column.toLowerCase()))
      .map((column) => ({
        label: columnLabel(column), value: row[column] || '—', unit: '', source: row.source || '',
        sourceUrl: row.source_url || '', tooltip: tooltipFor(row)
      }));
  }

  function scheduleMeasurement(): void {
    if (!fitHeight || isPropertyList) return;
    cancelAnimationFrame(measurementFrame);
    measurementFrame = requestAnimationFrame(measurePageSize);
  }

  function measurePageSize(): void {
    if (!fitHeight || !sectionElement || !tableViewport) return;
    const head = tableViewport.querySelector('thead')?.getBoundingClientRect().height ?? 34;
    const row = tableViewport.querySelector('tbody tr')?.getBoundingClientRect().height ?? 34;
    const available = Math.max(110, tableViewport.clientHeight - head - 2);
    const next = Math.max(4, Math.min(60, Math.floor(available / Math.max(28, row))));
    if (next !== measuredPageSize) measuredPageSize = next;
  }

  function refreshMeasurementTargets(): void {
    if (resizeObserver) {
      if (sectionElement) resizeObserver.observe(sectionElement);
      if (tableViewport) resizeObserver.observe(tableViewport);
    }
    scheduleMeasurement();
  }

  afterUpdate(refreshMeasurementTargets);

  onMount(() => {
    resizeObserver = new ResizeObserver(scheduleMeasurement);
    refreshMeasurementTargets();
    return () => {
      cancelAnimationFrame(measurementFrame);
      resizeObserver?.disconnect();
    };
  });
</script>

{#if domain?.available}
  <section bind:this={sectionElement} class:property-domain={isPropertyList} class:table-domain={!isPropertyList} class:fit-height={fitHeight} class="domain-section flat-domain" aria-label={domain.label}>
    <header class="domain-header inline-domain-header">
      <div><h3>{domain.label}</h3><span>—</span><small>{domain.file}</small></div>
      <span class="domain-count">{domain.row_count.toLocaleString('es-ES')} registros</span>
    </header>

    {#if isPropertyList}
      <dl class="property-list minimal-property-list">
        {#each propertyItems as item}
          <div title={item.tooltip || undefined}>
            <dt>{item.label}</dt>
            <dd>
              {#if item.sourceUrl && isUrl(item.sourceUrl)}
                <a href={item.sourceUrl} target="_blank" rel="noreferrer">{item.value}{item.unit ? ` ${item.unit}` : ''}</a>
              {:else}
                <span>{item.value}{item.unit ? ` ${item.unit}` : ''}</span>
              {/if}
            </dd>
          </div>
        {/each}
      </dl>
    {:else}
      <div bind:this={tableViewport} class="technical-table domain-table paginated-table">
        <table>
          <thead><tr>{#each displayColumns as column}<th>{columnLabel(column)}</th>{/each}</tr></thead>
          <tbody>
            {#each visibleRows as row}
              <tr>
                {#each displayColumns as column}
                  <td title={row[column] || undefined}>
                    {#if isUrl(row[column] ?? '')}<a href={row[column] ?? '#'} target="_blank" rel="noreferrer">Abrir fuente</a>{:else}{row[column] || '—'}{/if}
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    {#if !isPropertyList && totalPages > 1}
      <footer class="adaptive-pagination" aria-label={`Paginación de ${domain.label}`}>
        <button type="button" disabled={page === 0} on:click={() => (page -= 1)} aria-label="Página anterior" title="Página anterior">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 5-7 7 7 7"></path></svg>
        </button>
        <span>{page + 1} / {totalPages}</span>
        <button type="button" disabled={page >= totalPages - 1} on:click={() => (page += 1)} aria-label="Página siguiente" title="Página siguiente">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"></path></svg>
        </button>
      </footer>
    {/if}
  </section>
{:else if domain?.present}
  <section class="domain-section domain-empty flat-domain">
    <p><strong>{domain.label}:</strong> el archivo existe, pero todavía no contiene registros.</p>
  </section>
{/if}
