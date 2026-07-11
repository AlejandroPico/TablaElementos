let gridObserver: MutationObserver | null = null;
let documentObserver: MutationObserver | null = null;
let attachedGrid: HTMLElement | null = null;

function applyRenderBucket(grid: HTMLElement): void {
  const rawZoom = grid.style.zoom;
  const parsed = Number.parseFloat(rawZoom || '1');
  if (!Number.isFinite(parsed) || parsed <= 0) return;

  const normalized = parsed.toFixed(3);
  if (grid.style.getPropertyValue('--render-bucket-scale') !== normalized) {
    grid.style.setProperty('--render-bucket-scale', normalized);
    grid.dataset.renderBucket = normalized;
  }

  // CSS zoom modifica la geometría de layout y desplaza el centro del lienzo.
  // Conservamos el escalón de rasterizado como una escala interna sin layout.
  if (rawZoom && rawZoom !== '1') grid.style.zoom = '1';
}

function attachToGrid(grid: HTMLElement): void {
  if (attachedGrid === grid) {
    applyRenderBucket(grid);
    return;
  }

  gridObserver?.disconnect();
  attachedGrid = grid;
  applyRenderBucket(grid);

  gridObserver = new MutationObserver(() => applyRenderBucket(grid));
  gridObserver.observe(grid, {
    attributes: true,
    attributeFilter: ['style']
  });
}

function locateGrid(): void {
  const grid = document.querySelector<HTMLElement>('.absolute-periodic-grid');
  if (grid) attachToGrid(grid);
}

function start(): void {
  locateGrid();
  documentObserver = new MutationObserver(locateGrid);
  documentObserver.observe(document.documentElement, {
    childList: true,
    subtree: true
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start, { once: true });
} else {
  start();
}

window.addEventListener('beforeunload', () => {
  gridObserver?.disconnect();
  documentObserver?.disconnect();
});
