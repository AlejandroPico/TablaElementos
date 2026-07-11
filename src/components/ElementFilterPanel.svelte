<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';

  interface DatasetElement {
    symbol: string;
    name_es: string;
    atomic_number: number;
    group: number;
    period: number;
    block?: string;
    category: string;
    lines?: unknown[];
  }

  interface ElementIndex {
    available_domains?: string[];
    available_file_count?: number;
    domain_counts?: Record<string, number>;
    summary_values?: Record<string, string>;
    filter_values?: Record<string, string | number | null>;
  }

  interface Dataset {
    elements?: DatasetElement[];
    data_index_by_element?: Record<string, ElementIndex>;
  }

  interface FilterRecord {
    symbol: string;
    name: string;
    category: string;
    block: string;
    metalType: string;
    state: string;
    group: number;
    period: number;
    oxidationStates: string[];
    domains: Set<string>;
    numeric: Record<string, number | null>;
  }

  interface RangeDefinition {
    id: string;
    label: string;
    unit: string;
    section: 'periodic' | 'atomic' | 'physical' | 'dataset';
    step: number;
    domainMin: number;
    domainMax: number;
    min: number;
    max: number;
    includeMissing: boolean;
    availableCount: number;
  }

  interface SavedFilters {
    categories?: string[];
    blocks?: string[];
    metalTypes?: string[];
    states?: string[];
    groups?: number[];
    periods?: number[];
    oxidationStates?: string[];
    domains?: string[];
    ranges?: Record<string, { min: number; max: number; includeMissing: boolean }>;
  }

  export let open = false;

  const dispatch = createEventDispatcher<{
    close: void;
    change: { active: number; matches: number; total: number };
  }>();

  const STORAGE_KEY = 'tabla-elementos-filtros-v1';

  const RANGE_CATALOG: Array<Omit<RangeDefinition, 'domainMin' | 'domainMax' | 'min' | 'max' | 'includeMissing' | 'availableCount'>> = [
    { id: 'atomic_number', label: 'Número atómico', unit: 'Z', section: 'periodic', step: 1 },
    { id: 'group', label: 'Grupo', unit: '1–18', section: 'periodic', step: 1 },
    { id: 'period', label: 'Periodo', unit: '1–7', section: 'periodic', step: 1 },
    { id: 'atomic_mass', label: 'Masa atómica', unit: 'u', section: 'atomic', step: 0.01 },
    { id: 'electronegativity', label: 'Electronegatividad', unit: 'Pauling', section: 'atomic', step: 0.01 },
    { id: 'ionization_energy', label: 'Primera ionización', unit: 'kJ/mol', section: 'atomic', step: 1 },
    { id: 'electron_affinity', label: 'Afinidad electrónica', unit: 'kJ/mol', section: 'atomic', step: 1 },
    { id: 'atomic_radius', label: 'Radio atómico', unit: 'pm', section: 'atomic', step: 1 },
    { id: 'melting_point', label: 'Punto de fusión', unit: 'K', section: 'physical', step: 1 },
    { id: 'boiling_point', label: 'Punto de ebullición', unit: 'K', section: 'physical', step: 1 },
    { id: 'density', label: 'Densidad', unit: 'g/cm³', section: 'physical', step: 0.001 },
    { id: 'specific_heat', label: 'Calor específico', unit: 'J/(g·K)', section: 'physical', step: 0.01 },
    { id: 'discovery_year', label: 'Año de descubrimiento', unit: 'año', section: 'periodic', step: 1 },
    { id: 'spectral_line_count', label: 'Líneas espectrales', unit: 'registros', section: 'dataset', step: 1 },
    { id: 'isotope_count', label: 'Isótopos', unit: 'registros', section: 'dataset', step: 1 },
    { id: 'level_count', label: 'Niveles NIST', unit: 'registros', section: 'dataset', step: 1 },
    { id: 'available_file_count', label: 'Bloques con datos', unit: 'archivos', section: 'dataset', step: 1 }
  ];

  const DOMAIN_LABELS: Record<string, string> = {
    identity: 'Identidad',
    atomic: 'Propiedades atómicas',
    physical: 'Propiedades físicas',
    chemical: 'Química',
    isotopes: 'Isótopos',
    nist_levels: 'Niveles NIST',
    materials: 'Materiales',
    thermodynamics: 'Termodinámica',
    compounds: 'Compuestos',
    photonics: 'Fotónica y color',
    radiation: 'Radiación',
    analytical: 'Métodos analíticos',
    computational: 'Datos computacionales',
    geochemistry: 'Geoquímica',
    astrophysics: 'Astrofísica',
    biology: 'Biología y medicina',
    environment: 'Medioambiente y seguridad',
    industry: 'Industria y economía',
    history: 'Historia',
    sources: 'Fuentes'
  };

  let records: FilterRecord[] = [];
  let ranges: RangeDefinition[] = [];
  let categories: string[] = [];
  let oxidationOptions: string[] = [];
  let domainOptions: string[] = [];
  let loading = true;
  let loadError = '';
  let expandedRangeId = '';
  let matchingCount = 0;

  let selectedCategories = new Set<string>();
  let selectedBlocks = new Set<string>();
  let selectedMetalTypes = new Set<string>();
  let selectedStates = new Set<string>();
  let selectedGroups = new Set<number>();
  let selectedPeriods = new Set<number>();
  let selectedOxidationStates = new Set<string>();
  let selectedDomains = new Set<string>();

  $: activeCount = countActiveFilters();

  function datasetUrl(): string {
    return new URL('./data/spectra.sample.json', document.baseURI).toString();
  }

  function normalizeText(value: unknown): string {
    return String(value ?? '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim()
      .toLowerCase();
  }

  function displayCategory(value: string): string {
    const labels: Record<string, string> = {
      'metal alcalino': 'Metal alcalino',
      'metal alcalinoterreo': 'Metal alcalinotérreo',
      'metal de transicion': 'Metal de transición',
      'metal post-transicion': 'Metal postransición',
      metaloide: 'Metaloide',
      'no metal': 'No metal',
      halogeno: 'Halógeno',
      'gas noble': 'Gas noble',
      lantanido: 'Lantánido',
      actinido: 'Actínido',
      desconocido: 'Desconocido'
    };
    return labels[normalizeText(value)] ?? value;
  }

  function normalizeState(value: unknown): string {
    const normalized = normalizeText(value);
    if (normalized.includes('solid') || normalized.includes('solido')) return 'Sólido';
    if (normalized.includes('liquid') || normalized.includes('liquido')) return 'Líquido';
    if (normalized.includes('gas')) return 'Gas';
    return 'Sin dato';
  }

  function metalType(category: string): string {
    const normalized = normalizeText(category);
    if (normalized === 'metaloide') return 'Metaloide';
    if (['no metal', 'halogeno', 'gas noble'].includes(normalized)) return 'No metal';
    if (normalized === 'desconocido' || !normalized) return 'Sin clasificar';
    return 'Metal';
  }

  function numeric(value: unknown): number | null {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    const normalized = String(value ?? '')
      .replace(/−/g, '-')
      .replace(/,/g, '.')
      .trim();
    const match = normalized.match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    if (!match) return null;
    const parsed = Number(match[0]);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function oxidationTokens(value: unknown): string[] {
    const text = String(value ?? '');
    const tokens = text.match(/[+-]?\d+(?:\.\d+)?/g) ?? [];
    return Array.from(new Set(tokens.map((token) => (token.startsWith('+') || token.startsWith('-') ? token : `+${token}`))));
  }

  function fallbackFilterValues(element: DatasetElement, index: ElementIndex): Record<string, string | number | null> {
    const summary = index.summary_values ?? {};
    return {
      atomic_number: element.atomic_number,
      group: element.group,
      period: element.period,
      category: element.category,
      block: element.block ?? '',
      metal_type: metalType(element.category),
      standard_state: summary.standard_state ?? '',
      atomic_mass: numeric(summary.standard_atomic_weight ?? summary.atomic_mass),
      electronegativity: numeric(summary.electronegativity),
      ionization_energy: numeric(summary.ionization_energy),
      electron_affinity: numeric(summary.electron_affinity),
      atomic_radius: numeric(summary.atomic_radius),
      melting_point: numeric(summary.melting_point),
      boiling_point: numeric(summary.boiling_point),
      density: numeric(summary.density),
      spectral_line_count: element.lines?.length ?? 0,
      isotope_count: index.domain_counts?.isotopes ?? 0,
      level_count: index.domain_counts?.nist_levels ?? 0,
      available_file_count: index.available_file_count ?? 0
    };
  }

  function createRecord(element: DatasetElement, index: ElementIndex): FilterRecord {
    const values = { ...fallbackFilterValues(element, index), ...(index.filter_values ?? {}) };
    const category = String(values.category ?? element.category ?? 'Desconocido');
    return {
      symbol: element.symbol,
      name: element.name_es,
      category,
      block: String(values.block ?? element.block ?? '').toLowerCase() || 'sin dato',
      metalType: String(values.metal_type ?? metalType(category)),
      state: normalizeState(values.standard_state),
      group: Number(values.group ?? element.group ?? 0),
      period: Number(values.period ?? element.period ?? 0),
      oxidationStates: oxidationTokens(values.oxidation_states),
      domains: new Set(index.available_domains ?? []),
      numeric: Object.fromEntries(
        RANGE_CATALOG.map((definition) => [definition.id, numeric(values[definition.id])])
      )
    };
  }

  function prepareRanges(): void {
    ranges = RANGE_CATALOG.flatMap((definition) => {
      const values = records
        .map((record) => record.numeric[definition.id])
        .filter((value): value is number => value !== null && Number.isFinite(value));
      if (!values.length) return [];
      const domainMin = Math.min(...values);
      const domainMax = Math.max(...values);
      const safeMax = domainMax === domainMin ? domainMax + definition.step : domainMax;
      return [{
        ...definition,
        domainMin,
        domainMax: safeMax,
        min: domainMin,
        max: safeMax,
        includeMissing: false,
        availableCount: values.length
      }];
    });
  }

  function rangeActive(range: RangeDefinition): boolean {
    const epsilon = Math.max(range.step / 10, 1e-9);
    return (
      Math.abs(range.min - range.domainMin) > epsilon ||
      Math.abs(range.max - range.domainMax) > epsilon ||
      range.includeMissing
    );
  }

  function countActiveFilters(): number {
    let total = 0;
    if (selectedCategories.size) total += 1;
    if (selectedBlocks.size) total += 1;
    if (selectedMetalTypes.size) total += 1;
    if (selectedStates.size) total += 1;
    if (selectedGroups.size) total += 1;
    if (selectedPeriods.size) total += 1;
    if (selectedOxidationStates.size) total += 1;
    if (selectedDomains.size) total += 1;
    total += ranges.filter(rangeActive).length;
    return total;
  }

  function matchesSet<T>(selected: Set<T>, value: T): boolean {
    return !selected.size || selected.has(value);
  }

  function recordMatches(record: FilterRecord): boolean {
    if (!matchesSet(selectedCategories, record.category)) return false;
    if (!matchesSet(selectedBlocks, record.block)) return false;
    if (!matchesSet(selectedMetalTypes, record.metalType)) return false;
    if (!matchesSet(selectedStates, record.state)) return false;
    if (!matchesSet(selectedGroups, record.group)) return false;
    if (!matchesSet(selectedPeriods, record.period)) return false;

    if (
      selectedOxidationStates.size &&
      !record.oxidationStates.some((state) => selectedOxidationStates.has(state))
    ) return false;

    if (selectedDomains.size && !Array.from(selectedDomains).every((domain) => record.domains.has(domain))) {
      return false;
    }

    for (const range of ranges) {
      if (!rangeActive(range)) continue;
      const value = record.numeric[range.id];
      if (value === null) {
        if (!range.includeMissing) return false;
        continue;
      }
      if (value < range.min || value > range.max) return false;
    }

    return true;
  }

  function applyFilters(): void {
    if (!records.length) return;
    const active = activeCount > 0;
    let matches = 0;

    const recordBySymbol = new Map(records.map((record) => [record.symbol, record]));
    document.querySelectorAll<HTMLElement>('.element-cell[data-element-symbol]').forEach((cell) => {
      const symbol = cell.dataset.elementSymbol ?? '';
      const record = recordBySymbol.get(symbol);
      const matched = record ? recordMatches(record) : false;
      if (matched) matches += 1;
      cell.classList.toggle('filter-match', active && matched);
      cell.classList.toggle('filter-dimmed', active && !matched);
      cell.setAttribute('data-filter-match', matched ? 'true' : 'false');
    });

    document.documentElement.classList.toggle('element-filters-active', active);
    matchingCount = active ? matches : records.length;
    dispatch('change', { active: activeCount, matches: matchingCount, total: records.length });
    saveFilters();
  }

  function cloneToggle<T>(set: Set<T>, value: T): Set<T> {
    const next = new Set(set);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    return next;
  }

  function toggleCategory(value: string): void {
    selectedCategories = cloneToggle(selectedCategories, value);
    applyFilters();
  }

  function toggleBlock(value: string): void {
    selectedBlocks = cloneToggle(selectedBlocks, value);
    applyFilters();
  }

  function toggleMetalType(value: string): void {
    selectedMetalTypes = cloneToggle(selectedMetalTypes, value);
    applyFilters();
  }

  function toggleState(value: string): void {
    selectedStates = cloneToggle(selectedStates, value);
    applyFilters();
  }

  function toggleGroup(value: number): void {
    selectedGroups = cloneToggle(selectedGroups, value);
    applyFilters();
  }

  function togglePeriod(value: number): void {
    selectedPeriods = cloneToggle(selectedPeriods, value);
    applyFilters();
  }

  function toggleOxidation(value: string): void {
    selectedOxidationStates = cloneToggle(selectedOxidationStates, value);
    applyFilters();
  }

  function toggleDomain(value: string): void {
    selectedDomains = cloneToggle(selectedDomains, value);
    applyFilters();
  }

  function setRange(id: string, edge: 'min' | 'max', rawValue: string): void {
    const parsed = Number(rawValue);
    if (!Number.isFinite(parsed)) return;
    ranges = ranges.map((range) => {
      if (range.id !== id) return range;
      if (edge === 'min') {
        const min = Math.min(Math.max(parsed, range.domainMin), range.max);
        return { ...range, min };
      }
      const max = Math.max(Math.min(parsed, range.domainMax), range.min);
      return { ...range, max };
    });
    applyFilters();
  }

  function toggleMissing(id: string): void {
    ranges = ranges.map((range) => range.id === id ? { ...range, includeMissing: !range.includeMissing } : range);
    applyFilters();
  }

  function resetRange(id: string): void {
    ranges = ranges.map((range) => range.id === id
      ? { ...range, min: range.domainMin, max: range.domainMax, includeMissing: false }
      : range
    );
    applyFilters();
  }

  function clearAll(): void {
    selectedCategories = new Set();
    selectedBlocks = new Set();
    selectedMetalTypes = new Set();
    selectedStates = new Set();
    selectedGroups = new Set();
    selectedPeriods = new Set();
    selectedOxidationStates = new Set();
    selectedDomains = new Set();
    ranges = ranges.map((range) => ({
      ...range,
      min: range.domainMin,
      max: range.domainMax,
      includeMissing: false
    }));
    expandedRangeId = '';
    applyFilters();
  }

  function formatValue(value: number, step: number): string {
    if (step >= 1) return Math.round(value).toLocaleString('es-ES');
    const decimals = step <= 0.001 ? 3 : 2;
    return value.toLocaleString('es-ES', { maximumFractionDigits: decimals });
  }

  function percent(value: number, range: RangeDefinition): number {
    if (range.domainMax === range.domainMin) return 0;
    return ((value - range.domainMin) / (range.domainMax - range.domainMin)) * 100;
  }

  function filtersSnapshot(): SavedFilters {
    return {
      categories: Array.from(selectedCategories),
      blocks: Array.from(selectedBlocks),
      metalTypes: Array.from(selectedMetalTypes),
      states: Array.from(selectedStates),
      groups: Array.from(selectedGroups),
      periods: Array.from(selectedPeriods),
      oxidationStates: Array.from(selectedOxidationStates),
      domains: Array.from(selectedDomains),
      ranges: Object.fromEntries(ranges.map((range) => [range.id, {
        min: range.min,
        max: range.max,
        includeMissing: range.includeMissing
      }]))
    };
  }

  function saveFilters(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtersSnapshot()));
    } catch {
      // El filtrado no depende del almacenamiento local.
    }
  }

  function restoreFilters(): void {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw) as SavedFilters;
      selectedCategories = new Set(saved.categories ?? []);
      selectedBlocks = new Set(saved.blocks ?? []);
      selectedMetalTypes = new Set(saved.metalTypes ?? []);
      selectedStates = new Set(saved.states ?? []);
      selectedGroups = new Set(saved.groups ?? []);
      selectedPeriods = new Set(saved.periods ?? []);
      selectedOxidationStates = new Set(saved.oxidationStates ?? []);
      selectedDomains = new Set(saved.domains ?? []);
      ranges = ranges.map((range) => {
        const savedRange = saved.ranges?.[range.id];
        if (!savedRange) return range;
        return {
          ...range,
          min: Math.max(range.domainMin, Math.min(savedRange.min, range.domainMax)),
          max: Math.max(range.domainMin, Math.min(savedRange.max, range.domainMax)),
          includeMissing: Boolean(savedRange.includeMissing)
        };
      });
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  async function loadData(): Promise<void> {
    loading = true;
    loadError = '';
    try {
      const response = await fetch(datasetUrl(), { cache: 'no-cache' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dataset = (await response.json()) as Dataset;
      const index = dataset.data_index_by_element ?? {};
      records = (dataset.elements ?? []).map((element) => createRecord(element, index[element.symbol] ?? {}));
      categories = Array.from(new Set(records.map((record) => record.category))).sort((a, b) => a.localeCompare(b, 'es'));
      oxidationOptions = Array.from(new Set(records.flatMap((record) => record.oxidationStates)))
        .sort((a, b) => Number(a) - Number(b));
      domainOptions = Array.from(new Set(records.flatMap((record) => Array.from(record.domains))))
        .sort((a, b) => (DOMAIN_LABELS[a] ?? a).localeCompare(DOMAIN_LABELS[b] ?? b, 'es'));
      prepareRanges();
      restoreFilters();
      applyFilters();
    } catch (error) {
      loadError = error instanceof Error ? error.message : String(error);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    void loadData();
    const handleKey = (event: KeyboardEvent): void => {
      if (open && event.key === 'Escape') dispatch('close');
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  });
</script>

{#if open}
  <aside class="element-filter-panel" aria-label="Filtros científicos de la tabla">
    <header class="filter-panel-head">
      <div>
        <p>Selección científica</p>
        <h2>Filtros</h2>
      </div>
      <div class="filter-head-actions">
        <button type="button" title="Restablecer todos los filtros" aria-label="Restablecer todos los filtros" on:click={clearAll} disabled={!activeCount}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.35-5.65L4 8.7M4 4v4.7h4.7"></path></svg>
        </button>
        <button type="button" title="Cerrar filtros" aria-label="Cerrar filtros" on:click={() => dispatch('close')}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"></path></svg>
        </button>
      </div>
    </header>

    <div class="filter-result-bar">
      <strong>{matchingCount}</strong><span>de {records.length} elementos</span>
      <small>{activeCount ? `${activeCount} grupos activos` : 'Sin filtros aplicados'}</small>
    </div>

    {#if loading}
      <div class="filter-panel-state">Preparando propiedades y rangos…</div>
    {:else if loadError}
      <div class="filter-panel-state problem">No se pudieron cargar los filtros: {loadError}</div>
    {:else}
      <div class="filter-panel-scroll">
        <details open>
          <summary>Clasificación periódica</summary>

          <section class="filter-group">
            <h3>Categoría</h3>
            <div class="filter-option-grid category-options">
              {#each categories as category}
                <button class:active={selectedCategories.has(category)} type="button" on:click={() => toggleCategory(category)}>{displayCategory(category)}</button>
              {/each}
            </div>
          </section>

          <section class="filter-group compact-groups">
            <div>
              <h3>Bloque</h3>
              <div class="filter-option-grid tiny-options">
                {#each ['s', 'p', 'd', 'f', 'sin dato'] as block}
                  <button class:active={selectedBlocks.has(block)} type="button" on:click={() => toggleBlock(block)}>{block === 'sin dato' ? '—' : block}</button>
                {/each}
              </div>
            </div>
            <div>
              <h3>Tipo</h3>
              <div class="filter-option-grid type-options">
                {#each ['Metal', 'Metaloide', 'No metal', 'Sin clasificar'] as type}
                  <button class:active={selectedMetalTypes.has(type)} type="button" on:click={() => toggleMetalType(type)}>{type}</button>
                {/each}
              </div>
            </div>
          </section>

          <section class="filter-group">
            <h3>Estado estándar</h3>
            <div class="filter-option-grid phase-options">
              {#each ['Sólido', 'Líquido', 'Gas', 'Sin dato'] as state}
                <button class:active={selectedStates.has(state)} type="button" on:click={() => toggleState(state)}>{state}</button>
              {/each}
            </div>
          </section>

          <section class="filter-group">
            <h3>Periodo</h3>
            <div class="filter-option-grid number-options period-options">
              {#each Array.from({ length: 7 }, (_, index) => index + 1) as period}
                <button class:active={selectedPeriods.has(period)} type="button" on:click={() => togglePeriod(period)}>{period}</button>
              {/each}
            </div>
          </section>

          <section class="filter-group">
            <h3>Grupo</h3>
            <div class="filter-option-grid number-options group-options">
              {#each Array.from({ length: 18 }, (_, index) => index + 1) as group}
                <button class:active={selectedGroups.has(group)} type="button" on:click={() => toggleGroup(group)}>{group}</button>
              {/each}
            </div>
          </section>

          {#if oxidationOptions.length}
            <section class="filter-group">
              <h3>Estados de oxidación</h3>
              <div class="filter-option-grid oxidation-options">
                {#each oxidationOptions as state}
                  <button class:active={selectedOxidationStates.has(state)} type="button" on:click={() => toggleOxidation(state)}>{state}</button>
                {/each}
              </div>
            </section>
          {/if}
        </details>

        {#each [
          { id: 'periodic', label: 'Identidad y cronología' },
          { id: 'atomic', label: 'Propiedades atómicas' },
          { id: 'physical', label: 'Propiedades físicas' },
          { id: 'dataset', label: 'Cobertura del dataset' }
        ] as section}
          {@const sectionRanges = ranges.filter((range) => range.section === section.id)}
          {#if sectionRanges.length}
            <details open={section.id === 'atomic' || section.id === 'physical'}>
              <summary>{section.label}</summary>
              <div class="range-filter-list">
                {#each sectionRanges as range}
                  <article class:active={rangeActive(range)} class="range-filter">
                    <button class="range-filter-title" type="button" aria-expanded={expandedRangeId === range.id} on:click={() => (expandedRangeId = expandedRangeId === range.id ? '' : range.id)}>
                      <span><strong>{range.label}</strong><small>{range.availableCount} valores · {range.unit}</small></span>
                      <span class="range-current">{formatValue(range.min, range.step)} – {formatValue(range.max, range.step)}</span>
                      <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 8l4 4 4-4"></path></svg>
                    </button>

                    {#if expandedRangeId === range.id}
                      <div class="range-filter-body">
                        <div class="dual-range" style={`--range-start:${percent(range.min, range).toFixed(3)}%;--range-end:${percent(range.max, range).toFixed(3)}%;`}>
                          <div class="dual-range-track"></div>
                          <input class="range-min" type="range" min={range.domainMin} max={range.domainMax} step={range.step} value={range.min} aria-label={`Mínimo de ${range.label}`} on:input={(event) => setRange(range.id, 'min', event.currentTarget.value)} />
                          <input class="range-max" type="range" min={range.domainMin} max={range.domainMax} step={range.step} value={range.max} aria-label={`Máximo de ${range.label}`} on:input={(event) => setRange(range.id, 'max', event.currentTarget.value)} />
                        </div>

                        <div class="range-number-row">
                          <label><span>Mínimo</span><input type="number" min={range.domainMin} max={range.max} step={range.step} value={range.min} on:change={(event) => setRange(range.id, 'min', event.currentTarget.value)} /></label>
                          <span>{range.unit}</span>
                          <label><span>Máximo</span><input type="number" min={range.min} max={range.domainMax} step={range.step} value={range.max} on:change={(event) => setRange(range.id, 'max', event.currentTarget.value)} /></label>
                        </div>

                        <footer>
                          <label class="include-missing"><input type="checkbox" checked={range.includeMissing} on:change={() => toggleMissing(range.id)} /><span>Incluir elementos sin dato</span></label>
                          <button type="button" on:click={() => resetRange(range.id)} disabled={!rangeActive(range)}>Restablecer</button>
                        </footer>
                      </div>
                    {/if}
                  </article>
                {/each}
              </div>
            </details>
          {/if}
        {/each}

        <details>
          <summary>Disponibilidad de información</summary>
          <section class="filter-group">
            <p class="filter-group-help">Los elementos deben contener todos los bloques seleccionados.</p>
            <div class="filter-option-grid domain-options">
              {#each domainOptions as domain}
                <button class:active={selectedDomains.has(domain)} type="button" on:click={() => toggleDomain(domain)}>{DOMAIN_LABELS[domain] ?? domain}</button>
              {/each}
            </div>
          </section>
        </details>
      </div>
    {/if}
  </aside>
{/if}
