<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import AtomicStage from './AtomicStage.svelte';
  import DataDomainTable from './DataDomainTable.svelte';
  import ElementPanel from './ElementPanel.svelte';
  import SpectralLinesTable from './SpectralLinesTable.svelte';
  import SpectrumViewer from './SpectrumViewer.svelte';
  import type {
    ComparisonScope,
    ElementDataDomain,
    ElementDataPayload,
    ElementWithLines,
    NistFileStatus,
    SpectrumMode
  } from '../lib/atomicTypes';
  import { loadElementData } from '../lib/dataLoader';

  type TabId = Exclude<ComparisonScope, 'global'>;

  const PROPERTY_IDS = ['identity', 'atomic', 'physical', 'photonics'];
  const CHEMISTRY_IDS = ['chemical', 'materials', 'thermodynamics', 'compounds', 'computational'];
  const CONTEXT_IDS = ['history', 'geochemistry', 'astrophysics', 'biology', 'environment', 'industry', 'analytical', 'radiation'];

  const tabs: Array<{ id: TabId; label: string }> = [
    { id: 'summary', label: 'Resumen' }, { id: 'atom', label: 'Átomo 3D' },
    { id: 'properties', label: 'Propiedades' }, { id: 'isotopes', label: 'Isótopos' },
    { id: 'spectrum', label: 'Espectro' }, { id: 'lines', label: 'Líneas' },
    { id: 'levels', label: 'Niveles' }, { id: 'chemistry', label: 'Química' },
    { id: 'context', label: 'Contexto' }, { id: 'sources', label: 'Fuentes' }
  ];

  export let element: ElementWithLines | null = null;
  export let comparedSymbols: string[] = [];

  let activeTab: TabId = 'summary';
  let mode: SpectrumMode = 'emission';
  let lastSymbol = '';
  let elementData: ElementDataPayload | null = null;
  let loadingData = false;
  let dataError = '';
  let loadToken = 0;

  const dispatch = createEventDispatcher<{
    close: void;
    compare: { symbol: string; scope: ComparisonScope };
  }>();

  $: if (element && element.symbol !== lastSymbol) {
    activeTab = 'summary';
    mode = 'emission';
    lastSymbol = element.symbol;
    void loadDataFor(element);
  }

  $: isCompared = element ? comparedSymbols.includes(element.symbol) : false;
  $: availableDomains = elementData ? Object.values(elementData.domains).filter((domain) => domain.available) : [];
  $: hasNistProblem = Boolean(
    element?.nist &&
      ((element.nist.espectro.present && !element.nist.espectro.table_like) ||
        (element.nist.niveles.present && !element.nist.niveles.table_like))
  );
  $: nistFiles = element?.nist
    ? [
        { label: 'Espectro / líneas', item: element.nist.espectro },
        { label: 'Niveles de energía', item: element.nist.niveles }
      ]
    : [];

  async function loadDataFor(target: ElementWithLines): Promise<void> {
    const token = ++loadToken;
    elementData = null;
    dataError = '';
    loadingData = true;
    try {
      const loaded = await loadElementData(target.symbol, target.dataIndex);
      if (token === loadToken && element?.symbol === target.symbol) elementData = loaded;
    } catch (error) {
      if (token === loadToken) dataError = error instanceof Error ? error.message : 'No se pudieron cargar los datos del elemento.';
    } finally {
      if (token === loadToken) loadingData = false;
    }
  }

  function closeOnBackdrop(event: MouseEvent): void {
    if (event.currentTarget === event.target) dispatch('close');
  }

  function statusLabel(file: NistFileStatus): string {
    if (!file.present) return 'No encontrado';
    if (file.table_like) return 'CSV tabular válido';
    if (file.status === 'invalid_single_column_script') return 'Contiene JavaScript';
    if (file.status === 'invalid_html_export') return 'Parece HTML';
    if (file.status === 'single_column_csv') return 'CSV de una columna';
    return file.status;
  }

  function domainList(ids: string[]): ElementDataDomain[] {
    if (!elementData) return [];
    return ids
      .map((id) => elementData?.domains[id])
      .filter((domain): domain is ElementDataDomain => Boolean(domain?.available));
  }

  function compareCurrent(): void {
    if (element) dispatch('compare', { symbol: element.symbol, scope: activeTab });
  }
</script>

