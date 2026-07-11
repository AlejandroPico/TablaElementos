<script lang="ts">
  import { createEventDispatcher, onMount, tick } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';

  type TableLayout = 'short' | 'opening' | 'long';
  type LayoutAnimationStage = 'spread' | 'series-in' | 'series-out' | 'collapse';
  type SeriesKind = '' | 'lanthanide' | 'actinide';

  interface GridPosition {
    column: number;
    row: number;
  }

  interface LayoutSnapshot {
    key: string;
    left: number;
    top: number;
    width: number;
    height: number;
    className: string;
    html: string;
    tagName: string;
    atomicNumber: number;
    group: number;
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
  let transitionOverlay: HTMLDivElement;

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
  let seriesFocus: SeriesKind = '';

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
    if (viewportElement.classList.contains('layout-animating')) return;
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
    if (viewportElement.classList.contains('layout-animating')) return;
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

  function isLanthanide(atomicNumber: number): boolean {
    return atomicNumber >= 57 && atomicNumber <= 71;
  }

  function isActinide(atomicNumber: number): boolean {
    return atomicNumber >= 89 && atomicNumber <= 103;
  }

  function isFocusedSeries(atomicNumber: number): boolean {
    return (
      (seriesFocus === 'lanthanide' && isLanthanide(atomicNumber)) ||
      (seriesFocus === 'actinide' && isActinide(atomicNumber))
    );
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

  function layoutNodes(): HTMLElement[] {
    return Array.from(gridElement?.querySelectorAll<HTMLElement>('[data-layout-key]') ?? []);
  }

  export function captureElementRects(): Record<string, LayoutSnapshot> {
    const snapshots: Record<string, LayoutSnapshot> = {};
    layoutNodes().forEach((node) => {
      const key = node.dataset.layoutKey;
      if (!key) return;
      const rect = node.getBoundingClientRect();
      snapshots[key] = {
        key,
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
        className: node.className,
        html: node.innerHTML,
        tagName: node.tagName.toLowerCase(),
        atomicNumber: Number(node.dataset.atomicNumber ?? 0),
        group: Number(node.dataset.group ?? 0)
      };
    });
    return snapshots;
  }

  function nodeFromSnapshot(snapshot: LayoutSnapshot): HTMLElement {
    const node = document.createElement(snapshot.tagName || 'div');
    node.className = snapshot.className;
    node.innerHTML = snapshot.html;
    return node;
  }

  function ghostDelay(stage: LayoutAnimationStage, atomicNumber: number, group: number): number {
    if (stage === 'series-in' || stage === 'series-out') {
      if (isLanthanide(atomicNumber)) return 45 + (atomicNumber - 57) * 13;
      if (isActinide(atomicNumber)) return 75 + (atomicNumber - 89) * 13;
      return 0;
    }
    if (stage === 'spread' && group > 2) return Math.min(80, Math.max(0, group - 3) * 5);
    if (stage === 'collapse' && group > 2) return Math.min(80, Math.max(0, 18 - group) * 5);
    return 0;
  }

  function ghostDuration(stage: LayoutAnimationStage, atomicNumber: number): number {
    if ((stage === 'series-in' || stage === 'series-out') && (isLanthanide(atomicNumber) || isActinide(atomicNumber))) {
      return 880;
    }
    return stage === 'spread' || stage === 'collapse' ? 790 : 540;
  }

  export async function animateLayoutFrom(
    previous: Record<string, LayoutSnapshot>,
    stage: LayoutAnimationStage
  ): Promise<void> {
    if (!gridElement || !viewportElement || !transitionOverlay) {
      await fitToViewport(false);
      return;
    }

    viewportElement.classList.add('layout-animating');
    stopCamera();

    try {
      await fitToViewport(false);
      await tick();

      if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

      const viewportRect = viewportElement.getBoundingClientRect();
      const currentNodes = new Map<string, HTMLElement>();
      layoutNodes().forEach((node) => {
        const key = node.dataset.layoutKey;
        if (key) currentNodes.set(key, node);
      });

      transitionOverlay.replaceChildren();
      const keys = new Set([...Object.keys(previous), ...currentNodes.keys()]);
      const animations: Animation[] = [];

      keys.forEach((key) => {
        const before = previous[key];
        const current = currentNodes.get(key);
        const currentRect = current?.getBoundingClientRect();
        if (!before && !currentRect) return;

        const start = before ?? {
          key,
          left: currentRect!.left,
          top: currentRect!.top,
          width: currentRect!.width,
          height: currentRect!.height,
          className: current?.className ?? '',
          html: current?.innerHTML ?? '',
          tagName: current?.tagName.toLowerCase() ?? 'div',
          atomicNumber: Number(current?.dataset.atomicNumber ?? 0),
          group: Number(current?.dataset.group ?? 0)
        };
        const end = currentRect ?? {
          left: start.left,
          top: start.top,
          width: start.width,
          height: start.height
        };

        const ghost = current
          ? (current.cloneNode(true) as HTMLElement)
          : nodeFromSnapshot(start);

        ghost.removeAttribute('style');
        ghost.removeAttribute('id');
        ghost.classList.add('layout-transition-ghost');
        ghost.querySelectorAll<HTMLElement>('button, [tabindex]').forEach((child) => {
          child.setAttribute('tabindex', '-1');
          child.setAttribute('aria-hidden', 'true');
        });

        const startLeft = start.left - viewportRect.left;
        const startTop = start.top - viewportRect.top;
        const endLeft = end.left - viewportRect.left;
        const endTop = end.top - viewportRect.top;
        const scaleX = end.width / Math.max(start.width, 0.0001);
        const scaleY = end.height / Math.max(start.height, 0.0001);

        Object.assign(ghost.style, {
          position: 'absolute',
          left: `${startLeft}px`,
          top: `${startTop}px`,
          width: `${start.width}px`,
          height: `${start.height}px`,
          margin: '0',
          transformOrigin: '0 0',
          pointerEvents: 'none',
          willChange: 'transform, opacity'
        });

        transitionOverlay.appendChild(ghost);

        const atomicNumber = Number(current?.dataset.atomicNumber ?? start.atomicNumber ?? 0);
        const group = Number(current?.dataset.group ?? start.group ?? 0);
        const isAppearing = !before && Boolean(currentRect);
        const isDisappearing = Boolean(before) && !currentRect;
        const delay = ghostDelay(stage, atomicNumber, group);
        const duration = ghostDuration(stage, atomicNumber);

        const fromOpacity = isAppearing ? 0 : 1;
        const toOpacity = isDisappearing ? 0 : 1;
        const fromTransform = isAppearing ? 'scale3d(0.86, 0.86, 1)' : 'translate3d(0, 0, 0) scale3d(1, 1, 1)';
        const toTransform = isDisappearing
          ? 'scale3d(0.86, 0.86, 1)'
          : `translate3d(${(endLeft - startLeft).toFixed(2)}px, ${(endTop - startTop).toFixed(2)}px, 0) scale3d(${scaleX.toFixed(5)}, ${scaleY.toFixed(5)}, 1)`;

        const animation = ghost.animate(
          [
            { transform: fromTransform, opacity: fromOpacity },
            { transform: toTransform, opacity: toOpacity }
          ],
          {
            duration,
            delay,
            easing: stage === 'series-in' || stage === 'series-out'
              ? 'cubic-bezier(0.18, 0.82, 0.2, 1)'
              : 'cubic-bezier(0.22, 1, 0.36, 1)',
            fill: 'both'
          }
        );
        animations.push(animation);
      });

      gridElement.classList.add('layout-live-hidden');
      transitionOverlay.classList.add('active');
      await Promise.allSettled(animations.map((animation) => animation.finished));
    } finally {
      gridElement.classList.remove('layout-live-hidden');
      transitionOverlay.classList.remove('active');
      transitionOverlay.replaceChildren();
      viewportElement.classList.remove('layout-animating');
    }
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
      transitionOverlay?.replaceChildren();
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
      class:series-focus-lanthanide={seriesFocus === 'lanthanide'}
      class:series-focus-actinide={seriesFocus === 'actinide'}
      style={`zoom:${renderBucket};--zoom:${renderBucket};--content-scale:${Math.pow(Math.max(committedZoom, 1), 0.36).toFixed(4)};`}
    >
      {#if layoutMode !== 'long'}
        <button
          class="series-placeholder lanthanide-placeholder"
          type="button"
          data-layout-key="placeholder-lanthanides"
          style="grid-column:3;grid-row:6;"
          aria-label="Resaltar lantánidos, elementos 57 a 71"
          on:pointerdown|stopPropagation
          on:mouseenter={() => (seriesFocus = 'lanthanide')}
          on:mouseleave={() => (seriesFocus = '')}
          on:focus={() => (seriesFocus = 'lanthanide')}
          on:blur={() => (seriesFocus = '')}
        >
          <strong>57–71</strong>
          <span>Lantánidos</span>
          <small>La–Lu · fila inferior</small>
        </button>
        <button
          class="series-placeholder actinide-placeholder"
          type="button"
          data-layout-key="placeholder-actinides"
          style="grid-column:3;grid-row:7;"
          aria-label="Resaltar actínidos, elementos 89 a 103"
          on:pointerdown|stopPropagation
          on:mouseenter={() => (seriesFocus = 'actinide')}
          on:mouseleave={() => (seriesFocus = '')}
          on:focus={() => (seriesFocus = 'actinide')}
          on:blur={() => (seriesFocus = '')}
        >
          <strong>89–103</strong>
          <span>Actínidos</span>
          <small>Ac–Lr · fila inferior</small>
        </button>
      {/if}

      {#each elements as element (element.symbol)}
        {@const position = positionFor(element)}
        <article
          class={`element-cell ${categoryClass(element.category)}`}
          class:active={selectedSymbol === element.symbol}
          class:series-related={isFocusedSeries(element.atomic_number)}
          class:series-unrelated={Boolean(seriesFocus) && !isFocusedSeries(element.atomic_number)}
          data-layout-key={`element-${element.symbol}`}
          data-element-symbol={element.symbol}
          data-atomic-number={element.atomic_number}
          data-group={element.group}
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

  <div bind:this={transitionOverlay} class="layout-transition-overlay" aria-hidden="true"></div>
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
    position: relative;
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

  .layout-animating {
    cursor: progress;
  }

  .layout-animating .periodic-pan {
    pointer-events: none;
  }
</style>
