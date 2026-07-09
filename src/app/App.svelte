<script lang="ts">
  import CompareElements from '../components/CompareElements.svelte';
  import ElementModal from '../components/ElementModal.svelte';
  import PeriodicGrid from '../components/PeriodicGrid.svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';
  import { loadSpectraDataset, hydrateElements } from '../lib/dataLoader';

  let elements: ElementWithLines[] = [];
  let selectedSymbol = '';
  let modalElement: ElementWithLines | null = null;
  let comparedSymbols: string[] = [];
  let loading = true;
  let errorMessage = '';

  $: comparedElements = comparedSymbols
    .map((symbol) => elements.find((element) => element.symbol === symbol))
    .filter((element): element is ElementWithLines => Boolean(element));

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

  init();
</script>

<svelte:head>
  <title>Tabla elementos</title>
</svelte:head>

<main class:with-comparator={comparedElements.length > 0} class="app-shell">
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
    <PeriodicGrid {elements} {selectedSymbol} on:select={(event) => openElement(event.detail)} />

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
