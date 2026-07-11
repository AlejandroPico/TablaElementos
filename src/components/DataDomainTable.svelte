<script lang="ts">
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

  let page = 0;
  let lastDomainId = '';

  $: if ((domain?.id ?? '') !== lastDomainId) {
    lastDomainId = domain?.id ?? '';
    page = 0;
  }

  $: propertyItems = buildPropertyItems(domain);
  $: isPropertyList = propertyItems.length > 0;
  $: displayColumns = (domain?.columns ?? []).filter(
    (column) => !['source_url', 'retrieved_at', 'notes'].includes(column.toLowerCase())
  );
  $: totalPages = Math.max(1, Math.ceil((domain?.rows.length ?? 0) / Math.max(1, pageSize)));
  $: if (page >= totalPages) page = totalPages - 1;
  $: visibleRows = domain?.rows.slice(page * pageSize, (page + 1) * pageSize) ?? [];

  function isUrl(value: string): boolean {
    return /^https?:\/\//i.test(value);
  }

  function columnLabel(column: string): string {
    const labels: Record<string, string> = {
      property: 'Propiedad',
      value: 'Valor',
      unit: 'Unidad',
      source: 'Fuente',
      atomic_number: 'Z',
      symbol: 'Símbolo',
      name_en: 'Nombre (EN)',
      name_es: 'Nombre',
      standard_state: 'Estado estándar',
      group_block: 'Clasificación',
      half_life: 'Vida media',
      half_life_sec: 'Vida media (s)',
      decay_1: 'Decaimiento principal',
      abundance: 'Abundancia',
      Configuration: 'Configuración',
      Term: 'Término',
      'Level (cm-1)': 'Nivel (cm⁻¹)',
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
        label: columnLabel(row.property || 'property'),
        value: row.value || '—',
        unit: row.unit || '',
        source: row.source || '',
        sourceUrl: row.source_url || '',
        tooltip: tooltipFor(row)
      }));
    }

    if (current.id !== 'identity') return [];
    const row = current.rows[0];
    const metadata = new Set(['source', 'source_url', 'retrieved_at', 'notes']);
    return current.columns
      .filter((column) => !metadata.has(column.toLowerCase()))
      .map((column) => ({
        label: columnLabel(column),
        value: row[column] || '—',
        unit: '',
        source: row.source || '',
        sourceUrl: row.source_url || '',
        tooltip: tooltipFor(row)
      }));
  }
</script>

{#if domain?.available}
  <section class:property-domain={isPropertyList} class:table-domain={!isPropertyList} class="domain-section flat-domain" aria-label={domain.label}>
    <header class="domain-header compact-domain-header">
      <div>
        <p class="eyebrow">{domain.file}</p>
        <h3>{domain.label}</h3>
      </div>
      <span class="domain-count">{domain.row_count.toLocaleString('es-ES')} registros</span>
    </header>

    {#if isPropertyList}
      <dl class="property-list">
        {#each propertyItems as item}
          <div title={item.tooltip || undefined}>
            <dt>{item.label}</dt>
            <dd>
              {#if item.sourceUrl && isUrl(item.sourceUrl)}
                <a href={item.sourceUrl} target="_blank" rel="noreferrer">
                  {item.value}{item.unit ? ` ${item.unit}` : ''}
                </a>
              {:else}
                <span>{item.value}{item.unit ? ` ${item.unit}` : ''}</span>
              {/if}
            </dd>
          </div>
        {/each}
      </dl>
    {:else}
      <div class="technical-table domain-table single-scroll-table">
        <table>
          <thead>
            <tr>
              {#each displayColumns as column}<th>{columnLabel(column)}</th>{/each}
            </tr>
          </thead>
          <tbody>
            {#each visibleRows as row}
              <tr>
                {#each displayColumns as column}
                  <td title={row[column] || undefined}>
                    {#if isUrl(row[column] ?? '')}
                      <a href={row[column] ?? '#'} target="_blank" rel="noreferrer">Abrir fuente</a>
                    {:else}
                      {row[column] || '—'}
                    {/if}
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    {#if totalPages > 1}
      <footer class="domain-pagination compact-pagination">
        <button type="button" disabled={page === 0} on:click={() => (page -= 1)}>Anterior</button>
        <span>{page + 1} / {totalPages}</span>
        <button type="button" disabled={page >= totalPages - 1} on:click={() => (page += 1)}>Siguiente</button>
      </footer>
    {/if}
  </section>
{:else if domain?.present}
  <section class="domain-section domain-empty flat-domain">
    <p><strong>{domain.label}:</strong> el archivo existe, pero todavía no contiene registros.</p>
  </section>
{/if}
