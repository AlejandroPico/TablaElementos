<script lang="ts">
  import { tick } from 'svelte';
  import CompareElements from '../components/CompareElements.svelte';
  import ElementModal from '../components/ElementModal.svelte';
  import PeriodicGrid from '../components/PeriodicGrid.svelte';
  import ViewToolbar from '../components/ViewToolbar.svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';
  import { loadSpectraDataset, hydrateElements } from '../lib/dataLoader';

  type TableMode = 'short' | 'long';

  let elements: ElementWithLines[] = [];
  let selectedSymbol = '';
  let modalElement: ElementWithLines | null = null;
  let comparedSymbols: string[] = [];
  let loading = true;
  let errorMessage = '';
  let gridView: any;
  let zoomPercent = 100;
  let zoomLevel = 'Vista general';
  let softCells = true;
  let tableMode: TableMode = 'short';

  $: comparedElements = comparedSymbols
    .map((symbol) => elements.find((element) => element.symbol === symbol))
    .filter((element): element is ElementWithLines => Boolean(element));

  $: spectralLineCount = elements.reduce((total, element) => total + element.lines.length, 0);
  $: nistProblemCount = elements.reduce((total, element) => {
    if (!element.nist) return total;
    const files = [element.nist.espectro, element.nist.niveles];
    return total + files.filter((file) => file.present && !file.table_like).length;
  }, 0);

  async function init(): Promise<void> {
    try {
      const dataset = await loadSpectraDataset();
      elements = hydrateElements(dataset);
      selectedSymbol = elements[0]?.symbol ?? '';
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Error desconocido al cargar datos locales.';
    } finally {
      loading = false;
    }
  }

  function openElement(symbol: string): void {
    selectedSymbol = symbol;
    modalElement = elements.find((element) => element.symbol === symbol) ?? null;
  }

  function closeModal(): void {
    modalElement = null;
  }

  function toggleCompared(symbol: string): void {
    if (comparedSymbols.includes(symbol)) {
      removeCompared(symbol);
      return;
    }
    comparedSymbols = [...comparedSymbols, symbol];
  }

  function removeCompared(symbol: string): void {
    comparedSymbols = comparedSymbols.filter((item) => item !== symbol);
  }

  function clearCompared(): void {
    comparedSymbols = [];
  }

  async function applyTableMode(nextMode: TableMode): Promise<void> {
    tableMode = nextMode;
    await tick();
    gridView?.resetView();
  }

  function toggleTableMode(): void {
    const nextMode: TableMode = tableMode === 'short' ? 'long' : 'short';
    const transitionDocument = document as Document & {
      startViewTransition?: (callback: () => Promise<void>) => unknown;
    };

    if (transitionDocument.startViewTransition) {
      transitionDocument.startViewTransition(() => applyTableMode(nextMode));
      return;
    }

    void applyTableMode(nextMode);
  }

  init();
</script>

<svelte:head>
  <title>Tabla elementos</title>
</svelte:head>

<main class:with-comparator={comparedElements.length > 0} class:soft-cells={softCells} class="app-shell">
  {#if loading}
    <section class="state-card">
      <h2>Cargando dataset local…</h2>
    </section>
  {:else if errorMessage}
    <section class="state-card error">
      <h2>No se pudo iniciar la aplicación</h2>
      <p>{errorMessage}</p>
    </section>
  {:else}
    <PeriodicGrid
      bind:this={gridView}
      {elements}
      {selectedSymbol}
      {tableMode}
      on:select={(event) => openElement(event.detail)}
      on:zoomchange={(event) => {
        zoomPercent = event.detail.percent;
        zoomLevel = event.detail.level;
      }}
    />

    <ViewToolbar
      {zoomPercent}
      {zoomLevel}
      elementCount={elements.length}
      {spectralLineCount}
      {nistProblemCount}
      {softCells}
      {tableMode}
      on:zoomin={() => gridView?.zoomIn()}
      on:zoomout={() => gridView?.zoomOut()}
      on:reset={() => gridView?.resetView()}
      on:corners={() => (softCells = !softCells)}
      on:layout={toggleTableMode}
    />

    {#if comparedElements.length > 0}
      <aside class="comparison-drawer" aria-label="Comparador espectral">
        <CompareElements
          selected={comparedElements}
          on:remove={(event) => removeCompared(event.detail)}
          on:clear={clearCompared}
        />
      </aside>
    {/if}

    <ElementModal
      element={modalElement}
      {comparedSymbols}
      on:close={closeModal}
      on:compare={(event) => toggleCompared(event.detail)}
    />
  {/if}
</main>
