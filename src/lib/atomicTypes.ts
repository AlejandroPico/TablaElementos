export type SpectrumMode = 'emission' | 'absorption';

export type ComparisonScope =
  | 'global'
  | 'summary'
  | 'atom'
  | 'properties'
  | 'isotopes'
  | 'spectrum'
  | 'lines'
  | 'levels'
  | 'chemistry'
  | 'context'
  | 'sources';

export interface ElementRecord {
  symbol: string;
  name_es: string;
  name_en: string;
  atomic_number: number;
  group: number;
  period: number;
  block?: string;
  category: string;
  summary: string;
  folder?: string;
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

export interface NistFileStatus {
  file: string;
  path: string;
  present: boolean;
  table_like: boolean;
  status: string;
  columns: string[];
  row_count: number;
  preview: string;
  notes: string;
}

export interface NistElementStatus {
  espectro: NistFileStatus;
  niveles: NistFileStatus;
  imported_line_count: number;
}

export type DataRow = Record<string, string>;

export interface ElementDataDomain {
  id: string;
  label: string;
  file: string;
  present: boolean;
  available: boolean;
  columns: string[];
  row_count: number;
  rows: DataRow[];
  error?: string;
}

export interface ElementDataPayload {
  symbol: string;
  atomic_number: number;
  folder: string;
  domains: Record<string, ElementDataDomain>;
}

export interface ElementDataIndex {
  data_url: string;
  available_domains: string[];
  domain_counts: Record<string, number>;
  available_file_count: number;
}

export interface SpectraDataset {
  metadata: {
    project: string;
    dataset: string;
    description: string;
    external_runtime_requests: boolean;
    visible_range_nm: [number, number];
    generated_by: string;
    source_layout?: string;
    nist_files_present?: number;
    nist_files_malformed_or_non_tabular?: number;
    nist_imported_spectral_lines?: number;
    element_data_strategy?: string;
  };
  elements: ElementRecord[];
  spectral_lines_by_element: Record<string, SpectralLine[]>;
  nist_by_element?: Record<string, NistElementStatus>;
  data_index_by_element?: Record<string, ElementDataIndex>;
}

export interface ElementWithLines extends ElementRecord {
  lines: SpectralLine[];
  nist?: NistElementStatus;
  dataIndex?: ElementDataIndex;
}
