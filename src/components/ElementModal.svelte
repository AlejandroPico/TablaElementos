<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import AtomicStage from './AtomicStage.svelte';
  import DataDomainTable from './DataDomainTable.svelte';
  import ElementPanel from './ElementPanel.svelte';
  import SpectrumViewer from './SpectrumViewer.svelte';
  import type {
    ComparisonScope,
    ElementDataDomain,
    ElementDataPayload,
    ElementWithLines,
    NistFileStatus,
    SpectralLine,
    SpectrumMode
  } from '../lib/atomicTypes';
  import { loadElementData } from '../lib/dataLoader';
  import { getStrongestLines } from '../lib/filters';
  import { formatEv, formatNm, wavelengthRegion } from '../lib/wavelengthColor';

  type TabId = Exclude<ComparisonScope, 'global'>;

  const PROPERTY_IDS = ['identity', 'atomic', 'physical', 'photonics'];
  const CHEMISTRY_IDS = ['chemical', 'materials', 'thermodynamics', 'compounds', 'computational'];
  const CONTEXT_IDS = ['history', 'geochemistry', 'astrophysics', 'biology', 'environment', 'industry', 'analytical', 'radiation'];

  const tabs: Array<{ id: TabId; label: string }> = [
    { id: 'summary', label: 'Resumen' },
    { id: 'atom', label: 'Átomo 3D' },
    { id: 'properties', label: 'Propiedades' },
    { id: 'isotopes', label: 'Isótopos' },
    { id: 'spectrum', label: 'Espectro' },
    { id: 'lines', label: 'Líneas' },
    { id: 'levels', label: 'Niveles' },
    { id: 'chemistry', label: 'Química' },
    { id: 'context', label: 'Contexto' },
    { id: 'sources', label: 'Fuentes' }
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
  $: strongestLines = element ? getStrongestLines(element.lines, 8) : [];
  $: strongestLineIds = new Set(strongestLines.map(lineId));
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

  function energyJump(line: SpectralLine): number {
    return line.upper_level_ev - line.lower_level_ev;
  }

  function lineId(line: SpectralLine): string {
    return [line.species, Number(line.wavelength_nm).toFixed(6), line.transition, line.label].join('|');
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

  function compare(scope: ComparisonScope): void {
    if (element) dispatch('compare', { symbol: element.symbol, scope });
  }

  function currentTabLabel(): string {
    return tabs.find((tab) => tab.id === activeTab)?.label ?? 'sección';
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

        <div class="modal-actions comparison-actions">
          <button class:active={isCompared} type="button" on:click={() => compare('global')}>Comparar todo</button>
          <button type="button" on:click={() => compare(activeTab)}>Comparar {currentTabLabel()}</button>
          <button class="close-button" type="button" on:click={() => dispatch('close')} aria-label="Cerrar ficha">×</button>
        </div>
      </header>

      <nav class="modal-tabs master-tabs" aria-label="Secciones de la ficha maestra">
        {#each tabs as tab}
          <button
            class:active={activeTab === tab.id}
            class:problem={tab.id === 'sources' && hasNistProblem}
            type="button"
            on:click={() => (activeTab = tab.id)}
          >{tab.label}{tab.id === 'sources' && hasNistProblem ? ' · revisar' : ''}</button>
        {/each}
      </nav>

      <div class="modal-content master-content">
        {#if dataError}<p class="empty-copy modal-data-error">{dataError}</p>{/if}

        {#if activeTab === 'summary'}
          <div class="tab-pane tab-scroll"><ElementPanel {element} {elementData} {loadingData} /></div>
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
            {:else}<DataDomainTable domain={elementData?.domains.isotopes ?? null} pageSize={22} />{/if}
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
          <div class="tab-pane table-pane spectral-lines-panel">
            {#if strongestLines.length}
              <div class="featured-lines" aria-label="Líneas espectrales más intensas">
                <p>Líneas destacadas</p>
                <div>{#each strongestLines as line}<span class="featured-line"><i style={`--line-color:${line.approximate_color};`}></i><b>{formatNm(line.wavelength_nm)}</b><small>{line.label}</small></span>{/each}</div>
              </div>
            {/if}
            <div class="technical-table modal-table single-scroll-table">
              <table>
                <thead><tr><th>Línea</th><th>Especie</th><th>λ</th><th>Región</th><th>Intensidad</th><th>Nivel inferior</th><th>Nivel superior</th><th>ΔE</th><th>Transición</th></tr></thead>
                <tbody>{#each element.lines as line}<tr class:featured={strongestLineIds.has(lineId(line))}><td>{line.label}</td><td>{line.species}</td><td>{formatNm(line.wavelength_nm)}</td><td>{wavelengthRegion(line.wavelength_nm)}</td><td>{line.intensity.toFixed(2)}</td><td>{formatEv(line.lower_level_ev)}</td><td>{formatEv(line.upper_level_ev)}</td><td>{formatEv(energyJump(line))}</td><td>{line.transition}</td></tr>{/each}</tbody>
              </table>
            </div>
          </div>
        {:else if activeTab === 'levels'}
          <div class="tab-pane table-pane">
            {#if loadingData}<div class="modal-load-state"><span></span><p>Cargando niveles…</p></div>
            {:else}<DataDomainTable domain={elementData?.domains.nist_levels ?? null} pageSize={22} />{/if}
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
          <div class="tab-pane tab-scroll sources-pane">
            {#if loadingData}<div class="modal-load-state"><span></span><p>Cargando fuentes…</p></div>
            {:else}
              <section class="dataset-coverage-panel"><header><div><p class="eyebrow">Información interna</p><h2>Cobertura del dataset local</h2></div><strong>{availableDomains.length} archivos con datos</strong></header><div class="dataset-coverage-rows">{#each availableDomains as domain}<div><span>{domain.label}</span><b>{domain.row_count.toLocaleString('es-ES')} registros</b></div>{/each}</div></section>
              <DataDomainTable domain={elementData?.domains.sources ?? null} />
              <section class="modal-data-card nist-panel"><div class="section-title-row compact"><div><p class="eyebrow">Procedencia y validación</p><h2>Estado de los archivos NIST</h2></div><span class="range-pill">{element.nist?.imported_line_count ?? 0} líneas</span></div>{#if hasNistProblem}<p class="nist-inline-warning">Alguno de los archivos NIST no tiene estructura tabular válida.</p>{/if}{#if element.nist}<div class="nist-status-grid">{#each nistFiles as file}<article class:problem={file.item.present && !file.item.table_like} class="nist-status-card"><header><strong>{file.label}</strong><span>{statusLabel(file.item)}</span></header><dl><div><dt>Archivo</dt><dd>{file.item.file}</dd></div><div><dt>Filas</dt><dd>{file.item.row_count.toLocaleString('es-ES')}</dd></div><div><dt>Columnas</dt><dd>{file.item.columns.length ? file.item.columns.slice(0, 8).join(', ') : '—'}</dd></div></dl><p>{file.item.notes}</p></article>{/each}</div>{/if}</section>
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
