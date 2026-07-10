import type {
  ElementDataIndex,
  ElementDataPayload,
  ElementWithLines,
  SpectraDataset
} from './atomicTypes';

const elementDataCache = new Map<string, Promise<ElementDataPayload>>();

export async function loadSpectraDataset(): Promise<SpectraDataset> {
  const response = await fetch('./data/spectra.sample.json', { cache: 'no-store' });

  if (!response.ok) {
    throw new Error(`No se pudo cargar el dataset local: ${response.status} ${response.statusText}`);
  }

  return (await response.json()) as SpectraDataset;
}

export function hydrateElements(dataset: SpectraDataset): ElementWithLines[] {
  return dataset.elements.map((element) => ({
    ...element,
    lines: dataset.spectral_lines_by_element[element.symbol] ?? [],
    nist: dataset.nist_by_element?.[element.symbol],
    dataIndex: dataset.data_index_by_element?.[element.symbol]
  }));
}

export function loadElementData(symbol: string, index?: ElementDataIndex): Promise<ElementDataPayload> {
  const cached = elementDataCache.get(symbol);
  if (cached) return cached;

  const url = index?.data_url || `./data/elements/${symbol}.json`;
  const request = fetch(url, { cache: 'no-store' })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`No se pudieron cargar los datos de ${symbol}: ${response.status} ${response.statusText}`);
      }
      return (await response.json()) as ElementDataPayload;
    })
    .catch((error) => {
      elementDataCache.delete(symbol);
      throw error;
    });

  elementDataCache.set(symbol, request);
  return request;
}
