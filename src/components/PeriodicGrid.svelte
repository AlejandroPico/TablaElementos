<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';

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

  function categoryClass(category: string): string {
    return category
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, '-')
      .replace(/^metal-de-transicion$/, 'metal-transicion')
      .toLowerCase();
  }
</script>

<section class="periodic-card" aria-label="Tabla periódica de espectros atómicos">
  <div class="periodic-grid">
    {#each elements as element}
      <article
        class:active={selectedSymbol === element.symbol}
        class:compared={comparedSymbols.includes(element.symbol)}
        class={`element-cell ${categoryClass(element.category)}`}
        style={`grid-column:${element.group};grid-row:${element.period};`}
        title={`${element.name_es} (${element.symbol})`}
      >
        <button
          class="element-open-button"
          type="button"
          on:click={() => dispatch('select', element.symbol)}
          aria-label={`Abrir ficha de ${element.name_es}`}
        >
          <span class="atomic-number">{element.atomic_number}</span>
          <strong>{element.symbol}</strong>
          <span class="element-name">{element.name_es}</span>
        </button>

        <button
          class="compare-dot"
          type="button"
          on:click={(event) => handleCompare(event, element.symbol)}
          title="Añadir o quitar del comparador"
          aria-label={`Añadir o quitar ${element.name_es} del comparador`}
        >
          {comparedSymbols.includes(element.symbol) ? '−' : '+'}
        </button>
      </article>
    {/each}
  </div>
</section>
