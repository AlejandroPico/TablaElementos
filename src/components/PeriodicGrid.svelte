<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';

  export let elements: ElementWithLines[] = [];
  export let selectedSymbol = '';

  const MIN_ZOOM = 0.82;
  const MAX_ZOOM = 3.2;

  let zoom = 1;
  let offsetX = 0;
  let offsetY = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let dragOriginX = 0;
  let dragOriginY = 0;

  $: zoomClass = zoom >= 2.15 ? 'zoom-deep' : zoom >= 1.45 ? 'zoom-medium' : 'zoom-base';

  const dispatch = createEventDispatcher<{
    select: string;
  }>();

  function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
  }

  function handleWheel(event: WheelEvent): void {
    event.preventDefault();

    const viewport = event.currentTarget as HTMLElement;
    const rect = viewport.getBoundingClientRect();
    const previousZoom = zoom;
    const direction = event.deltaY > 0 ? -1 : 1;
    const nextZoom = clamp(zoom * (direction > 0 ? 1.12 : 0.88), MIN_ZOOM, MAX_ZOOM);

    if (nextZoom === previousZoom) {
      return;
    }

    const cursorX = event.clientX - rect.left - rect.width / 2;
    const cursorY = event.clientY - rect.top - rect.height / 2;
    const ratio = nextZoom / previousZoom;

    offsetX = cursorX - (cursorX - offsetX) * ratio;
    offsetY = cursorY - (cursorY - offsetY) * ratio;
    zoom = Number(nextZoom.toFixed(3));

    if (zoom <= 1.01) {
      offsetX = 0;
      offsetY = 0;
    }
  }

  function startDrag(event: PointerEvent): void {
    const target = event.target as HTMLElement;
    if (target.closest('.element-open-button')) {
      return;
    }

    isDragging = true;
    dragStartX = event.clientX;
    dragStartY = event.clientY;
    dragOriginX = offsetX;
    dragOriginY = offsetY;
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function dragCanvas(event: PointerEvent): void {
    if (!isDragging) {
      return;
    }

    offsetX = dragOriginX + event.clientX - dragStartX;
    offsetY = dragOriginY + event.clientY - dragStartY;
  }

  function stopDrag(): void {
    isDragging = false;
  }

  function resetView(): void {
    zoom = 1;
    offsetX = 0;
    offsetY = 0;
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

<section class="periodic-card" aria-label="Tabla elementos">
  <div
    class={`periodic-viewport ${zoomClass}`}
    role="application"
    aria-label="Canvas interactivo de la tabla periódica"
    on:wheel={handleWheel}
    on:pointerdown={startDrag}
    on:pointermove={dragCanvas}
    on:pointerup={stopDrag}
    on:pointerleave={stopDrag}
    on:dblclick={resetView}
  >
    <div
      class="periodic-grid"
      style={`transform: translate(${offsetX.toFixed(1)}px, ${offsetY.toFixed(1)}px) scale(${zoom});`}
    >
      {#each elements as element}
        <article
          class:active={selectedSymbol === element.symbol}
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
            <span class="element-detail detail-medium">{element.category}</span>
            <span class="element-detail detail-deep">{element.lines.length} líneas espectrales</span>
          </button>
        </article>
      {/each}
    </div>
  </div>
</section>
