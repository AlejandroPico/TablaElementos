<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export type TableMode = 'short' | 'long';
  export type ThemeMode = 'auto' | 'light' | 'dark';

  export let zoomPercent = 100;
  export let zoomLevel = 'Vista general';
  export let elementCount = 0;
  export let spectralLineCount = 0;
  export let nistProblemCount = 0;
  export let softCells = true;
  export let tableMode: TableMode = 'short';
  export let layoutBusy = false;
  export let themeMode: ThemeMode = 'auto';

  let infoOpen = false;

  const dispatch = createEventDispatcher<{
    zoomin: void;
    zoomout: void;
    reset: void;
    corners: void;
    layout: void;
    theme: void;
  }>();

  function themeLabel(): string {
    if (themeMode === 'light') return 'Tema claro';
    if (themeMode === 'dark') return 'Tema oscuro';
    return 'Tema automático';
  }
</script>

<div class="view-tools" aria-label="Herramientas de la tabla">
  <button
    class:active={softCells}
    class="view-tool-button"
    type="button"
    title={softCells ? 'Usar celdas cuadradas' : 'Usar esquinas suaves'}
    aria-label={softCells ? 'Usar celdas cuadradas' : 'Usar esquinas suaves'}
    on:click={() => dispatch('corners')}
  >
    <span class="corners-icon" aria-hidden="true"></span>
  </button>

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

  <button
    class="view-tool-button theme-mode-button"
    type="button"
    title={`${themeLabel()}. Pulsar para cambiar.`}
    aria-label={`${themeLabel()}. Cambiar tema.`}
    on:click={() => dispatch('theme')}
  >
    <span class={`theme-icon ${themeMode}`} aria-hidden="true">{themeMode === 'auto' ? 'A' : ''}</span>
  </button>

  <button
    class:active={infoOpen}
    class="view-tool-button"
    type="button"
    title="Información de la vista"
    aria-label="Mostrar información de la vista"
    on:click={() => (infoOpen = !infoOpen)}
  >
    <span class="info-icon" aria-hidden="true">i</span>
  </button>

  <button
    class="view-tool-button"
    type="button"
    title="Restablecer y encajar la tabla"
    aria-label="Restablecer zoom, posición y encaje"
    on:click={() => dispatch('reset')}
  >
    <span class="reset-icon" aria-hidden="true">↺</span>
  </button>

  <div class="view-zoom-hud" aria-label="Control de zoom">
    <button type="button" aria-label="Alejar" on:click={() => dispatch('zoomout')}>−</button>
    <div>
      <strong>{zoomPercent}%</strong>
      <span>{zoomLevel}</span>
    </div>
    <button type="button" aria-label="Acercar" on:click={() => dispatch('zoomin')}>+</button>
  </div>
</div>

{#if infoOpen}
  <aside class="view-info-popover" aria-label="Información de Tabla elementos">
    <header>
      <div>
        <p>Tabla elementos</p>
        <strong>Vista científica progresiva</strong>
      </div>
      <button type="button" aria-label="Cerrar información" on:click={() => (infoOpen = false)}>×</button>
    </header>

    <div class="view-info-stats">
      <div><span>Elementos</span><strong>{elementCount}</strong></div>
      <div><span>Líneas válidas</span><strong>{spectralLineCount}</strong></div>
      <div><span>CSV a revisar</span><strong>{nistProblemCount}</strong></div>
    </div>

    <div class="view-info-copy">
      <p><strong>Distribución:</strong> {tableMode === 'short' ? 'corta, 18 columnas' : 'larga, 32 columnas'}.</p>
      <p><strong>Tema:</strong> {themeLabel().toLowerCase()}.</p>
      <p><strong>Rueda:</strong> cámara GPU continua y centrada en el cursor.</p>
      <p><strong>Arrastre:</strong> desplaza el escenario cuando estás ampliado.</p>
      <p><strong>Doble clic:</strong> vuelve a encajar la tabla completa.</p>
    </div>
  </aside>
{/if}
