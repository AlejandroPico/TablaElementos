<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { SpectrumMode } from '../lib/atomicTypes';

  export let mode: SpectrumMode = 'emission';
  export let query = '';

  const dispatch = createEventDispatcher<{
    mode: SpectrumMode;
    query: string;
  }>();

  function setMode(nextMode: SpectrumMode): void {
    dispatch('mode', nextMode);
  }
</script>

<nav class="toolbar" aria-label="Herramientas principales">
  <div class="search-box">
    <span>Buscar</span>
    <input
      bind:value={query}
      on:input={() => dispatch('query', query)}
      placeholder="H, Na, hierro, gas noble..."
      type="search"
    />
  </div>

  <div class="segmented-control" aria-label="Modo de espectro">
    <button class:active={mode === 'emission'} type="button" on:click={() => setMode('emission')}>Emisión</button>
    <button class:active={mode === 'absorption'} type="button" on:click={() => setMode('absorption')}>Absorción</button>
  </div>
</nav>
