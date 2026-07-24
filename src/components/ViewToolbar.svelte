<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import ElementFilterPanelV2 from './ElementFilterPanelV2.svelte';
  import PeriodicInfoGuideExpanded from './PeriodicInfoGuideExpanded.svelte';

  type TableMode = 'short' | 'long';
  type ThemeMode = 'auto' | 'light' | 'dark';
  type ResolvedTheme = 'light' | 'dark';

  export let zoomPercent = 100;
  export let zoomLevel = 'Vista general';
  export let elementCount = 0;
  export let spectralLineCount = 0;
  export let nistProblemCount = 0;
  export let tableMode: TableMode = 'short';
  export let layoutBusy = false;
  export let themeMode: ThemeMode = 'auto';
  export let resolvedTheme: ResolvedTheme = 'dark';

  let guideOpen = false;
  let internalInfoOpen = false;
  let filterOpen = false;
  let activeFilterCount = 0;
  let filterMatches = 0;

  const dispatch = createEventDispatcher<{
    zoomin: void;
    zoomout: void;
    reset: void;
    layout: void;
    theme: void;
  }>();

  function themeLabel(): string {
    if (themeMode === 'light') return 'Tema claro activo';
    if (themeMode === 'dark') return 'Tema oscuro activo';
    return `Tema automático activo · mostrando ${resolvedTheme === 'dark' ? 'oscuro' : 'claro'}`;
  }

  function handleFilterClick(): void {
    filterOpen = !filterOpen;
    guideOpen = false;
    internalInfoOpen = false;
  }

  function handleInfoClick(event: MouseEvent): void {
    filterOpen = false;
    if (event.altKey) {
      internalInfoOpen = !internalInfoOpen;
      guideOpen = false;
      return;
    }

    guideOpen = !guideOpen;
    internalInfoOpen = false;
  }

</script>

<div class="view-tools" aria-label="Herramientas de la tabla">
  <button
    class:active={tableMode === 'long'}
    class:busy={layoutBusy}
    class="view-tool-button layout-mode-button"
    type="button"
    disabled={layoutBusy}
    title={tableMode === 'short' ? 'Mostrar tabla larga de 32 columnas' : 'Mostrar tabla corta de 18 columnas'}
    aria-label={tableMode === 'short' ? 'Cambiar a tabla larga' : 'Cambiar a tabla corta'}
    on:click={() => dispatch('layout')}
  >
    <span class="layout-icon" aria-hidden="true">{tableMode === 'short' ? '18' : '32'}</span>
  </button>

  {#key `${themeMode}-${resolvedTheme}`}
    <button
      class="view-tool-button theme-mode-button"
      type="button"
      data-tooltip={themeLabel()}
      aria-label={themeLabel()}
      on:click={() => dispatch('theme')}
    >
      {#if themeMode === 'light'}
        <svg class="theme-svg" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="4.2"></circle>
          <path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6"></path>
        </svg>
      {:else if themeMode === 'dark'}
        <svg class="theme-svg" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M19.2 15.2A7.7 7.7 0 0 1 8.8 4.8 8.3 8.3 0 1 0 19.2 15.2Z"></path>
        </svg>
      {:else}
        <svg class="theme-svg theme-auto" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="8.2"></circle>
          <path class="theme-auto-fill" d="M12 3.8a8.2 8.2 0 0 0 0 16.4Z"></path>
          <path d="M12 3.8v16.4"></path>
        </svg>
      {/if}
    </button>
  {/key}

  <button
    class:active={filterOpen || activeFilterCount > 0}
    class="view-tool-button filter-tool-button"
    type="button"
    title={activeFilterCount ? `${activeFilterCount} criterios activos · ${filterMatches} coincidencias` : 'Abrir filtros científicos'}
    aria-label={activeFilterCount ? `Abrir filtros. ${activeFilterCount} criterios activos y ${filterMatches} elementos coincidentes.` : 'Abrir filtros científicos'}
    on:click={handleFilterClick}
  >
    <svg class="filter-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 5h18l-7 8v5.5l-4 2V13L3 5Z"></path>
    </svg>
    {#if activeFilterCount > 0}<span class="filter-count" aria-hidden="true">{activeFilterCount}</span>{/if}
  </button>

  <button
    class:active={guideOpen || internalInfoOpen}
    class="view-tool-button"
    type="button"
    title="Guía completa de la tabla. Alt + clic: diagnóstico interno."
    aria-label="Abrir guía de la tabla periódica. Alt más clic abre el diagnóstico interno."
    on:click={handleInfoClick}
  >
    <svg class="info-svg" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="9"></circle>
      <path d="M12 10v7"></path>
      <path d="M12 7h.01"></path>
    </svg>
  </button>

  <button
    class="view-zoom-hud zoom-reset-chip"
    type="button"
    title="Restablecer y encajar la tabla"
    aria-label={`Zoom ${zoomPercent} por ciento. ${zoomLevel}. Pulsar para restablecer la vista.`}
    on:click={() => dispatch('reset')}
  >
    <strong>{zoomPercent}%</strong>
    <span>{zoomLevel}</span>
  </button>
</div>

{#if internalInfoOpen}
  <aside class="view-info-popover internal-diagnostics" aria-label="Diagnóstico interno de Tabla elementos">
    <header>
      <div><p>Diagnóstico interno</p><strong>Vista científica progresiva</strong></div>
      <button type="button" aria-label="Cerrar diagnóstico" on:click={() => (internalInfoOpen = false)}>×</button>
    </header>

    <div class="view-info-stats">
      <div><span>Elementos</span><strong>{elementCount}</strong></div>
      <div><span>Líneas válidas</span><strong>{spectralLineCount}</strong></div>
      <div><span>CSV a revisar</span><strong>{nistProblemCount}</strong></div>
    </div>

    <div class="view-info-copy">
      <p><strong>Distribución:</strong> {tableMode === 'short' ? 'corta, 18 columnas' : 'larga, 32 columnas'}.</p>
      <p><strong>Tema:</strong> {themeLabel().toLowerCase()}.</p>
      <p><strong>Filtros:</strong> {activeFilterCount ? `${activeFilterCount} criterios; ${filterMatches} coincidencias` : 'ninguno'}.</p>
      <p><strong>Rueda:</strong> cámara GPU continua y centrada en el cursor.</p>
      <p><strong>Arrastre:</strong> desplaza el escenario, incluso comenzando sobre una ficha.</p>
      <p><strong>Doble clic o porcentaje:</strong> vuelve a encajar la tabla completa.</p>
    </div>
  </aside>
{/if}

<ElementFilterPanelV2
  open={filterOpen}
  on:close={() => (filterOpen = false)}
  on:change={(event) => {
    activeFilterCount = event.detail.active;
    filterMatches = event.detail.matches;
  }}
/>

<PeriodicInfoGuideExpanded open={guideOpen} on:close={() => (guideOpen = false)} />
