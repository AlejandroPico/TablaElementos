import type { ElementWithLines, SpectraDataset } from './atomicTypes';

export async function loadSpectraDataset(): Promise<SpectraDataset> {
  const response = await fetch('./data/spectra.sample.json');

  if (!response.ok) {
    throw new Error(`No se pudo cargar el dataset local: ${response.status} ${response.statusText}`);
  }

  return (await response.json()) as SpectraDataset;
}

export function hydrateElements(dataset: SpectraDataset): ElementWithLines[] {
  return dataset.elements.map((element) => ({
    ...element,
    lines: dataset.spectral_lines_by_element[element.symbol] ?? []
  }));
}
