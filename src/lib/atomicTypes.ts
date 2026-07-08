export type SpectrumMode = 'emission' | 'absorption';

export interface ElementRecord {
  symbol: string;
  name_es: string;
  name_en: string;
  atomic_number: number;
  group: number;
  period: number;
  category: string;
  summary: string;
}

export interface SpectralLine {
  element: string;
  species: string;
  wavelength_nm: number;
  intensity: number;
  kind: 'emission' | 'absorption';
  lower_level_ev: number;
  upper_level_ev: number;
  transition: string;
  label: string;
  source_note: string;
  visible: boolean;
  approximate_color: string;
  spectral_region: 'ultravioleta' | 'visible' | 'infrarrojo';
}

export interface SpectraDataset {
  metadata: {
    project: string;
    dataset: string;
    description: string;
    external_runtime_requests: boolean;
    visible_range_nm: [number, number];
    generated_by: string;
  };
  elements: ElementRecord[];
  spectral_lines_by_element: Record<string, SpectralLine[]>;
}

export interface ElementWithLines extends ElementRecord {
  lines: SpectralLine[];
}
