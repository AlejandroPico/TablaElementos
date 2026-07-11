<script lang="ts">
  import { createEventDispatcher, onMount, tick } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';

  type PublicLayout = 'short' | 'long';
  type VisualLayout = 'short' | 'opening' | 'long';
  type LayoutAnimationStage = 'idle' | 'spread' | 'series-in' | 'series-out' | 'collapse';
  type SeriesFocus = '' | 'lanthanide' | 'actinide';

  interface GridPosition {
    column: number;
    row: number;
  }

  interface CameraTarget {
    zoom: number;
    x: number;
    y: number;
  }

  export let elements: ElementWithLines[] = [];
  export let selectedSymbol = '';
  export let layoutMode: PublicLayout = 'short';

  const MIN_ZOOM = 0.18;
  const MAX_ZOOM = 14;
  const DRAG_THRESHOLD_PX = 5;
  const CAMERA_TAU_MS = 78;
  const RENDER_STEP = 0.5;
  const MAX_COLUMNS = 32;
  const MAX_ROWS = 9;
  const SHORT_COLUMN_OFFSET = 7;

  let viewportElement: HTMLDivElement;
  let panElement: HTMLDivElement;
  let gridElement: HTMLDivElement;
  let cellProbe: HTMLSpanElement;
  let gapProbe: HTMLSpanElement;

  let visualLayout: VisualLayout = layoutMode;
  let stableLayout: PublicLayout = layoutMode;
  let animationStage: LayoutAnimationStage = 'idle';
  let layoutAnimating = false;
  let seriesFocus: SeriesFocus = '';

  let cellSizePx = 82;
  let gapPx = 6;

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

  $: canvasWidth = MAX_COLUMNS * cellSizePx + (MAX_COLUMNS - 1) * gapPx;
  $: canvasHeight = MAX_ROWS * cellSizePx + (MAX_ROWS - 1) * gapPx;

  $: if (!layoutAnimating && layoutMode !== stableLayout) {
    stableLayout = layoutMode;
    visualLayout = layoutMode;
    animationStage = 'idle';
    void tick().then(() => fitToViewport(false, layoutMode));
  }

  const dispatch = createEventDispatcher<{
    select: string;
    zoomchange: { zoom: number; percent: number; level: string };
  }>();

  function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
  }

  function pause(milliseconds: number): Promise<void> {
    return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
  }

  function nextFrame(): Promise<void> {
    return new Promise((resolve) => requestAnimationFrame(() => resolve()));
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

  function setCameraAbsolute(target: CameraTarget, animated: boolean): Promise<void> {
    if (!animated) {
      stopCamera();
      zoom = target.zoom;
      targetZoom = target.zoom;
      offsetX = target.x;
      offsetY = target.y;
      targetOffsetX = target.x;
      targetOffsetY = target.y;
      setRenderBucket(bucketFor(zoom));
      applyCamera();
      updateCommittedDetailLevel();
      publishZoom();
      return Promise.resolve();
    }

    targetZoom = target.zoom;
    targetOffsetX = target.x;
    targetOffsetY = target.y;
    ensureCamera();
    return waitForCamera();
  }

  function normalizedWheelDelta(event: WheelEvent): number {
    if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * 16;
    if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * innerHeight;
    return event.deltaY;
  }

  function handleWheel(event: WheelEvent): void {
    event.preventDefault();
    if (layoutAnimating) return;
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
    if (layoutAnimating) return;
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
    if (event.detail !== 0 || performance.now() < suppressClickUntil || layoutAnimating) return;
    dispatch('select', symbol);
  }

  function handleDoubleClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    if (target.closest('[data-element-symbol]') || layoutAnimating) return;
    resetView();
  }

  function isInnerSeries(atomicNumber: number): boolean {
    return (atomicNumber >= 57 && atomicNumber <= 71) || (atomicNumber >= 89 && atomicNumber <= 103);
  }

  function shortPosition(element: ElementWithLines): GridPosition {
    const atomicNumber = element.atomic_number;
    if (atomicNumber >= 57 && atomicNumber <= 71) {
      return { column: atomicNumber - 54 + SHORT_COLUMN_OFFSET, row: 8 };
    }
    if (atomicNumber >= 89 && atomicNumber <= 103) {
      return { column: atomicNumber - 86 + SHORT_COLUMN_OFFSET, row: 9 };
    }
    return { column: Math.max(1, element.group) + SHORT_COLUMN_OFFSET, row: element.period };
  }

  function openingPosition(element: ElementWithLines): GridPosition {
    const atomicNumber = element.atomic_number;
    if (atomicNumber >= 57 && atomicNumber <= 71) return { column: atomicNumber - 54, row: 8 };
    if (atomicNumber >= 89 && atomicNumber <= 103) return { column: atomicNumber - 86, row: 9 };
    const group = Math.max(1, element.group);
    return { column: group <= 2 ? group : group + 14, row: element.period };
  }

  function longPosition(element: ElementWithLines): GridPosition {
    const atomicNumber = element.atomic_number;
    if (atomicNumber >= 57 && atomicNumber <= 71) return { column: atomicNumber - 54, row: 6 };
    if (atomicNumber >= 89 && atomicNumber <= 103) return { column: atomicNumber - 86, row: 7 };
    const group = Math.max(1, element.group);
    return { column: group <= 2 ? group : group + 14, row: element.period };
  }

  function positionFor(element: ElementWithLines): GridPosition {
    if (visualLayout === 'long') return longPosition(element);
    if (visualLayout === 'opening') return openingPosition(element);
    return shortPosition(element);
  }

  function placeholderPosition(kind: SeriesFocus): GridPosition {
    const column = visualLayout === 'short' ? 3 + SHORT_COLUMN_OFFSET : 3;
    return { column, row: kind === 'lanthanide' ? 6 : 7 };
  }

  function positionTransform(position: GridPosition): string {
    const step = cellSizePx + gapPx;
    const x = (position.column - 1) * step;
    const y = (position.row - 1) * step;
    return `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
  }

  function layoutDelay(element: ElementWithLines): number {
    if (!layoutAnimating) return 0;
    const atomicNumber = element.atomic_number;

    if (animationStage === 'series-in' || animationStage === 'series-out') {
      if (!isInnerSeries(atomicNumber)) return 0;
      const index = atomicNumber <= 71 ? atomicNumber - 57 : atomicNumber - 89;
      return index * 13;
    }

    if (animationStage === 'spread' || animationStage === 'collapse') {
      if (isInnerSeries(atomicNumber)) return 55;
      const group = Math.max(1, element.group);
      if (group <= 2) return (2 - group) * 18;
      return Math.min(150, (group - 3) * 9);
    }

    return 0;
  }

  function layoutDuration(element: ElementWithLines): number {
    if (!layoutAnimating) return 0;
    return isInnerSeries(element.atomic_number) && (animationStage === 'series-in' || animationStage === 'series-out')
      ? 820
      : 720;
  }

  function stageBounds(stage: VisualLayout): { columns: number; rows: number; verticalCenterCorrection: number } {
    if (stage === 'short') return { columns: 18, rows: 9, verticalCenterCorrection: 0 };
    if (stage === 'opening') return { columns: 32, rows: 9, verticalCenterCorrection: 0 };
    return { columns: 32, rows: 7, verticalCenterCorrection: cellSizePx + gapPx };
  }

  function cameraTargetFor(stage: VisualLayout): CameraTarget {
    const bounds = stageBounds(stage);
    const logicalWidth = bounds.columns * cellSizePx + (bounds.columns - 1) * gapPx;
    const logicalHeight = bounds.rows * cellSizePx + (bounds.rows - 1) * gapPx;
    const availableWidth = Math.max(240, viewportElement.clientWidth - 56);
    const availableHeight = Math.max(220, viewportElement.clientHeight - 56);
    const nextZoom = clamp(
      Math.min(availableWidth / logicalWidth, availableHeight / logicalHeight, 1) * 0.97,
      MIN_ZOOM,
      1
    );

    return {
      zoom: nextZoom,
      x: 0,
      y: bounds.verticalCenterCorrection * nextZoom
    };
  }

  export async function fitToViewport(animated = true, stage: VisualLayout = visualLayout): Promise<void> {
    await tick();
    await setCameraAbsolute(cameraTargetFor(stage), animated);
  }

  export function zoomIn(): void {
    setCameraTarget(targetZoom * 1.18);
  }

  export function zoomOut(): void {
    setCameraTarget(targetZoom / 1.18);
  }

  export function resetView(): void {
    void fitToViewport(true, visualLayout);
  }

  async function setVisualStage(nextLayout: VisualLayout, nextStage: LayoutAnimationStage): Promise<void> {
    animationStage = nextStage;
    visualLayout = nextLayout;
    await tick();
    await nextFrame();
  }

  async function animateShortToLong(): Promise<void> {
    await setVisualStage('opening', 'spread');
    await Promise.all([
      pause(910),
      pause(170).then(() => fitToViewport(true, 'opening'))
    ]);

    await setVisualStage('long', 'series-in');
    await Promise.all([
      pause(1060),
      pause(120).then(() => fitToViewport(true, 'long'))
    ]);
  }

  async function animateLongToShort(): Promise<void> {
    await setVisualStage('opening', 'series-out');
    await Promise.all([
      pause(1060),
      pause(110).then(() => fitToViewport(true, 'opening'))
    ]);

    await setVisualStage('short', 'collapse');
    await Promise.all([
      pause(930),
      pause(170).then(() => fitToViewport(true, 'short'))
    ]);
  }

  export async function transitionTo(target: PublicLayout): Promise<void> {
    if (layoutAnimating || target === stableLayout) return;

    layoutAnimating = true;
    viewportElement.classList.add('layout-animating');
    stopCamera();

    try {
      if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
        stableLayout = target;
        visualLayout = target;
        animationStage = 'idle';
        await tick();
        await fitToViewport(false, target);
        return;
      }

      if (target === 'long') await animateShortToLong();
      else await animateLongToShort();

      stableLayout = target;
      visualLayout = target;
    } catch (error) {
      console.warn('[TablaElementos] La transición absoluta falló; se aplicará el diseño final.', error);
      stableLayout = target;
      visualLayout = target;
      await tick();
      await fitToViewport(false, target);
    } finally {
      animationStage = 'idle';
      layoutAnimating = false;
      viewportElement.classList.remove('layout-animating');
    }
  }

  function isFocusedSeries(atomicNumber: number): boolean {
    if (seriesFocus === 'lanthanide') return atomicNumber >= 57 && atomicNumber <= 71;
    if (seriesFocus === 'actinide') return atomicNumber >= 89 && atomicNumber <= 103;
    return false;
  }

  function measureGeometry(): void {
    const measuredCell = cellProbe?.offsetWidth ?? 0;
    const measuredGap = gapProbe?.offsetWidth ?? 0;
    if (measuredCell > 0) cellSizePx = measuredCell;
    if (measuredGap >= 0) gapPx = measuredGap;
  }

  onMount(() => {
    measureGeometry();
    setRenderBucket(1);
    updateCommittedDetailLevel();

    const observer = new ResizeObserver(() => {
      measureGeometry();
      if (!isPointerDown && !layoutAnimating) {
        void tick().then(() => fitToViewport(false, visualLayout));
      }
    });
    observer.observe(viewportElement);

    requestAnimationFrame(() => {
      measureGeometry();
      void fitToViewport(false, visualLayout);
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
  class:layout-animating={layoutAnimating}
  role="application"
  aria-label="Tabla periódica interactiva. Arrastra para desplazarte y usa la rueda para ampliar."
  on:wheel={handleWheel}
  on:pointerdown={startDrag}
  on:pointermove={dragCanvas}
  on:pointerup={finishDrag}
  on:pointercancel={cancelDrag}
  on:dblclick={handleDoubleClick}
>
  <div class="layout-metric-probes" aria-hidden="true">
    <span bind:this={cellProbe} class="layout-cell-probe"></span>
    <span bind:this={gapProbe} class="layout-gap-probe"></span>
  </div>

  <div bind:this={panElement} class="periodic-pan">
    <div
      bind:this={gridElement}
      class={`periodic-grid absolute-periodic-grid stage-${animationStage}`}
      class:series-focus-lanthanide={seriesFocus === 'lanthanide'}
      class:series-focus-actinide={seriesFocus === 'actinide'}
      style={`width:${canvasWidth}px;height:${canvasHeight}px;zoom:${renderBucket};--zoom:${renderBucket};--content-scale:${Math.pow(Math.max(committedZoom, 1), 0.36).toFixed(4)};`}
    >
      <div
        class="series-slot"
        style={`transform:${positionTransform(placeholderPosition('lanthanide'))};--layout-delay:40ms;--layout-duration:${layoutAnimating ? 690 : 0}ms;opacity:${visualLayout === 'long' ? 0 : 1};`}
      >
        <button
          class="series-placeholder lanthanide-placeholder"
          type="button"
          aria-label="Resaltar lantánidos, elementos 57 a 71"
          tabindex={visualLayout === 'long' ? -1 : 0}
          on:pointerdown|stopPropagation
          on:mouseenter={() => (seriesFocus = 'lanthanide')}
          on:mouseleave={() => (seriesFocus = '')}
          on:focus={() => (seriesFocus = 'lanthanide')}
          on:blur={() => (seriesFocus = '')}
        >
          <span class="series-range">57 - 71</span>
          <strong>Lantánidos</strong>
          <small>La - Lu</small>
        </button>
      </div>

      <div
        class="series-slot"
        style={`transform:${positionTransform(placeholderPosition('actinide'))};--layout-delay:65ms;--layout-duration:${layoutAnimating ? 690 : 0}ms;opacity:${visualLayout === 'long' ? 0 : 1};`}
      >
        <button
          class="series-placeholder actinide-placeholder"
          type="button"
          aria-label="Resaltar actínidos, elementos 89 a 103"
          tabindex={visualLayout === 'long' ? -1 : 0}
          on:pointerdown|stopPropagation
          on:mouseenter={() => (seriesFocus = 'actinide')}
          on:mouseleave={() => (seriesFocus = '')}
          on:focus={() => (seriesFocus = 'actinide')}
          on:blur={() => (seriesFocus = '')}
        >
          <span class="series-range">89 - 103</span>
          <strong>Actínidos</strong>
          <small>Ac - Lr</small>
        </button>
      </div>

      {#each elements as element (element.symbol)}
        {@const position = positionFor(element)}
        <div
          class="element-slot"
          style={`transform:${positionTransform(position)};--layout-delay:${layoutDelay(element)}ms;--layout-duration:${layoutDuration(element)}ms;`}
        >
          <article
            class={`element-cell ${categoryClass(element.category)}`}
            class:active={selectedSymbol === element.symbol}
            class:series-related={isFocusedSeries(element.atomic_number)}
            class:series-unrelated={Boolean(seriesFocus) && !isFocusedSeries(element.atomic_number)}
            data-element-symbol={element.symbol}
            data-atomic-number={element.atomic_number}
            data-group={element.group}
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
              </div>
              <div class="element-core">
                <strong>{element.symbol}</strong>
                <span class="element-name">{element.name_es}</span>
              </div>
            </button>
          </article>
        </div>
      {/each}
    </div>
  </div>
</div>
