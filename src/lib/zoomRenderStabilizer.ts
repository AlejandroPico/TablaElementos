export {};

let gridObserver: MutationObserver | null = null;
let documentObserver: MutationObserver | null = null;
let attachedGrid: HTMLElement | null = null;

function applyRenderBucket(grid: HTMLElement): void {
  const rawZoom = grid.style.zoom;
  const currentBucket = grid.style.getPropertyValue('--render-bucket-scale').trim();

  // Cuando PeriodicGrid publica un nuevo escalón, lo trasladamos a una escala
  // visual interna y neutralizamos CSS zoom antes del siguiente pintado.
  if (rawZoom && rawZoom !== '1') {
    const parsed = Number.parseFloat(rawZoom);
    if (!Number.isFinite(parsed) || parsed <= 0) return;

    const normalized = parsed.toFixed(3);
    if (currentBucket !== normalized) {
      grid.style.setProperty('--render-bucket-scale', normalized);
      grid.dataset.renderBucket = normalized;
    }
    grid.style.zoom = '1';
    return;
  }

  // El valor 1 escrito por este mismo estabilizador no debe borrar el último
  // escalón real. Solo inicializamos cuando todavía no existe ninguno.
  if (!currentBucket) {
    grid.style.setProperty('--render-bucket-scale', '1.000');
    grid.dataset.renderBucket = '1.000';
  }
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
  gridObserver?.disconnect();
  documentObserver?.disconnect();
});
