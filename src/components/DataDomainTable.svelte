<script lang="ts">
  import type { ElementDataDomain } from '../lib/atomicTypes';

  export let domain: ElementDataDomain | null = null;

  const PAGE_SIZE = 100;
  let page = 0;
  let lastDomainId = '';

  $: if ((domain?.id ?? '') !== lastDomainId) {
    lastDomainId = domain?.id ?? '';
    page = 0;
  }

  $: totalPages = Math.max(1, Math.ceil((domain?.rows.length ?? 0) / PAGE_SIZE));
  $: if (page >= totalPages) page = totalPages - 1;
  $: visibleRows = domain?.rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE) ?? [];
  $: isPropertyList = Boolean(
    domain?.columns.some((column) => column.toLowerCase() === 'property') &&
      domain?.columns.some((column) => column.toLowerCase() === 'value')
  );

  function isUrl(value: string): boolean {
    return /^https?:\/\//i.test(value);
  }

  function columnLabel(column: string): string {
    const labels: Record<string, string> = {
      property: 'Propiedad',
      value: 'Valor',
      unit: 'Unidad',
      source: 'Fuente',
      source_url: 'Enlace oficial',
      retrieved_at: 'Consultado',
      notes: 'Notas',
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
</script>

{#if domain?.available}
  <section class="domain-section" aria-label={domain.label}>
    <header class="domain-header">
      <div>
        <p class="eyebrow">{domain.file}</p>
        <h3>{domain.label}</h3>
      </div>
      <span class="range-pill">{domain.row_count.toLocaleString('es-ES')} registros</span>
    </header>

    {#if isPropertyList}
      <div class="property-record-grid">
        {#each visibleRows as row}
          <article>
            <span>{row.property || 'Propiedad'}</span>
            <strong>{row.value || '—'}{row.unit ? ` ${row.unit}` : ''}</strong>
            {#if row.notes}<p>{row.notes}</p>{/if}
            {#if row.source_url && isUrl(row.source_url)}
              <a href={row.source_url} target="_blank" rel="noreferrer">{row.source || 'Fuente oficial'}</a>
            {:else if row.source}
              <small>{row.source}</small>
            {/if}
          </article>
        {/each}
      </div>
    {:else}
      <div class="technical-table domain-table">
        <table>
          <thead>
            <tr>
              {#each domain.columns as column}<th>{columnLabel(column)}</th>{/each}
            </tr>
          </thead>
          <tbody>
            {#each visibleRows as row}
              <tr>
                {#each domain.columns as column}
                  <td>
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
      <footer class="domain-pagination">
        <button type="button" disabled={page === 0} on:click={() => (page -= 1)}>Anterior</button>
        <span>Página {page + 1} de {totalPages}</span>
        <button type="button" disabled={page >= totalPages - 1} on:click={() => (page += 1)}>Siguiente</button>
      </footer>
    {/if}
  </section>
{:else if domain?.present}
  <section class="domain-section domain-empty">
    <p><strong>{domain.label}:</strong> el archivo existe, pero todavía no contiene registros.</p>
  </section>
{/if}
