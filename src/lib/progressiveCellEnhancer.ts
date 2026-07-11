interface LightweightElementRecord {
  symbol: string;
  group: number;
  period: number;
  block?: string;
  category: string;
}

interface LightweightDataIndex {
  summary_values?: Record<string, string>;
}

interface LightweightDataset {
  elements?: LightweightElementRecord[];
  data_index_by_element?: Record<string, LightweightDataIndex>;
}

interface CellFacts {
  atomicMass: string;
  configuration: string;
  electronegativity: string;
  radius: string;
  ionization: string;
  affinity: string;
  state: string;
  density: string;
  thermal: string;
  coordinates: string;
  category: string;
}

let datasetPromise: Promise<LightweightDataset> | null = null;
let observer: MutationObserver | null = null;
let scheduledFrame = 0;

function datasetUrl(): string {
  return new URL('./data/spectra.sample.json', document.baseURI).toString();
}

function loadDataset(): Promise<LightweightDataset> {
  if (!datasetPromise) {
    datasetPromise = fetch(datasetUrl(), { cache: 'no-cache' }).then(async (response) => {
      if (!response.ok) throw new Error(`No se pudo cargar el índice progresivo (${response.status}).`);
      return (await response.json()) as LightweightDataset;
    });
  }
  return datasetPromise;
}

function clean(value: unknown): string {
  const text = String(value ?? '').trim();
  return text || '—';
}

function factsFor(
  element: LightweightElementRecord,
  index: LightweightDataIndex | undefined
): CellFacts {
  const values = index?.summary_values ?? {};
  return {
    atomicMass: clean(values.standard_atomic_weight || values.atomic_mass),
    configuration: clean(values.electron_configuration),
    electronegativity: clean(values.electronegativity),
    radius: clean(values.atomic_radius),
    ionization: clean(values.ionization_energy),
    affinity: clean(values.electron_affinity),
    state: clean(values.standard_state),
    density: clean(values.density),
    thermal: `${clean(values.melting_point)} / ${clean(values.boiling_point)}`,
    coordinates: `Grupo ${element.group || '—'} · Periodo ${element.period} · Bloque ${element.block || '—'}`,
    category: clean(element.category)
  };
}

function addFact(
  grid: HTMLElement,
  className: string,
  level: 'medium' | 'deep' | 'inspect',
  label: string,
  value: string
): void {
  const item = document.createElement('span');
  item.className = `cell-fact fact-${className} level-${level}`;
  item.title = `${label}: ${value}`;

  const caption = document.createElement('small');
  caption.textContent = label;
  const content = document.createElement('b');
  content.textContent = value;

  item.append(caption, content);
  grid.append(item);
}

function decorateCell(
  cell: HTMLElement,
  element: LightweightElementRecord,
  index: LightweightDataIndex | undefined
): void {
  const button = cell.querySelector<HTMLElement>('.element-open-button');
  if (!button || button.dataset.progressiveDecorated === '1') return;

  button.dataset.progressiveDecorated = '1';
  button.classList.add('progressive-element-button');

  button.querySelector('.cell-data-state')?.remove();
  button.querySelectorAll('.element-detail').forEach((node) => node.remove());

  const core = button.querySelector<HTMLElement>('.element-core');
  const name = button.querySelector<HTMLElement>('.element-name');
  if (core && name && name.parentElement !== core) core.append(name);

  const facts = factsFor(element, index);
  const grid = document.createElement('div');
  grid.className = 'cell-science-grid';
  grid.setAttribute('aria-hidden', 'true');

  addFact(grid, 'mass', 'medium', 'Masa atómica', facts.atomicMass);
  addFact(grid, 'state', 'medium', 'Estado', facts.state);

  addFact(grid, 'config', 'deep', 'Configuración', facts.configuration);
  addFact(grid, 'electronegativity', 'deep', 'Electronegatividad', facts.electronegativity);
  addFact(grid, 'radius', 'deep', 'Radio atómico', facts.radius);
  addFact(grid, 'density', 'deep', 'Densidad', facts.density);

  addFact(grid, 'ionization', 'inspect', 'Ionización', facts.ionization);
  addFact(grid, 'affinity', 'inspect', 'Afinidad electrónica', facts.affinity);
  addFact(grid, 'thermal', 'inspect', 'Fusión / ebullición', facts.thermal);
  addFact(grid, 'coordinates', 'inspect', 'Posición', facts.coordinates);
  addFact(grid, 'category', 'inspect', 'Familia', facts.category);

  button.append(grid);
}

async function decorateVisibleCells(): Promise<void> {
  const dataset = await loadDataset();
  const elements = new Map((dataset.elements ?? []).map((element) => [element.symbol, element]));
  const index = dataset.data_index_by_element ?? {};

  document.querySelectorAll<HTMLElement>('.element-cell[data-element-symbol]').forEach((cell) => {
    const symbol = cell.dataset.elementSymbol ?? '';
    const element = elements.get(symbol);
    if (element) decorateCell(cell, element, index[symbol]);
  });
}

function scheduleDecoration(): void {
  cancelAnimationFrame(scheduledFrame);
  scheduledFrame = requestAnimationFrame(() => {
    void decorateVisibleCells().catch((error) => {
      console.warn('[TablaElementos] No se pudo preparar la información progresiva.', error);
    });
  });
}

function start(): void {
  scheduleDecoration();
  observer = new MutationObserver(scheduleDecoration);
  observer.observe(document.documentElement, { childList: true, subtree: true });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start, { once: true });
} else {
  start();
}

window.addEventListener('beforeunload', () => {
  cancelAnimationFrame(scheduledFrame);
  observer?.disconnect();
});