{#if element}
  <div class="modal-backdrop" role="presentation" on:click={closeOnBackdrop}>
    <div class="element-modal master-modal" aria-modal="true" role="dialog" aria-label={`Ficha maestra de ${element.name_es}`} tabindex="-1">
      <header class="modal-header">
        <div class="modal-identity">
          <div class="modal-symbol"><span>{element.atomic_number}</span><strong>{element.symbol}</strong></div>
          <div>
            <p class="eyebrow">Ficha maestra · {element.category}</p>
            <h2>{element.name_es}</h2>
            <small>{element.name_en} · Grupo {element.group} · Periodo {element.period} · Bloque {element.block || '—'}</small>
          </div>
        </div>

        <div class="modal-actions icon-modal-actions">
          <button
            class:active={isCompared}
            class="modal-icon-button compare-icon-button"
            type="button"
            on:click={compareCurrent}
            aria-label={isCompared ? `Quitar ${element.name_es} del comparador` : `Comparar ${element.name_es}`}
            title={isCompared ? 'Quitar del comparador' : `Comparar desde ${tabs.find((tab) => tab.id === activeTab)?.label ?? 'esta sección'}`}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="3.5" y="5" width="7" height="14"></rect><rect x="13.5" y="5" width="7" height="14"></rect>
              <path d="M10.5 9h3M10.5 15h3"></path>
            </svg>
          </button>
          <button class="modal-icon-button close-button" type="button" on:click={() => dispatch('close')} aria-label="Cerrar ficha" title="Cerrar">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"></path></svg>
          </button>
        </div>
      </header>

      <nav class="modal-tabs master-tabs" aria-label="Secciones de la ficha maestra">
        {#each tabs as tab}
          <button class:active={activeTab === tab.id} class:problem={tab.id === 'sources' && hasNistProblem} type="button" on:click={() => (activeTab = tab.id)}>
            {tab.label}{tab.id === 'sources' && hasNistProblem ? ' · revisar' : ''}
          </button>
        {/each}
      </nav>

      <div class="modal-content master-content">
        {#if dataError}<p class="empty-copy modal-data-error">{dataError}</p>{/if}

        {#if activeTab === 'summary'}
          <div class="tab-pane summary-pane"><ElementPanel {element} {elementData} {loadingData} /></div>
        {:else if activeTab === 'atom'}
          <div class="tab-pane atom-tab"><AtomicStage {element} {elementData} /></div>
        {:else if activeTab === 'properties'}
          <div class="tab-pane tab-scroll domain-list-pane">
            {#if loadingData}<div class="modal-load-state"><span></span><p>Cargando propiedades…</p></div>
            {:else}{#each domainList(PROPERTY_IDS) as domain}<DataDomainTable {domain} />{/each}{/if}
          </div>
        {:else if activeTab === 'isotopes'}
          <div class="tab-pane table-pane">
            {#if loadingData}<div class="modal-load-state"><span></span><p>Cargando isótopos…</p></div>
            {:else}<DataDomainTable domain={elementData?.domains.isotopes ?? null} fitHeight={true} pageSize={18} />{/if}
          </div>
        {:else if activeTab === 'spectrum'}
          <div class="tab-pane spectrum-workspace">
            <div class="spectrum-toolbar">
              <strong>{element.name_es} · {element.lines.length.toLocaleString('es-ES')} líneas</strong>
              <div class="segmented-control small">
                <button class:active={mode === 'emission'} type="button" on:click={() => (mode = 'emission')}>Emisión</button>
                <button class:active={mode === 'absorption'} type="button" on:click={() => (mode = 'absorption')}>Absorción</button>
              </div>
            </div>
            <SpectrumViewer lines={element.lines} {mode} title={`${element.name_es} (${element.symbol})`} />
          </div>
        {:else if activeTab === 'lines'}
          <div class="tab-pane table-pane"><SpectralLinesTable lines={element.lines} /></div>
        {:else if activeTab === 'levels'}
          <div class="tab-pane table-pane">
            {#if loadingData}<div class="modal-load-state"><span></span><p>Cargando niveles…</p></div>
            {:else}<DataDomainTable domain={elementData?.domains.nist_levels ?? null} fitHeight={true} pageSize={18} />{/if}
          </div>
        {:else if activeTab === 'chemistry'}
          <div class="tab-pane tab-scroll domain-list-pane">
            {#if loadingData}<div class="modal-load-state"><span></span><p>Cargando química…</p></div>
            {:else}{#each domainList(CHEMISTRY_IDS) as domain}<DataDomainTable {domain} />{/each}{/if}
          </div>
        {:else if activeTab === 'context'}
          <div class="tab-pane tab-scroll domain-list-pane">
            {#if loadingData}<div class="modal-load-state"><span></span><p>Cargando contexto…</p></div>
            {:else}{#each domainList(CONTEXT_IDS) as domain}<DataDomainTable {domain} />{/each}{/if}
          </div>
        {:else if activeTab === 'sources'}
          <div class="tab-pane tab-scroll sources-pane compact-sources-pane">
            {#if loadingData}<div class="modal-load-state"><span></span><p>Cargando fuentes…</p></div>
            {:else}
              <section class="dataset-coverage-panel compact-dataset-coverage">
                <header class="inline-summary-header"><div><strong>Cobertura local</strong><span>—</span><small>{availableDomains.length} archivos con datos</small></div></header>
                <div class="dataset-coverage-rows">{#each availableDomains as domain}<div><span>{domain.label}</span><b>{domain.row_count.toLocaleString('es-ES')}</b></div>{/each}</div>
              </section>
              <DataDomainTable domain={elementData?.domains.sources ?? null} />
              <section class="nist-compact-panel">
                <header class="inline-summary-header"><div><strong>Validación NIST</strong><span>—</span><small>{element.nist?.imported_line_count ?? 0} líneas interpretadas</small></div></header>
                {#if hasNistProblem}<p class="nist-inline-warning">Alguno de los archivos NIST no tiene estructura tabular válida.</p>{/if}
                {#if element.nist}
                  <div class="nist-status-list">
                    {#each nistFiles as file}
                      <div class:problem={file.item.present && !file.item.table_like}>
                        <strong>{file.label}</strong><span>{statusLabel(file.item)}</span><small>{file.item.row_count.toLocaleString('es-ES')} filas · {file.item.columns.length} columnas</small>
                      </div>
                    {/each}
                  </div>
                {/if}
              </section>
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
