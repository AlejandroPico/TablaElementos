<script lang="ts">
  import CompareElements from '../components/CompareElements.svelte';
  import ElementPanel from '../components/ElementPanel.svelte';
  import EnergyLevels from '../components/EnergyLevels.svelte';
  import PeriodicGrid from '../components/PeriodicGrid.svelte';
  import SpectrumViewer from '../components/SpectrumViewer.svelte';
  import Toolbar from '../components/Toolbar.svelte';
  import type { ElementWithLines, SpectraDataset, SpectrumMode } from '../lib/atomicTypes';
  import { loadSpectraDataset, hydrateElements } from '../lib/dataLoader';
  import { getElementsByQuery } from '../lib/filters';

  let dataset: SpectraDataset | null = null;
  let elements: ElementWithLines[] = [];
  let selectedSymbol = 'H';
  let comparedSymbols: string[] = ['H', 'Na', 'Hg'];
  let mode: SpectrumMode = 'emission';
  let query = '';
  let loading = true;
  let errorMessage = '';

  $: filteredElements = getElementsByQuery(elements, query);
  $: selectedElement = elements.find((element) => element.symbol === selectedSymbol) ?? elements[0] ?? null;
  $: comparedElements = comparedSymbols
    .map((symbol) => elements.find((element) => element.symbol === symbol))
    .filter((element): element is ElementWithLines => Boolean(element));

  async function init(): Promise<void> {
    try {
      dataset = await loadSpectraDataset();
      elements = hydrateElements(dataset);
      selectedSymbol = elements[0]?.symbol ?? 'H';
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Error desconocido al cargar datos locales.';
    } finally {
      loading = false;
    }
  }

  function selectElement(symbol: string): void {
    selectedSymbol = symbol;
  }

  function toggleCompared(symbol: string): void {
    if (comparedSymbols.includes(symbol)) {
      comparedSymbols = comparedSymbols.filter((item) => item !== symbol);
      return;
    }

    comparedSymbols = [...comparedSymbols, symbol].slice(-4);
  }

  init();
</script>

<svelte:head>
  <title>Espectros Atómicos · V1</title>
</svelte:head>

<main class="app-shell">
  <section class="hero">
    <div class="hero-copy">
      <p class="eyebrow">Laboratorio espectroscópico estático</p>
      <h1>Espectros Atómicos</h1>
      <p>
        Cada elemento deja una huella de luz. Explora líneas de emisión, absorción, longitudes de onda,
        colores aproximados y transiciones electrónicas desde datos locales del repositorio.
      </p>
    </div>

    <div class="hero-panel">
      <span>Sin servidor</span>
      <strong>GitHub Pages + Actions</strong>
      <small>Python genera los datos. Svelte, TypeScript y D3 los convierten en una interfaz visual.</small>
    </div>
  </section>

  {#if loading}
    <section class="state-card">
      <h2>Cargando dataset local…</h2>
      <p>La aplicación está leyendo el JSON publicado en <code>public/data/</code>.</p>
    </section>
  {:else if errorMessage}
    <section class="state-card error">
      <h2>No se pudo iniciar la aplicación</h2>
      <p>{errorMessage}</p>
    </section>
  {:else}
    <Toolbar {mode} {query} on:mode={(event) => (mode = event.detail)} on:query={(event) => (query = event.detail)} />

    <div class="workspace">
      <div class="left-column">
        <PeriodicGrid
          elements={filteredElements}
          {selectedSymbol}
          {comparedSymbols}
          on:select={(event) => selectElement(event.detail)}
          on:compare={(event) => toggleCompared(event.detail)}
        />

        <CompareElements selected={comparedElements} />
      </div>

      <div class="center-column">
        <SpectrumViewer
          lines={selectedElement?.lines ?? []}
          {mode}
          title={selectedElement ? `${selectedElement.name_es} (${selectedElement.symbol})` : 'Espectro'}
        />

        <EnergyLevels lines={selectedElement?.lines ?? []} />
      </div>

      <ElementPanel element={selectedElement} />
    </div>
  {/if}
</main>
