<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';
  import { countVisibleLines } from '../lib/filters';

  export let elements: ElementWithLines[] = [];
  export let selectedSymbol = '';
  export let comparedSymbols: string[] = [];

  const dispatch = createEventDispatcher<{
    select: string;
    compare: string;
  }>();

  function handleCompare(event: MouseEvent, symbol: string): void {
    event.stopPropagation();
    dispatch('compare', symbol);
  }
</script>

<section class="periodic-card" aria-label="Tabla periódica de muestra">
  <div class="periodic-header">
    <div>
      <p class="eyebrow">Muestra V1</p>
      <h2>Elementos disponibles</h2>
    </div>
    <span>{elements.length} elementos</span>
  </div>

  <div class="periodic-grid">
    {#each elements as element}
      <button
        class:active={selectedSymbol === element.symbol}
        class:compared={comparedSymbols.includes(element.symbol)}
        class="element-cell category-{element.category.replaceAll(' ', '-')}"
        style={`grid-column:${element.group};grid-row:${element.period};`}
        type="button"
        on:click={() => dispatch('select', element.symbol)}
        aria-label={`Seleccionar ${element.name_es}`}
      >
        <span class="atomic-number">{element.atomic_number}</span>
        <strong>{element.symbol}</strong>
        <small>{element.name_es}</small>
        <em>{countVisibleLines(element.lines)} visibles</em>
        <span class="compare-dot" on:click={(event) => handleCompare(event, element.symbol)} title="Añadir o quitar del comparador">
          +
        </span>
      </button>
    {/each}
  </div>

  <p class="periodic-note">
    Esta tabla todavía es una muestra reducida. La arquitectura ya permite incorporar los 118 elementos y datasets
    mucho más grandes sin cambiar el modelo visual base.
  </p>
</section>
