<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';

  export let elements: ElementWithLines[] = [];
  export let selectedSymbol = '';

  const MIN_ZOOM = 0.9;
  const MAX_ZOOM = 14;

  let zoom = 1;
  let offsetX = 0;
  let offsetY = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let dragOriginX = 0;
  let dragOriginY = 0;

  $: zoomClass = zoom >= 7.5 ? 'zoom-inspect' : zoom >= 3.2 ? 'zoom-deep' : zoom >= 1.6 ? 'zoom-medium' : 'zoom-base';

  const dispatch = createEventDispatcher<{
    select: string;
    zoomchange: { zoom: number; percent: number; level: string };
  }>();

  function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
  }

  function zoomLabel(): string {
    if (zoom >= 7.5) return 'Inspección';
    if (zoom >= 3.2) return 'Ficha ampliada';
    if (zoom >= 1.6) return 'Datos intermedios';
    return 'Vista general';
  }

  function publishZoom(): void {
    dispatch('zoomchange', {
      zoom,
      percent: Math.round(zoom * 100),
      level: zoomLabel()
    });
  }

  function applyZoom(nextValue: number, anchorX = 0, anchorY = 0): void {
    const previousZoom = zoom;
    const nextZoom = clamp(nextValue, MIN_ZOOM, MAX_ZOOM);
    if (nextZoom === previousZoom) return;

    const ratio = nextZoom / previousZoom;
    offsetX = anchorX - (anchorX - offsetX) * ratio;
    offsetY = anchorY - (anchorY - offsetY) * ratio;
    zoom = Number(nextZoom.toFixed(3));

    if (zoom <= 1.01) {
      offsetX = 0;
      offsetY = 0;
    }

    publishZoom();
  }

  function handleWheel(event: WheelEvent): void {
    event.preventDefault();
    const viewport = event.currentTarget as HTMLElement;
    const rect = viewport.getBoundingClientRect();
    const cursorX = event.clientX - rect.left - rect.width / 2;
    const cursorY = event.clientY - rect.top - rect.height / 2;
    applyZoom(zoom * (event.deltaY > 0 ? 0.84 : 1.18), cursorX, cursorY);
  }

  function startDrag(event: PointerEvent): void {
    const target = event.target as HTMLElement;
    if (target.closest('.element-open-button')) return;

    isDragging = true;
    dragStartX = event.clientX;
    dragStartY = event.clientY;
    dragOriginX = offsetX;
    dragOriginY = offsetY;
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function dragCanvas(event: PointerEvent): void {
    if (!isDragging) return;
    offsetX = dragOriginX + event.clientX - dragStartX;
    offsetY = dragOriginY + event.clientY - dragStartY;
  }

  function stopDrag(): void {
    isDragging = false;
  }

  export function zoomIn(): void {
    applyZoom(zoom * 1.22);
  }

  export function zoomOut(): void {
    applyZoom(zoom * 0.82);
  }

  export function resetView(): void {
    zoom = 1;
    offsetX = 0;
    offsetY = 0;
    publishZoom();
  }

  function categoryClass(category: string): string {
    return category
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, '-')
      .replace(/^metal-de-transicion$/, 'metal-transicion')
      .toLowerCase();
  }

  function dataState(element: ElementWithLines): 'ready' | 'review' | 'empty' {
    if (element.lines.length > 0) return 'ready';
    if (
      element.nist &&
      ((element.nist.espectro.present && !element.nist.espectro.table_like) ||
        (element.nist.niveles.present && !element.nist.niveles.table_like))
    ) {
      return 'review';
    }
    return 'empty';
  }

  function dataLabel(element: ElementWithLines): string {
    const state = dataState(element);
    if (state === 'ready') return `${element.lines.length} líneas`;
    if (state === 'review') return 'NIST · revisar';
    return 'Datos pendientes';
  }

  onMount(publishZoom);
</script>

<section class="periodic-card" aria-label="Tabla elementos">
  <div
    class={`periodic-viewport ${zoomClass}`}
    role="application"
    aria-label="Escenario interactivo de la tabla periódica"
    on:wheel={handleWheel}
    on:pointerdown={startDrag}
    on:pointermove={dragCanvas}
    on:pointerup={stopDrag}
    on:pointercancel={stopDrag}
    on:pointerleave={stopDrag}
    on:dblclick={resetView}
  >
    <div
      class="periodic-grid"
      style={`--zoom:${zoom}; transform: translate(${offsetX.toFixed(1)}px, ${offsetY.toFixed(1)}px) scale(${zoom});`}
    >
      {#each elements as element}
        <article
          class:active={selectedSymbol === element.symbol}
          class={`element-cell ${categoryClass(element.category)} data-${dataState(element)}`}
          style={`grid-column:${element.group};grid-row:${element.period};`}
          title={`${element.name_es} (${element.symbol})`}
        >
          <button
            class="element-open-button"
            type="button"
            on:click={() => dispatch('select', element.symbol)}
            aria-label={`Abrir ficha maestra de ${element.name_es}`}
          >
            <div class="cell-topline">
              <span class="atomic-number">{element.atomic_number}</span>
              <span class="cell-data-state" title={dataLabel(element)}>{dataLabel(element)}</span>
            </div>

            <div class="element-core">
              <strong>{element.symbol}</strong>
              <span class="element-name">{element.name_es}</span>
            </div>

            <div class="element-metrics detail-medium">
              <span><small>Grupo</small><b>{element.group}</b></span>
              <span><small>Periodo</small><b>{element.period}</b></span>
              <span><small>Categoría</small><b>{element.category}</b></span>
            </div>

            <div class="element-coverage detail-deep">
              <span>Identidad</span>
              <span class:ready={element.lines.length > 0}>Espectro</span>
              <span class:warning={dataState(element) === 'review'}>NIST</span>
              <span>Ficha maestra</span>
            </div>

            <p class="element-summary detail-inspect">{element.summary}</p>
          </button>
        </article>
      {/each}
    </div>
  </div>
</section>
