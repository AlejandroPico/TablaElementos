<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import AtomicModel3D from './AtomicModel3D.svelte';
  import DataDomainTable from './DataDomainTable.svelte';
  import ElementPanel from './ElementPanel.svelte';
  import SpectrumViewer from './SpectrumViewer.svelte';
  import type {
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

  type TabId =
    | 'summary'
    | 'atom'
    | 'properties'
    | 'isotopes'
    | 'spectrum'
    | 'lines'
    | 'levels'
    | 'chemistry'
    | 'context'
    | 'sources';

  const PROPERTY_IDS = ['identity', 'atomic', 'physical', 'photonics'];
  const CHEMISTRY_IDS = ['chemical', 'materials', 'thermodynamics', 'compounds', 'computational'];
  const CONTEXT_IDS = [
    'history',
    'geochemistry',
    'astrophysics',
    'biology',
    'environment',
    'industry',
    'analytical',
    'radiation'
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

  const dispatch = createEventDispatcher<{ close: void; compare: string }>();

  $: hasNistProblem = element
    ? Boolean(
        element.nist &&
          ((element.nist.espectro.present && !element.nist.espectro.table_like) ||
            (element.nist.niveles.present && !element.nist.niveles.table_like))
      )
    : false;

  $: if (element && element.symbol !== lastSymbol) {
    activeTab = 'summary';
    mode = 'emission';
    lastSymbol = element.symbol;
    void loadDataFor(element);
  }

  $: isCompared = element ? comparedSymbols.includes(element.symbol) : false;
  $: nistFiles = element?.nist
    ? [
        { label: 'Espectro / líneas', item: element.nist.espectro },
        { label: 'Niveles de energía', item: element.nist.niveles }
      ]
    : [];
  $: strongestLines = element ? getStrongestLines(element.lines, 8) : [];
  $: strongestLineIds = new Set(strongestLines.map(lineId));
  $: availableDomains = elementData
    ? Object.values(elementData.domains).filter((domain) => domain.available)
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
      if (token === loadToken) {
        dataError = error instanceof Error ? error.message : 'No se pudieron cargar los datos del elemento.';
      }
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
    return [
      line.species,
      Number(line.wavelength_nm).toFixed(6),
      line.transition,
      line.label
    ].join('|');
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
    const data = elementData;
    if (!data) return [];
    return ids
      .map((id) => data.domains[id])
      .filter((domain): domain is ElementDataDomain => Boolean(domain && domain.available));
  }

  function hasAnyDomain(ids: string[]): boolean {
    return domainList(ids).length > 0;
  }
</script>

{#if element}
  <div class="modal-backdrop" role="presentation" on:click={closeOnBackdrop}>
    <div
      class="element-modal master-modal"
      aria-modal="true"
      role="dialog"
      aria-label={`Ficha maestra de ${element.name_es}`}
      tabindex="-1"
    >
      <header class="modal-header">
        <div class="modal-identity">
          <div class="modal-symbol"><span>{element.atomic_number}</span><strong>{element.symbol}</strong></div>
          <div>
            <p class="eyebrow">Ficha maestra · {element.category}</p>
            <h2>{element.name_es}</h2>
            <small>{element.name_en} · Grupo {element.group} · Periodo {element.period} · Bloque {element.block || '—'}</small>
          </div>
        </div>

        <div class="modal-actions">
          <button class:active={isCompared} type="button" on:click={() => dispatch('compare', element.symbol)}>
            {isCompared ? 'En comparador' : 'Comparar'}
          </button>
          <button class="close-button" type="button" on:click={() => dispatch('close')} aria-label="Cerrar ficha">×</button>
        </div>
      </header>

      <nav class="modal-tabs master-tabs" aria-label="Secciones de la ficha maestra">
        <button class:active={activeTab === 'summary'} type="button" on:click={() => (activeTab = 'summary')}>Resumen</button>
        <button class:active={activeTab === 'atom'} type="button" on:click={() => (activeTab = 'atom')}>Átomo 3D</button>
        <button class:active={activeTab === 'properties'} type="button" on:click={() => (activeTab = 'properties')}>Propiedades</button>
        <button class:active={activeTab === 'isotopes'} type="button" on:click={() => (activeTab = 'isotopes')}>Isótopos</button>
        <button class:active={activeTab === 'spectrum'} type="button" on:click={() => (activeTab = 'spectrum')}>Espectro</button>
        <button class:active={activeTab === 'lines'} type="button" on:click={() => (activeTab = 'lines')}>Líneas</button>
        <button class:active={activeTab === 'levels'} type="button" on:click={() => (activeTab = 'levels')}>Niveles</button>
        <button class:active={activeTab === 'chemistry'} type="button" on:click={() => (activeTab = 'chemistry')}>Química</button>
        <button class:active={activeTab === 'context'} type="button" on:click={() => (activeTab = 'context')}>Contexto</button>
        <button class:active={activeTab === 'sources'} class:problem={hasNistProblem} type="button" on:click={() => (activeTab = 'sources')}>
          Fuentes{hasNistProblem ? ' · revisar' : ''}
        </button>
      </nav>

      <div class="modal-content">
        {#if dataError}
          <p class="empty-copy modal-data-error">{dataError}</p>
        {/if}

        {#if activeTab === 'summary'}
          <ElementPanel {element} {elementData} {loadingData} />
        {:else if activeTab === 'atom'}
          <AtomicModel3D {element} {elementData} />
        {:else if activeTab === 'properties'}
          {#if loadingData}
            <div class="modal-load-state"><span></span><p>Cargando propiedades de {element.name_es}…</p></div>
          {:else}
            {#each domainList(PROPERTY_IDS) as domain}<DataDomainTable {domain} />{/each}
            {#if !hasAnyDomain(PROPERTY_IDS)}<p class="empty-copy master-empty">No hay propiedades adicionales disponibles.</p>{/if}
          {/if}
        {:else if activeTab === 'isotopes'}
          {#if loadingData}
            <div class="modal-load-state"><span></span><p>Cargando isótopos de {element.name_es}…</p></div>
          {:else}
            <DataDomainTable domain={elementData?.domains.isotopes ?? null} />
            {#if !elementData?.domains.isotopes?.available}<p class="empty-copy master-empty">No hay datos isotópicos disponibles.</p>{/if}
          {/if}
        {:else if activeTab === 'spectrum'}
          <div class="mode-row">
            <div><p class="eyebrow">Modo de visualización</p><h3>Emisión / absorción</h3></div>
            <div class="segmented-control small">
              <button class:active={mode === 'emission'} type="button" on:click={() => (mode = 'emission')}>Emisión</button>
              <button class:active={mode === 'absorption'} type="button" on:click={() => (mode = 'absorption')}>Absorción</button>
            </div>
          </div>
          <SpectrumViewer lines={element.lines} {mode} title={`${element.name_es} (${element.symbol})`} />
        {:else if activeTab === 'lines'}
          <section class="modal-data-card spectral-lines-panel">
            <div class="section-title-row compact">
              <div><p class="eyebrow">Tabla técnica</p><h2>Líneas espectrales NIST</h2></div>
              <span class="range-pill">{element.lines.length.toLocaleString('es-ES')} líneas</span>
            </div>

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

            {#if element.lines.length}
              <div class="technical-table modal-table">
                <table>
                  <thead><tr><th>Línea</th><th>Especie</th><th>λ</th><th>Región</th><th>Intensidad</th><th>Nivel inferior</th><th>Nivel superior</th><th>ΔE</th><th>Transición</th></tr></thead>
                  <tbody>
                    {#each element.lines as line}
                      <tr class:featured={strongestLineIds.has(lineId(line))}>
                        <td>{line.label}</td><td>{line.species}</td><td>{formatNm(line.wavelength_nm)}</td>
                        <td>{wavelengthRegion(line.wavelength_nm)}</td><td>{line.intensity.toFixed(2)}</td>
                        <td>{formatEv(line.lower_level_ev)}</td><td>{formatEv(line.upper_level_ev)}</td>
                        <td>{formatEv(energyJump(line))}</td><td>{line.transition}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            {:else}
              <p class="empty-copy technical-empty">No hay líneas espectrales tabulares para mostrar.</p>
            {/if}
          </section>
        {:else if activeTab === 'levels'}
          {#if loadingData}
            <div class="modal-load-state"><span></span><p>Cargando niveles de {element.name_es}…</p></div>
          {:else}
            <DataDomainTable domain={elementData?.domains.nist_levels ?? null} />
            {#if !elementData?.domains.nist_levels?.available}<p class="empty-copy master-empty">No hay niveles NIST disponibles para este elemento.</p>{/if}
          {/if}
        {:else if activeTab === 'chemistry'}
          {#if loadingData}
            <div class="modal-load-state"><span></span><p>Cargando química de {element.name_es}…</p></div>
          {:else}
            {#each domainList(CHEMISTRY_IDS) as domain}<DataDomainTable {domain} />{/each}
            {#if !hasAnyDomain(CHEMISTRY_IDS)}<p class="empty-copy master-empty">No hay datos químicos o de materiales disponibles.</p>{/if}
          {/if}
        {:else if activeTab === 'context'}
          {#if loadingData}
            <div class="modal-load-state"><span></span><p>Cargando contexto de {element.name_es}…</p></div>
          {:else}
            {#each domainList(CONTEXT_IDS) as domain}<DataDomainTable {domain} />{/each}
            {#if !hasAnyDomain(CONTEXT_IDS)}<p class="empty-copy master-empty">Estos bloques todavía están pendientes.</p>{/if}
          {/if}
        {:else if activeTab === 'sources'}
          {#if loadingData}
            <div class="modal-load-state"><span></span><p>Cargando procedencia de {element.name_es}…</p></div>
          {:else}
            <section class="dataset-coverage-panel" aria-label="Cobertura local del elemento">
              <header>
                <div><p class="eyebrow">Información interna</p><h2>Cobertura del dataset local</h2></div>
                <strong>{availableDomains.length} archivos con datos</strong>
              </header>
              <div class="dataset-coverage-rows">
                {#each availableDomains as domain}
                  <div><span>{domain.label}</span><b>{domain.row_count.toLocaleString('es-ES')} registros</b></div>
                {/each}
              </div>
            </section>

            <DataDomainTable domain={elementData?.domains.sources ?? null} />
            <section class="modal-data-card nist-panel">
              <div class="section-title-row compact">
                <div><p class="eyebrow">Procedencia y validación</p><h2>Estado de los archivos NIST</h2></div>
                <span class="range-pill">{element.nist?.imported_line_count ?? 0} líneas interpretadas</span>
              </div>
              {#if hasNistProblem}
                <p class="nist-inline-warning">Alguno de los archivos NIST aún no tiene estructura tabular válida. Los demás datos de la ficha sí pueden utilizarse.</p>
              {/if}
              {#if element.nist}
                <div class="nist-status-grid">
                  {#each nistFiles as file}
                    <article class:problem={file.item.present && !file.item.table_like} class="nist-status-card">
                      <header><strong>{file.label}</strong><span>{statusLabel(file.item)}</span></header>
                      <dl>
                        <div><dt>Archivo</dt><dd>{file.item.file}</dd></div>
                        <div><dt>Ruta</dt><dd>{file.item.path || '—'}</dd></div>
                        <div><dt>Filas</dt><dd>{file.item.row_count.toLocaleString('es-ES')}</dd></div>
                        <div><dt>Columnas</dt><dd>{file.item.columns.length ? file.item.columns.slice(0, 8).join(', ') : '—'}</dd></div>
                      </dl>
                      <p>{file.item.notes}</p>
                    </article>
                  {/each}
                </div>
              {/if}
            </section>
          {/if}
        {/if}
      </div>
    </div>
  </div>
{/if}
