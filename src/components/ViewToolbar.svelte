<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let zoomPercent = 100;
  export let zoomLevel = 'Vista general';
  export let elementCount = 0;
  export let spectralLineCount = 0;
  export let nistProblemCount = 0;
  export let softCells = true;

  let infoOpen = false;

  const dispatch = createEventDispatcher<{
    zoomin: void;
    zoomout: void;
    reset: void;
    corners: void;
  }>();
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
    title="Restablecer vista"
    aria-label="Restablecer zoom y posición"
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
      <p><strong>Rueda:</strong> zoom centrado en el cursor.</p>
      <p><strong>Arrastre:</strong> desplaza el escenario cuando estás ampliado.</p>
      <p><strong>Doble clic:</strong> restaura la vista general.</p>
      <p>Al aumentar el zoom aparecen categoría, grupo, periodo, cobertura de datos y resumen del elemento.</p>
    </div>
  </aside>
{/if}
