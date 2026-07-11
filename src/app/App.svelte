<script lang="ts">
  import { onMount } from 'svelte';
  import CompareElements from '../components/CompareElements.svelte';
  import ElementModal from '../components/ElementModal.svelte';
  import PeriodicGrid from '../components/PeriodicGrid.svelte';
  import ViewToolbar from '../components/ViewToolbar.svelte';
  import type { ComparisonScope, ElementWithLines } from '../lib/atomicTypes';
  import { loadSpectraDataset, hydrateElements } from '../lib/dataLoader';
  import { animatePeriodicLayout } from '../lib/layoutTransitionV4';

  type TableMode = 'short' | 'long';
  type ThemeMode = 'auto' | 'light' | 'dark';
  type ResolvedTheme = 'light' | 'dark';

  let elements: ElementWithLines[] = [];
  let selectedSymbol = '';
  let modalElement: ElementWithLines | null = null;
  let comparedSymbols: string[] = [];
  let comparisonScope: ComparisonScope = 'global';
  let loading = true;
  let errorMessage = '';
  let gridView: any;
  let zoomPercent = 100;
  let zoomLevel = 'Vista general';
  let tableMode: TableMode = 'short';
  let layoutBusy = false;
  let themeMode: ThemeMode = 'auto';
  let resolvedTheme: ResolvedTheme = 'dark';
  let systemTheme: MediaQueryList | null = null;
  let themeTimer = 0;

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

  function toggleCompared(detail: { symbol: string; scope: ComparisonScope }): void {
    comparisonScope = detail.scope;
    if (comparedSymbols.includes(detail.symbol)) {
      comparedSymbols = comparedSymbols.filter((symbol) => symbol !== detail.symbol);
      if (!comparedSymbols.length) comparisonScope = 'global';
      return;
    }
    comparedSymbols = [...comparedSymbols, detail.symbol];
  }

  function removeCompared(symbol: string): void {
    comparedSymbols = comparedSymbols.filter((item) => item !== symbol);
  }

  function clearCompared(): void {
    comparedSymbols = [];
    comparisonScope = 'global';
  }

  async function toggleTableMode(): Promise<void> {
    if (layoutBusy) return;

    const source = tableMode;
    const target: TableMode = source === 'short' ? 'long' : 'short';
    layoutBusy = true;

    try {
      await animatePeriodicLayout({
        source,
        target,
        fitToViewport: (animated, stage) => gridView?.fitToViewport?.(animated, stage)
      });
      tableMode = target;
    } catch (error) {
      console.warn('[TablaElementos] No se pudo completar la transición animada; se aplicará el modo final.', error);
      tableMode = target;
      await Promise.resolve(gridView?.fitToViewport?.(false, target));
    } finally {
      window.setTimeout(() => (layoutBusy = false), 120);
    }
  }

  function resolveAutomaticTheme(): ResolvedTheme {
    const hour = new Date().getHours();
    return systemTheme?.matches || hour >= 20 || hour < 7 ? 'dark' : 'light';
  }

  function applyTheme(): void {
    resolvedTheme = themeMode === 'auto' ? resolveAutomaticTheme() : themeMode;
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.dataset.themeMode = themeMode;
  }

  function cycleTheme(): void {
    themeMode = themeMode === 'auto' ? 'light' : themeMode === 'light' ? 'dark' : 'auto';
    try { localStorage.setItem('tabla-elementos-theme', themeMode); } catch (_) {}
    applyTheme();
  }

  onMount(() => {
    try {
      const savedTheme = localStorage.getItem('tabla-elementos-theme');
      if (savedTheme === 'auto' || savedTheme === 'light' || savedTheme === 'dark') themeMode = savedTheme;
    } catch (_) { themeMode = 'auto'; }

    systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
    const refreshTheme = (): void => { if (themeMode === 'auto') applyTheme(); };
    systemTheme.addEventListener('change', refreshTheme);
    themeTimer = window.setInterval(refreshTheme, 60_000);
    applyTheme();

    return () => {
      systemTheme?.removeEventListener('change', refreshTheme);
      window.clearInterval(themeTimer);
    };
  });

  init();
</script>

<svelte:head><title>Tabla elementos</title></svelte:head>

<main class:with-comparator={comparedElements.length > 0} class={`app-shell theme-${resolvedTheme}`}>
  {#if loading}
    <section class="state-card"><h2>Cargando dataset local…</h2></section>
  {:else if errorMessage}
    <section class="state-card error"><h2>No se pudo iniciar la aplicación</h2><p>{errorMessage}</p></section>
  {:else}
    <PeriodicGrid
      bind:this={gridView}
      {elements}
      {selectedSymbol}
      layoutMode={tableMode}
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
      {tableMode}
      {layoutBusy}
      {themeMode}
      {resolvedTheme}
      on:zoomin={() => gridView?.zoomIn()}
      on:zoomout={() => gridView?.zoomOut()}
      on:reset={() => gridView?.resetView()}
      on:layout={toggleTableMode}
      on:theme={cycleTheme}
    />

    {#if comparedElements.length > 0}
      <aside class="comparison-drawer" aria-label="Comparador de elementos">
        <CompareElements
          selected={comparedElements}
          scope={comparisonScope}
          on:scope={(event) => (comparisonScope = event.detail)}
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
