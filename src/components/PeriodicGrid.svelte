<script lang="ts">
  import { createEventDispatcher, onMount, tick } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';

  type TableLayout = 'short' | 'opening' | 'long';
  type LayoutAnimationStage = 'spread' | 'series-in' | 'series-out' | 'collapse';

  interface RectSnapshot {
    left: number;
    top: number;
    width: number;
    height: number;
  }

  interface GridPosition {
    column: number;
    row: number;
  }

  export let elements: ElementWithLines[] = [];
  export let selectedSymbol = '';
  export let layoutMode: TableLayout = 'short';

  const MIN_ZOOM = 0.18;
  const MAX_ZOOM = 14;
  const DRAG_THRESHOLD_PX = 5;
  const CAMERA_TAU_MS = 78;
  const RENDER_STEP = 0.5;

  let viewportElement: HTMLDivElement;
  let panElement: HTMLDivElement;
  let gridElement: HTMLDivElement;

  let zoom = 1;
  let targetZoom = 1;
  let offsetX = 0;
  let offsetY = 0;
  let targetOffsetX = 0;
  let targetOffsetY = 0;
  let renderBucket = 1;
  let committedZoom = 1;

  let cameraFrame = 0;
  let lastFrameTime = 0;
  let cameraResolvers: Array<() => void> = [];

  let isPointerDown = false;
  let dragActivated = false;
  let activePointerId = -1;
  let dragStartX = 0;
  let dragStartY = 0;
  let dragOriginX = 0;
  let dragOriginY = 0;
  let pressedSymbol = '';
  let suppressClickUntil = 0;

  $: zoomClass =
    committedZoom >= 7.5
      ? 'zoom-inspect'
      : committedZoom >= 3.2
        ? 'zoom-deep'
        : committedZoom >= 1.6
          ? 'zoom-medium'
          : 'zoom-base';

  const dispatch = createEventDispatcher<{
    select: string;
    zoomchange: { zoom: number; percent: number; level: string };
  }>();

  function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
  }

  function categoryClass(category: string): string {
    const normalized = category
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();

    const classes: Record<string, string> = {
      'no metal': 'no-metal',
      'gas noble': 'gas-noble',
      'metal alcalino': 'metal-alcalino',
      'metal alcalinoterreo': 'metal-alcalinoterreo',
      'metal de transicion': 'metal-transicion',
      metaloide: 'metaloide',
      halogeno: 'halogeno',
      'metal post-transicion': 'metal-post-transicion',
      lantanido: 'lantanido',
      actinido: 'actinido',
      desconocido: 'desconocido'
    };

    return classes[normalized] ?? normalized.replace(/\s+/g, '-');
  }

  function zoomLabel(value = zoom): string {
    if (value >= 7.5) return 'Inspección';
    if (value >= 3.2) return 'Ficha ampliada';
    if (value >= 1.6) return 'Datos intermedios';
    return 'Vista general';
  }

  function publishZoom(): void {
    dispatch('zoomchange', {
      zoom,
      percent: Math.round(zoom * 100),
      level: zoomLabel()
    });
  }

  function bucketFor(value: number): number {
    return clamp(Math.round(value / RENDER_STEP) * RENDER_STEP, 0.5, MAX_ZOOM);
  }

  function setRenderBucket(nextBucket: number): void {
    if (Math.abs(nextBucket - renderBucket) < 0.001) return;
    renderBucket = nextBucket;

    if (gridElement) {
      gridElement.style.zoom = renderBucket.toFixed(2);
      gridElement.style.setProperty('--zoom', renderBucket.toFixed(2));
    }
  }

  function updateCommittedDetailLevel(): void {
    committedZoom = zoom;
    gridElement?.style.setProperty(
      '--content-scale',
      Math.pow(Math.max(committedZoom, 1), 0.36).toFixed(4)
    );
  }

  function applyCamera(): void {
    if (!panElement) return;
    const compositorScale = zoom / Math.max(renderBucket, 0.0001);
    panElement.style.transform =
      `translate3d(calc(-50% + ${offsetX.toFixed(2)}px), ` +
      `calc(-50% + ${offsetY.toFixed(2)}px), 0) ` +
      `scale3d(${compositorScale.toFixed(5)}, ${compositorScale.toFixed(5)}, 1)`;
  }

  function resolveCameraPromises(): void {
    const resolvers = cameraResolvers;
    cameraResolvers = [];
    resolvers.forEach((resolve) => resolve());
  }

  function waitForCamera(): Promise<void> {
    if (!cameraFrame) return Promise.resolve();
    return new Promise((resolve) => cameraResolvers.push(resolve));
  }

  function stopCamera(): void {
    if (cameraFrame) cancelAnimationFrame(cameraFrame);
    cameraFrame = 0;
    lastFrameTime = 0;
    viewportElement?.classList.remove('camera-moving');
    resolveCameraPromises();
  }

  function cameraStep(timestamp: number): void {
    if (!lastFrameTime) lastFrameTime = timestamp;
    const delta = Math.min(40, Math.max(1, timestamp - lastFrameTime));
    lastFrameTime = timestamp;
    const alpha = 1 - Math.exp(-delta / CAMERA_TAU_MS);

    zoom += (targetZoom - zoom) * alpha;
    offsetX += (targetOffsetX - offsetX) * alpha;
    offsetY += (targetOffsetY - offsetY) * alpha;

    const nextBucket = bucketFor(zoom);
    if (Math.abs(nextBucket - renderBucket) >= 0.001) setRenderBucket(nextBucket);
    applyCamera();

    const settled =
      Math.abs(targetZoom - zoom) < Math.max(0.0005, targetZoom * 0.00035) &&
      Math.abs(targetOffsetX - offsetX) < 0.08 &&
      Math.abs(targetOffsetY - offsetY) < 0.08;

    if (settled) {
      zoom = targetZoom;
      offsetX = targetOffsetX;
      offsetY = targetOffsetY;
      setRenderBucket(bucketFor(zoom));
      applyCamera();
      updateCommittedDetailLevel();
      publishZoom();
      cameraFrame = 0;
      lastFrameTime = 0;
      viewportElement?.classList.remove('camera-moving');
      resolveCameraPromises();
      return;
    }

    publishZoom();
    cameraFrame = requestAnimationFrame(cameraStep);
  }

  function ensureCamera(): void {
    if (cameraFrame) return;
    viewportElement?.classList.add('camera-moving');
    lastFrameTime = 0;
    cameraFrame = requestAnimationFrame(cameraStep);
  }

  function setCameraTarget(nextZoom: number, anchorX = 0, anchorY = 0): void {
    const clamped = clamp(nextZoom, MIN_ZOOM, MAX_ZOOM);
    const previous = targetZoom;
    if (Math.abs(clamped - previous) < 0.00001) return;

    const ratio = clamped / previous;
    targetOffsetX = anchorX - (anchorX - targetOffsetX) * ratio;
    targetOffsetY = anchorY - (anchorY - targetOffsetY) * ratio;
    targetZoom = clamped;
    ensureCamera();
  }

  function setCameraImmediate(nextZoom: number, nextX = 0, nextY = 0): void {
    stopCamera();
    zoom = clamp(nextZoom, MIN_ZOOM, MAX_ZOOM);
    targetZoom = zoom;
    offsetX = nextX;
    offsetY = nextY;
    targetOffsetX = nextX;
    targetOffsetY = nextY;
    setRenderBucket(bucketFor(zoom));
    applyCamera();
    updateCommittedDetailLevel();
    publishZoom();
  }

  function normalizedWheelDelta(event: WheelEvent): number {
    if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * 16;
    if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * innerHeight;
    return event.deltaY;
  }

  function handleWheel(event: WheelEvent): void {
    event.preventDefault();
    const rect = viewportElement.getBoundingClientRect();
    const anchorX = event.clientX - rect.left - rect.width / 2;
    const anchorY = event.clientY - rect.top - rect.height / 2;
    const factor = clamp(Math.exp(-normalizedWheelDelta(event) * 0.00125), 0.82, 1.22);
    setCameraTarget(targetZoom * factor, anchorX, anchorY);
  }

  function symbolFromTarget(target: EventTarget | null): string {
    if (!(target instanceof HTMLElement)) return '';
    return target.closest<HTMLElement>('[data-element-symbol]')?.dataset.elementSymbol ?? '';
  }

  function startDrag(event: PointerEvent): void {
    if (event.pointerType === 'mouse' && event.button !== 0) return;

    event.preventDefault();
    stopCamera();
    isPointerDown = true;
    dragActivated = false;
    activePointerId = event.pointerId;
    dragStartX = event.clientX;
    dragStartY = event.clientY;
    dragOriginX = offsetX;
    dragOriginY = offsetY;
    pressedSymbol = symbolFromTarget(event.target);
  }

  function dragCanvas(event: PointerEvent): void {
    if (!isPointerDown || event.pointerId !== activePointerId) return;

    const deltaX = event.clientX - dragStartX;
    const deltaY = event.clientY - dragStartY;

    if (!dragActivated && Math.hypot(deltaX, deltaY) < DRAG_THRESHOLD_PX) return;

    if (!dragActivated) {
      dragActivated = true;
      viewportElement.classList.add('dragging');
      viewportElement.setPointerCapture(event.pointerId);
    }

    event.preventDefault();
    offsetX = dragOriginX + deltaX;
    offsetY = dragOriginY + deltaY;
    targetOffsetX = offsetX;
    targetOffsetY = offsetY;
    applyCamera();
  }

  function finishDrag(event: PointerEvent): void {
    if (!isPointerDown || event.pointerId !== activePointerId) return;

    const wasDrag = dragActivated;
    const symbol = pressedSymbol;

    if (viewportElement.hasPointerCapture(event.pointerId)) {
      viewportElement.releasePointerCapture(event.pointerId);
    }

    viewportElement.classList.remove('dragging');
    isPointerDown = false;
    dragActivated = false;
    activePointerId = -1;
    pressedSymbol = '';

    if (wasDrag) {
      suppressClickUntil = performance.now() + 500;
      return;
    }

    if (symbol) {
      suppressClickUntil = performance.now() + 350;
      dispatch('select', symbol);
    }
  }

  function cancelDrag(event: PointerEvent): void {
    if (event.pointerId !== activePointerId) return;
    suppressClickUntil = performance.now() + 500;

    if (viewportElement.hasPointerCapture(event.pointerId)) {
      viewportElement.releasePointerCapture(event.pointerId);
    }

    viewportElement.classList.remove('dragging');
    isPointerDown = false;
    dragActivated = false;
    activePointerId = -1;
    pressedSymbol = '';
  }

  function openFromKeyboard(event: MouseEvent, symbol: string): void {
    if (event.detail !== 0 || performance.now() < suppressClickUntil) return;
    dispatch('select', symbol);
  }

  function handleDoubleClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    if (target.closest('[data-element-symbol]')) return;
    resetView();
  }

  function shortPosition(element: ElementWithLines): GridPosition {
    const z = element.atomic_number;
    if (z >= 57 && z <= 71) return { column: z - 54, row: 8 };
    if (z >= 89 && z <= 103) return { column: z - 86, row: 9 };
    return { column: Math.max(1, element.group), row: element.period };
  }

  function openingPosition(element: ElementWithLines): GridPosition {
    const z = element.atomic_number;
    if (z >= 57 && z <= 71) return { column: z - 54, row: 8 };
    if (z >= 89 && z <= 103) return { column: z - 86, row: 9 };
    const group = Math.max(1, element.group);
    return { column: group <= 2 ? group : group + 14, row: element.period };
  }

  function longPosition(element: ElementWithLines): GridPosition {
    const z = element.atomic_number;
    if (z >= 57 && z <= 71) return { column: z - 54, row: 6 };
    if (z >= 89 && z <= 103) return { column: z - 86, row: 7 };
    const group = Math.max(1, element.group);
    return { column: group <= 2 ? group : group + 14, row: element.period };
  }

  function positionFor(element: ElementWithLines): GridPosition {
    if (layoutMode === 'long') return longPosition(element);
    if (layoutMode === 'opening') return openingPosition(element);
    return shortPosition(element);
  }

  function fitScale(): number {
    if (!viewportElement || !gridElement) return 1;
    const rect = gridElement.getBoundingClientRect();
    const baseWidth = rect.width / Math.max(zoom, 0.0001);
    const baseHeight = rect.height / Math.max(zoom, 0.0001);
    const availableWidth = Math.max(240, viewportElement.clientWidth - 56);
    const availableHeight = Math.max(220, viewportElement.clientHeight - 56);
    return clamp(
      Math.min(availableWidth / baseWidth, availableHeight / baseHeight, 1) * 0.97,
      MIN_ZOOM,
      1
    );
  }

  export async function fitToViewport(animated = true): Promise<void> {
    await tick();
    const nextZoom = fitScale();
    targetOffsetX = 0;
    targetOffsetY = 0;

    if (!animated) {
      setCameraImmediate(nextZoom, 0, 0);
      return;
    }

    targetZoom = nextZoom;
    ensureCamera();
    await waitForCamera();
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
    gridElement
      ?.querySelectorAll<HTMLElement>('[data-element-symbol]')
      .forEach((cell) => {
        const symbol = cell.dataset.elementSymbol;
        if (!symbol) return;
        const rect = cell.getBoundingClientRect();
        snapshots[symbol] = {
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height
        };
      });
    return snapshots;
  }

  export async function animateLayoutFrom(
    previous: Record<string, RectSnapshot>,
    stage: LayoutAnimationStage
  ): Promise<void> {
    if (!gridElement || matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const animations: Animation[] = [];
    viewportElement.classList.add('layout-animating');

    gridElement
      .querySelectorAll<HTMLElement>('[data-element-symbol]')
      .forEach((cell) => {
        const symbol = cell.dataset.elementSymbol;
        const before = symbol ? previous[symbol] : undefined;
        if (!before) return;

        const atomicNumber = Number(cell.dataset.atomicNumber ?? 0);
        const innerSeries =
          (atomicNumber >= 57 && atomicNumber <= 71) ||
          (atomicNumber >= 89 && atomicNumber <= 103);

        if ((stage === 'spread' || stage === 'collapse') && innerSeries) return;
        if ((stage === 'series-in' || stage === 'series-out') && !innerSeries) return;

        const after = cell.getBoundingClientRect();
        const localScale = Math.max(zoom, 0.0001);
        const deltaX = (before.left - after.left) / localScale;
        const deltaY = (before.top - after.top) / localScale;
        const deltaScaleX = before.width / Math.max(after.width, 0.0001);
        const deltaScaleY = before.height / Math.max(after.height, 0.0001);

        if (Math.hypot(deltaX, deltaY) < 0.5) return;

        const seriesIndex =
          atomicNumber >= 57 && atomicNumber <= 71
            ? atomicNumber - 57
            : atomicNumber >= 89 && atomicNumber <= 103
              ? atomicNumber - 89
              : 0;

        const animation = cell.animate(
          [
            {
              transform: `translate3d(${deltaX}px, ${deltaY}px, 0) scale(${deltaScaleX}, ${deltaScaleY})`,
              opacity: 0.86
            },
            { transform: 'translate3d(0, 0, 0) scale(1, 1)', opacity: 1 }
          ],
          {
            duration: innerSeries ? 900 : 760,
            delay: innerSeries ? Math.min(210, seriesIndex * 14) : 0,
            easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
            fill: 'both'
          }
        );

        animations.push(animation);
      });

    await Promise.allSettled(animations.map((animation) => animation.finished));
    animations.forEach((animation) => animation.cancel());
    viewportElement.classList.remove('layout-animating');
  }

  onMount(() => {
    setRenderBucket(1);
    updateCommittedDetailLevel();

    const observer = new ResizeObserver(() => {
      if (!isPointerDown && !viewportElement.classList.contains('layout-animating')) {
        void fitToViewport(false);
      }
    });
    observer.observe(viewportElement);

    requestAnimationFrame(() => {
      void fitToViewport(false);
    });

    return () => {
      observer.disconnect();
      stopCamera();
    };
  });
</script>

<div
  bind:this={viewportElement}
  class={`periodic-viewport ${zoomClass}`}
  role="application"
  aria-label="Tabla periódica interactiva. Arrastra para desplazarte y usa la rueda para ampliar."
  on:wheel={handleWheel}
  on:pointerdown={startDrag}
  on:pointermove={dragCanvas}
  on:pointerup={finishDrag}
  on:pointercancel={cancelDrag}
  on:dblclick={handleDoubleClick}
>
  <div bind:this={panElement} class="periodic-pan">
    <div
      bind:this={gridElement}
      class={`periodic-grid mode-${layoutMode}`}
      style={`zoom:${renderBucket};--zoom:${renderBucket};--content-scale:${Math.pow(Math.max(committedZoom, 1), 0.36).toFixed(4)};`}
    >
      {#if layoutMode !== 'long'}
        <div
          class="series-placeholder lanthanide-placeholder"
          style="grid-column:3;grid-row:6;"
          aria-hidden="true"
        >
          <span class="series-tree-mark"></span>
          <strong>57–71</strong>
          <span>La–Lu</span>
          <small>Fila inferior</small>
        </div>
        <div
          class="series-placeholder actinide-placeholder"
          style="grid-column:3;grid-row:7;"
          aria-hidden="true"
        >
          <span class="series-tree-mark"></span>
          <strong>89–103</strong>
          <span>Ac–Lr</span>
          <small>Fila inferior</small>
        </div>
      {/if}

      {#each elements as element (element.symbol)}
        {@const position = positionFor(element)}
        <article
          class={`element-cell ${categoryClass(element.category)}`}
          class:active={selectedSymbol === element.symbol}
          data-element-symbol={element.symbol}
          data-atomic-number={element.atomic_number}
          style={`grid-column:${position.column};grid-row:${position.row};`}
        >
          <button
            class="element-open-button"
            type="button"
            aria-label={`Abrir ficha de ${element.name_es}`}
            on:click={(event) => openFromKeyboard(event, element.symbol)}
            on:dragstart|preventDefault
          >
            <div class="cell-topline">
              <span class="atomic-number">{element.atomic_number}</span>
              <span class="cell-data-state">{element.dataIndex?.available_file_count ?? 0}</span>
            </div>
            <div class="element-core"><strong>{element.symbol}</strong></div>
            <span class="element-name">{element.name_es}</span>
            <span class="element-detail detail-medium">Grupo {element.group || '—'} · Periodo {element.period}</span>
            <span class="element-detail detail-deep">{element.category} · {element.lines.length} líneas</span>
            <span class="element-detail detail-inspect">{element.summary}</span>
          </button>
        </article>
      {/each}
    </div>
  </div>
</div>

<style>
  .periodic-grid.mode-short {
    grid-template-columns: repeat(18, var(--cell-size));
    grid-template-rows: repeat(9, var(--cell-size));
  }

  .periodic-grid.mode-opening {
    grid-template-columns: repeat(32, var(--cell-size));
    grid-template-rows: repeat(9, var(--cell-size));
  }

  .periodic-grid.mode-long {
    grid-template-columns: repeat(32, var(--cell-size));
    grid-template-rows: repeat(7, var(--cell-size));
  }

  .periodic-viewport,
  .periodic-viewport * {
    user-select: none;
    -webkit-user-select: none;
  }

  .periodic-viewport {
    touch-action: none;
    cursor: grab;
  }

  .periodic-viewport.dragging {
    cursor: grabbing;
  }

  .periodic-viewport.dragging .element-open-button {
    pointer-events: none;
  }

  .element-cell {
    transform-origin: center center;
  }

  .layout-animating .element-cell {
    pointer-events: none;
  }
</style>
