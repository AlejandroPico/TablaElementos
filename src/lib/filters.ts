import type { ElementWithLines, SpectralLine } from './atomicTypes';

export function getStrongestLines(lines: SpectralLine[], limit = 4): SpectralLine[] {
  return [...lines].sort((a, b) => b.intensity - a.intensity).slice(0, limit);
}

export function getElementsByQuery(elements: ElementWithLines[], query: string): ElementWithLines[] {
  const normalizedQuery = query.trim().toLocaleLowerCase('es');

  if (!normalizedQuery) {
    return elements;
  }

  return elements.filter((element) => {
    const haystack = [
      element.symbol,
      element.name_es,
      element.name_en,
      element.category,
      String(element.atomic_number)
    ]
      .join(' ')
      .toLocaleLowerCase('es');

    return haystack.includes(normalizedQuery);
  });
}

export function countVisibleLines(lines: SpectralLine[]): number {
  return lines.filter((line) => line.visible).length;
}
