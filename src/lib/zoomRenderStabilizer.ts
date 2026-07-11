export {};

let gridObserver: MutationObserver | null = null;
let viewportObserver: MutationObserver | null = null;
let documentObserver: MutationObserver | null = null;
let attachedGrid: HTMLElement | null = null;
let attachedViewport: HTMLElement | null = null;
let rasterFrame = 0;
let cleanupFrame = 0;
let repaintTimer = 0;

function pulseRaster(grid: HTMLElement): void {
  cancelAnimationFrame(rasterFrame);
  cancelAnimationFrame(cleanupFrame);
  window.clearTimeout(repaintTimer);

  const pan = grid.closest<HTMLElement>('.periodic-pan');
  grid.classList.remove('zoom-raster-refresh');
  pan?.classList.remove('zoom-raster-refresh');

  // Obliga al navegador a registrar el estado previo antes de volver a pintar.
  void grid.offsetWidth;

  grid.classList.add('zoom-raster-refresh');
  pan?.classList.add('zoom-raster-refresh');

  rasterFrame = requestAnimationFrame(() => {
    cleanupFrame = requestAnimationFrame(() => {
      grid.classList.remove('zoom-raster-refresh');
      pan?.classList.remove('zoom-raster-refresh');
    });
  });
}

function scheduleRasterRefresh(grid: HTMLElement, delay = 36): void {
  window.clearTimeout(repaintTimer);
  repaintTimer = window.setTimeout(() => pulseRaster(grid), delay);
}

function applyRenderBucket(grid: HTMLElement): void {
  const rawZoom = grid.style.zoom;
  const currentBucket = grid.style.getPropertyValue('--render-bucket-scale').trim();

  // PeriodicGrid publica cada escalón mediante la propiedad inline zoom. La hoja
  // zoom-stability.css impide que ese zoom altere el layout; aquí se traslada de
  // forma atómica a una escala visual centrada.
  if (rawZoom && rawZoom !== '1') {
    const parsed = Number.parseFloat(rawZoom);
    if (!Number.isFinite(parsed) || parsed <= 0) return;

    const normalized = parsed.toFixed(3);
    if (currentBucket !== normalized) {
      grid.style.setProperty('--render-bucket-scale', normalized);
      grid.dataset.renderBucket = normalized;
      scheduleRasterRefresh(grid, 0);
    }

    grid.style.zoom = '1';
    return;
  }

  if (!currentBucket) {
    grid.style.setProperty('--render-bucket-scale', '1.000');
    grid.dataset.renderBucket = '1.000';
  }
}

function attachViewport(viewport: HTMLElement): void {
  if (attachedViewport === viewport) return;

  viewportObserver?.disconnect();
  attachedViewport = viewport;
  viewportObserver = new MutationObserver(() => {
    if (!viewport.classList.contains('camera-moving') && attachedGrid) {
      // El repintado final sucede cuando la interpolación de cámara ha terminado,
      // no mientras las fichas están desplazándose.
      scheduleRasterRefresh(attachedGrid, 28);
    }
  });
  viewportObserver.observe(viewport, {
    attributes: true,
    attributeFilter: ['class']
  });
}

function attachToGrid(grid: HTMLElement): void {
  if (attachedGrid !== grid) {
    gridObserver?.disconnect();
    attachedGrid = grid;
    gridObserver = new MutationObserver(() => applyRenderBucket(grid));
    gridObserver.observe(grid, {
      attributes: true,
      attributeFilter: ['style']
    });
  }

  applyRenderBucket(grid);
  const viewport = grid.closest<HTMLElement>('.periodic-viewport');
  if (viewport) attachViewport(viewport);
}

function locateGrid(): void {
  const grid = document.querySelector<HTMLElement>('.absolute-periodic-grid');
  if (grid) attachToGrid(grid);
}

function startZoomRenderStabilizer(): void {
  locateGrid();
  documentObserver = new MutationObserver(locateGrid);
  documentObserver.observe(document.documentElement, {
    childList: true,
    subtree: true
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startZoomRenderStabilizer, { once: true });
} else {
  startZoomRenderStabilizer();
}

window.addEventListener('beforeunload', () => {
  cancelAnimationFrame(rasterFrame);
  cancelAnimationFrame(cleanupFrame);
  window.clearTimeout(repaintTimer);
  gridObserver?.disconnect();
  viewportObserver?.disconnect();
  documentObserver?.disconnect();
});
