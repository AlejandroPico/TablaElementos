<script lang="ts">
  import { createEventDispatcher, onMount, tick } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';

  export type TableMode = 'short' | 'long';

  interface RectSnapshot {
    left: number;
    top: number;
    width: number;
    height: number;
  }

  export let elements: ElementWithLines[] = [];
  export let selectedSymbol = '';
  export let tableMode: TableMode = 'short';

  const MIN_ZOOM = 0.2;
  const MAX_ZOOM = 14;
  const CAMERA_ZOOM_TAU = 68;
  const CAMERA_PAN_TAU = 54;

  let viewportElement: HTMLDivElement;
  let panElement: HTMLDivElement;
  let gridElement: HTMLDivElement;

  let zoom = 1;
  let targetZoom = 1;
  let renderZoom = 1;
  let offsetX = 0;
  let offsetY = 0;
  let targetOffsetX = 0;
  let targetOffsetY = 0;

  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let dragOriginX = 0;
  let dragOriginY = 0;

  let cameraFrame = 0;
  let lastFrameTime = 0;
  let lastPublishedPercent = -1;
  let lastPublishedLevel = '';

  $: zoomClass = renderZoom >= 7.5 ? 'zoom-inspect' : renderZoom >= 3.2 ? 'zoom-deep' : renderZoom >= 1.6 ? 'zoom-medium' : 'zoom-base';
  $: contentScale = Math.pow(Math.max(renderZoom, 1), 0.36);

  const dispatch = createEventDispatcher<{
    select: string;
    zoomchange: { zoom: number; percent: number; level: string };
  }>();

  function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
  }

  function zoomLabel(value = zoom): string {
    if (value >= 7.5) return 'Inspección';
    if (value >= 3.2) return 'Ficha ampliada';
    if (value >= 1.6) return 'Datos intermedios';
    return 'Vista general';
  }

  function publishZoom(force = false): void {
    const percent = Math.round(zoom * 100);
    const level = zoomLabel();
    if (!force && percent === lastPublishedPercent && level === lastPublishedLevel) return;

    lastPublishedPercent = percent;
    lastPublishedLevel = level;
    dispatch('zoomchange', { zoom, percent, level });
  }

  function visualScale(): number {
    return zoom / Math.max(renderZoom, 0.0001);
  }

  function applyCameraTransform(): void {
    if (!panElement) return;
    const scale = visualScale();
    panElement.style.transform = `translate3d(calc(-50% + ${offsetX.toFixed(2)}px), calc(-50% + ${offsetY.toFixed(2)}px), 0) scale3d(${scale.toFixed(5)}, ${scale.toFixed(5)}, 1)`;
  }

  function commitRenderZoom(): void {
    renderZoom = zoom;

    if (gridElement) {
      gridElement.style.zoom = renderZoom.toFixed(5);
      gridElement.style.setProperty('--zoom', renderZoom.toFixed(5));
      gridElement.style.setProperty('--content-scale', Math.pow(Math.max(renderZoom, 1), 0.36).toFixed(4));
    }

    applyCameraTransform();
  }

  function stopCameraAnimation(): void {
    if (cameraFrame) {
      cancelAnimationFrame(cameraFrame);
      cameraFrame = 0;
    }
    lastFrameTime = 0;
    viewportElement?.classList.remove('camera-moving');
  }

  function cameraStep(timestamp: number): void {
    if (!lastFrameTime) lastFrameTime = timestamp;
    const delta = Math.min(48, Math.max(1, timestamp - lastFrameTime));
    lastFrameTime = timestamp;

    const zoomAlpha = 1 - Math.exp(-delta / CAMERA_ZOOM_TAU);
    const panAlpha = 1 - Math.exp(-delta / CAMERA_PAN_TAU);

    const zoomDistance = targetZoom - zoom;
    const xDistance = targetOffsetX - offsetX;
    const yDistance = targetOffsetY - offsetY;

    zoom += zoomDistance * zoomAlpha;
    offsetX += xDistance * panAlpha;
    offsetY += yDistance * panAlpha;
    applyCameraTransform();

    const settled =
      Math.abs(zoomDistance) < Math.max(0.0007, targetZoom * 0.00045) &&
      Math.abs(xDistance) < 0.08 &&
      Math.abs(yDistance) < 0.08;

    if (settled) {
      zoom = targetZoom;
      offsetX = targetOffsetX;
      offsetY = targetOffsetY;
      cameraFrame = 0;
      lastFrameTime = 0;
      commitRenderZoom();
      viewportElement?.classList.remove('camera-moving');
      publishZoom(true);
      return;
    }

    publishZoom();
    cameraFrame = requestAnimationFrame(cameraStep);
  }

  function ensureCameraAnimation(): void {
    if (cameraFrame) return;
    viewportElement?.classList.add('camera-moving');
    lastFrameTime = performance.now();
    cameraFrame = requestAnimationFrame(cameraStep);
  }

  function setCameraTarget(nextZoom: number, anchorX = 0, anchorY = 0): void {
    const clampedZoom = clamp(nextZoom, MIN_ZOOM, MAX_ZOOM);
    const previousTargetZoom = targetZoom;
    if (Math.abs(clampedZoom - previousTargetZoom) < 0.0001) return;

    const ratio = clampedZoom / previousTargetZoom;
    targetOffsetX = anchorX - (anchorX - targetOffsetX) * ratio;
    targetOffsetY = anchorY - (anchorY - targetOffsetY) * ratio;
    targetZoom = clampedZoom;
    ensureCameraAnimation();
  }

  function setCameraImmediate(nextZoom: number, nextOffsetX = 0, nextOffsetY = 0): void {
    stopCameraAnimation();
    zoom = clamp(nextZoom, MIN_ZOOM, MAX_ZOOM);
    targetZoom = zoom;
    offsetX = nextOffsetX;
    offsetY = nextOffsetY;
    targetOffsetX = nextOffsetX;
    targetOffsetY = nextOffsetY;
    commitRenderZoom();
    publishZoom(true);
  }

  function normalizedWheelDelta(event: WheelEvent): number {
    if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * 16;
    if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * window.innerHeight;
    return event.deltaY;
  }

  function handleWheel(event: WheelEvent): void {
    event.preventDefault();
    const rect = viewportElement.getBoundingClientRect();
    const cursorX = event.clientX - rect.left - rect.width / 2;
    const cursorY = event.clientY - rect.top - rect.height / 2;
    const factor = clamp(Math.exp(-normalizedWheelDelta(event) * 0.00135), 0.84, 1.19);
    setCameraTarget(targetZoom * factor, cursorX, cursorY);
  }

  function startDrag(event: PointerEvent): void {
    const target = event.target as HTMLElement;
    if (target.closest('.element-open-button, .series-placeholder')) return;

    stopCameraAnimation();
    isDragging = true;
    dragStartX = event.clientX;
    dragStartY = event.clientY;
    dragOriginX = targetOffsetX;
    dragOriginY = targetOffsetY;
    viewportElement.setPointerCapture(event.pointerId);
  }

  function dragCanvas(event: PointerEvent): void {
    if (!isDragging) return;
    offsetX = dragOriginX + event.clientX - dragStartX;
    offsetY = dragOriginY + event.clientY - dragStartY;
    targetOffsetX = offsetX;
    targetOffsetY = offsetY;
    applyCameraTransform();
  }

  function stopDrag(): void {
    isDragging = false;
  }

  function fitScale(): number {
    if (!viewportElement || !gridElement) return 1;

    const rect = gridElement.getBoundingClientRect();
    const baseWidth = rect.width / Math.max(zoom, 0.0001);
    const baseHeight = rect.height / Math.max(zoom, 0.0001);
    const availableWidth = Math.max(240, viewportElement.clientWidth - 64);
    const availableHeight = Math.max(220, viewportElement.clientHeight - 64);

    return clamp(Math.min(availableWidth / baseWidth, availableHeight / baseHeight, 1) * 0.965, MIN_ZOOM, 1);
  }

  export async function fitToViewport(animated = true): Promise<void> {
    await tick();
    const nextZoom = fitScale();

    targetOffsetX = 0;
    targetOffsetY = 0;

    if (animated) {
      targetZoom = nextZoom;
      ensureCameraAnimation();
      return;
    }

    setCameraImmediate(nextZoom, 0, 0);
  }

  export function zoomIn(): void {
    setCameraTarget(targetZoom * 1.18);
  }

  export function zoomOut(): void {
    setCameraTarget(targetZoom / 1.18);
  }

  export function resetView(): void {
    void fitToViewport(true);
  }

  export function captureElementRects(): Record<string, RectSnapshot> {
    const snapshots: Record<string, RectSnapshot> = {};
    if (!gridElement) return snapshots;

    gridElement.querySelectorAll<HTMLElement>('[data-element-symbol]').forEach((cell) => {
      const symbol = cell.dataset.elementSymbol;
      if (!symbol) return;
      const rect = cell.getBoundingClientRect();
      snapshots[symbol] = { left: rect.left, top: rect.top, width: rect.width, height: rect.height };
    });

    return snapshots;
  }

  export async function animateLayoutFrom(previous: Record<string, RectSnapshot>): Promise<void> {
    if (!gridElement || matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const animations: Animation[] = [];

    gridElement.querySelectorAll<HTMLElement>('[data-element-symbol]').forEach((cell) => {
      const symbol = cell.dataset.elementSymbol;
      const before = symbol ? previous[symbol] : undefined;
      if (!before) return;

      const after = cell.getBoundingClientRect();
      const deltaX = before.left - after.left;
      const deltaY = before.top - after.top;
      const atomicNumber = Number(cell.dataset.atomicNumber ?? '0');
      const isInnerSeries = (atomicNumber >= 57 && atomicNumber <= 71) || (atomicNumber >= 89 && atomicNumber <= 103);
      const delay = isInnerSeries ? 90 + ((atomicNumber - 57 + 118) % 15) * 9 : 0;

      cell.getAnimations().forEach((animation) => animation.cancel());
      const animation = cell.animate(
        [
          {
            transformOrigin: 'center',
            transform: `translate3d(${deltaX}px, ${deltaY}px, 0) scale3d(0.985, 0.985, 1)`,
            opacity: 0.92
          },
          {
            transformOrigin: 'center',
            transform: 'translate3d(0, 0, 0) scale3d(1, 1, 1)',
            opacity: 1
          }
        ],
        {
          duration: 920,
          delay,
          easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
          fill: 'both'
        }
      );
      animations.push(animation);
    });

    gridElement.querySelectorAll<HTMLElement>('.series-placeholder').forEach((item) => {
      const animation = item.animate(
        [
          { opacity: 0, transform: 'translate3d(0, -10px, 0) scale3d(0.94, 0.94, 1)' },
          { opacity: 1, transform: 'translate3d(0, 0, 0) scale3d(1, 1, 1)' }
        ],
        {
          duration: 520,
          delay: 180,
          easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
          fill: 'both'
        }
      );
      animations.push(animation);
    });

    await Promise.allSettled(animations.map((animation) => animation.finished));
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

  function shortPosition(element: ElementWithLines): { column: number; row: number } {
    if (element.atomic_number >= 57 && element.atomic_number <= 71) {
      return { column: element.atomic_number - 54, row: 8 };
    }
    if (element.atomic_number >= 89 && element.atomic_number <= 103) {
      return { column: element.atomic_number - 86, row: 9 };
    }
    return { column: element.group, row: element.period };
  }

  function longPosition(element: ElementWithLines): { column: number; row: number } {
    const z = element.atomic_number;
    if (z >= 55 && z <= 86) return { column: z - 54, row: 6 };
    if (z >= 87 && z <= 118) return { column: z - 86, row: 7 };
    return { column: element.group <= 2 ? element.group : element.group + 14, row: element.period };
  }

  function positionStyle(element: ElementWithLines): string {
    const position = tableMode === 'long' ? longPosition(element) : shortPosition(element);
    return `grid-column:${position.column};grid-row:${position.row};`;
  }

  onMount(() => {
    const resize = (): void => {
      void fitToViewport(false);
    };

    window.addEventListener('resize', resize);
    requestAnimationFrame(() => {
      applyCameraTransform();
      void fitToViewport(false);
    });

    return () => {
      window.removeEventListener('resize', resize);
      stopCameraAnimation();
    };
  });
</script>

<section class="periodic-card" aria-label="Tabla elementos">
  <div
    bind:this={viewportElement}
    class={`periodic-viewport ${zoomClass} table-${tableMode}`}
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
    <div bind:this={panElement} class="periodic-pan">
      <div
        bind:this={gridElement}
        class={`periodic-grid mode-${tableMode}`}
        style={`--zoom:${renderZoom.toFixed(5)};--content-scale:${contentScale.toFixed(4)};zoom:${renderZoom.toFixed(5)};`}
      >
        {#if tableMode === 'short'}
          <article class="series-placeholder lanthanide-placeholder" style="grid-column:3;grid-row:6;">
            <strong>57–71</strong><span>La–Lu</span><small>Fila inferior</small>
          </article>
          <article class="series-placeholder actinide-placeholder" style="grid-column:3;grid-row:7;">
            <strong>89–103</strong><span>Ac–Lr</span><small>Fila inferior</small>
          </article>
        {/if}

        {#each elements as element (element.symbol)}
          <article
            data-element-symbol={element.symbol}
            data-atomic-number={element.atomic_number}
            class:active={selectedSymbol === element.symbol}
            class={`element-cell ${categoryClass(element.category)} data-${dataState(element)}`}
            style={positionStyle(element)}
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
  </div>
</section>
