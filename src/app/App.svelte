<script lang="ts">
  import { onMount, tick } from 'svelte';
  import CompareElements from '../components/CompareElements.svelte';
  import ElementModal from '../components/ElementModal.svelte';
  import PeriodicGrid from '../components/PeriodicGrid.svelte';
  import ViewToolbar from '../components/ViewToolbar.svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';
  import { loadSpectraDataset, hydrateElements } from '../lib/dataLoader';

  type TableMode = 'short' | 'long';
  type TableLayout = 'short' | 'opening' | 'long';
  type LayoutAnimationStage = 'spread' | 'series-in' | 'series-out' | 'collapse';
  type ThemeMode = 'auto' | 'light' | 'dark';
  type ResolvedTheme = 'light' | 'dark';

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
  let layoutMode: TableLayout = 'short';
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

  function pause(milliseconds: number): Promise<void> {
    return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
  }

  function nextFrame(): Promise<void> {
    return new Promise((resolve) => requestAnimationFrame(() => resolve()));
  }

  async function runLayoutStage(
    nextLayout: TableLayout,
    stage: LayoutAnimationStage,
    settleDelay = 90
  ): Promise<void> {
    const previousRects = gridView?.captureElementRects?.() ?? {};
    layoutMode = nextLayout;
    await tick();
    await nextFrame();

    await Promise.resolve(gridView?.animateLayoutFrom?.(previousRects, stage));
    await pause(settleDelay);
    await Promise.resolve(gridView?.fitToViewport?.(true));
  }

  async function toggleTableMode(): Promise<void> {
    if (layoutBusy) return;
    layoutBusy = true;

    try {
      if (tableMode === 'short') {
        tableMode = 'long';
        await runLayoutStage('opening', 'spread', 130);
        await pause(110);
        await runLayoutStage('long', 'series-in', 70);
      } else {
        tableMode = 'short';
        await runLayoutStage('opening', 'series-out', 100);
        await pause(110);
        await runLayoutStage('short', 'collapse', 70);
      }
    } finally {
      layoutMode = tableMode;
      window.setTimeout(() => {
        layoutBusy = false;
      }, 120);
    }
  }

  function resolveAutomaticTheme(): ResolvedTheme {
    const hour = new Date().getHours();
    const nightByClock = hour >= 20 || hour < 7;
    return systemTheme?.matches || nightByClock ? 'dark' : 'light';
  }

  function applyTheme(): void {
    resolvedTheme = themeMode === 'auto' ? resolveAutomaticTheme() : themeMode;
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.dataset.themeMode = themeMode;
  }

  function cycleTheme(): void {
    themeMode = themeMode === 'auto' ? 'light' : themeMode === 'light' ? 'dark' : 'auto';
    try {
      localStorage.setItem('tabla-elementos-theme', themeMode);
    } catch (_) {
      // La aplicación puede funcionar aunque el navegador bloquee almacenamiento local.
    }
    applyTheme();
  }

  onMount(() => {
    try {
      const savedTheme = localStorage.getItem('tabla-elementos-theme');
      if (savedTheme === 'auto' || savedTheme === 'light' || savedTheme === 'dark') themeMode = savedTheme;
    } catch (_) {
      themeMode = 'auto';
    }

    systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
    const refreshTheme = (): void => {
      if (themeMode === 'auto') applyTheme();
    };

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

<svelte:head>
  <title>Tabla elementos</title>
</svelte:head>

<main
  class:with-comparator={comparedElements.length > 0}
  class:soft-cells={softCells}
  class={`app-shell theme-${resolvedTheme}`}
>
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
      {layoutMode}
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
      {layoutBusy}
      {themeMode}
      on:zoomin={() => gridView?.zoomIn()}
      on:zoomout={() => gridView?.zoomOut()}
      on:reset={() => gridView?.resetView()}
      on:corners={() => (softCells = !softCells)}
      on:layout={toggleTableMode}
      on:theme={cycleTheme}
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
