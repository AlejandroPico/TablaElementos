<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';

  type SectionId = 'classification' | 'atomic' | 'physical' | 'dataset';

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
    section: Exclude<SectionId, 'classification'>;
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

  const STORAGE_KEY = 'tabla-elementos-filtros-v2';

  const RANGE_CATALOG: Array<Omit<RangeDefinition, 'domainMin' | 'domainMax' | 'min' | 'max' | 'includeMissing' | 'availableCount'>> = [
    { id: 'atomic_number', label: 'Número atómico', unit: 'Z', section: 'atomic', step: 1 },
    { id: 'atomic_mass', label: 'Masa atómica', unit: 'u', section: 'atomic', step: 0.01 },
    { id: 'electronegativity', label: 'Electronegatividad', unit: 'Pauling', section: 'atomic', step: 0.01 },
    { id: 'ionization_energy', label: 'Primera ionización', unit: 'kJ/mol', section: 'atomic', step: 1 },
    { id: 'electron_affinity', label: 'Afinidad electrónica', unit: 'kJ/mol', section: 'atomic', step: 1 },
    { id: 'atomic_radius', label: 'Radio atómico', unit: 'pm', section: 'atomic', step: 1 },
    { id: 'melting_point', label: 'Punto de fusión', unit: 'K', section: 'physical', step: 1 },
    { id: 'boiling_point', label: 'Punto de ebullición', unit: 'K', section: 'physical', step: 1 },
    { id: 'density', label: 'Densidad', unit: 'g/cm³', section: 'physical', step: 0.001 },
    { id: 'specific_heat', label: 'Calor específico', unit: 'J/(g·K)', section: 'physical', step: 0.01 },
    { id: 'discovery_year', label: 'Año de descubrimiento', unit: 'año', section: 'dataset', step: 1 },
    { id: 'spectral_line_count', label: 'Líneas espectrales', unit: 'registros', section: 'dataset', step: 1 },
    { id: 'isotope_count', label: 'Isótopos', unit: 'registros', section: 'dataset', step: 1 },
    { id: 'level_count', label: 'Niveles NIST', unit: 'registros', section: 'dataset', step: 1 },
    { id: 'available_file_count', label: 'Bloques con datos', unit: 'archivos', section: 'dataset', step: 1 }
  ];

  const DOMAIN_LABELS: Record<string, string> = {
    identity: 'Identidad', atomic: 'Propiedades atómicas', physical: 'Propiedades físicas',
    chemical: 'Química', isotopes: 'Isótopos', nist_levels: 'Niveles NIST',
    materials: 'Materiales', thermodynamics: 'Termodinámica', compounds: 'Compuestos',
    photonics: 'Fotónica y color', radiation: 'Radiación', analytical: 'Métodos analíticos',
    computational: 'Datos computacionales', geochemistry: 'Geoquímica',
    astrophysics: 'Astrofísica', biology: 'Biología y medicina',
    environment: 'Medioambiente y seguridad', industry: 'Industria y economía',
    history: 'Historia', sources: 'Fuentes'
  };

  const sections: Array<{ id: SectionId; label: string; short: string }> = [
    { id: 'classification', label: 'Clasificación', short: 'Clases' },
    { id: 'atomic', label: 'Propiedades atómicas', short: 'Atómicas' },
    { id: 'physical', label: 'Propiedades físicas', short: 'Físicas' },
    { id: 'dataset', label: 'Datos y cobertura', short: 'Datos' }
  ];

  let activeSection: SectionId = 'classification';
  let records: FilterRecord[] = [];
  let ranges: RangeDefinition[] = [];
  let categories: string[] = [];
  let oxidationOptions: string[] = [];
  let domainOptions: string[] = [];
  let loading = true;
  let loadError = '';
  let expandedRangeId = '';
  let matchingCount = 0;
  let activeCount = 0;
  let reapplyFrame = 0;
  let gridObserver: MutationObserver | null = null;

  let selectedCategories = new Set<string>();
  let selectedBlocks = new Set<string>();
  let selectedMetalTypes = new Set<string>();
  let selectedStates = new Set<string>();
  let selectedGroups = new Set<number>();
  let selectedPeriods = new Set<number>();
  let selectedOxidationStates = new Set<string>();
  let selectedDomains = new Set<string>();

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
      metaloide: 'Metaloide', 'no metal': 'No metal', halogeno: 'Halógeno',
      'gas noble': 'Gas noble', lantanido: 'Lantánido', actinido: 'Actínido',
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
    if (!normalized || normalized === 'desconocido') return 'Sin clasificar';
    return 'Metal';
  }

  function numeric(value: unknown): number | null {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    const text = String(value ?? '').replace(/−/g, '-').replace(/,/g, '.');
    const match = text.match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    if (!match) return null;
    const result = Number(match[0]);
    return Number.isFinite(result) ? result : null;
  }

  function oxidationTokens(value: unknown): string[] {
    const tokens = String(value ?? '').match(/[+-]?\d+(?:\.\d+)?/g) ?? [];
    return Array.from(new Set(tokens.map((token) => token.startsWith('+') || token.startsWith('-') ? token : `+${token}`)));
  }

  function fallbackValues(element: DatasetElement, index: ElementIndex): Record<string, string | number | null> {
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
    const values = { ...fallbackValues(element, index), ...(index.filter_values ?? {}) };
    const category = String(values.category ?? element.category ?? 'Desconocido');
    return {
      symbol: element.symbol,
      category,
      block: String(values.block ?? element.block ?? '').toLowerCase() || 'sin dato',
      metalType: String(values.metal_type ?? metalType(category)),
      state: normalizeState(values.standard_state),
      group: Number(values.group ?? element.group ?? 0),
      period: Number(values.period ?? element.period ?? 0),
      oxidationStates: oxidationTokens(values.oxidation_states),
      domains: new Set(index.available_domains ?? []),
      numeric: Object.fromEntries(RANGE_CATALOG.map((definition) => [definition.id, numeric(values[definition.id])]))
    };
  }

  function prepareRanges(): void {
    ranges = RANGE_CATALOG.flatMap((definition) => {
      const values = records
        .map((record) => record.numeric[definition.id])
        .filter((value): value is number => value !== null && Number.isFinite(value));
      if (!values.length) return [];
      const domainMin = Math.min(...values);
      const rawMax = Math.max(...values);
      const domainMax = rawMax === domainMin ? rawMax + definition.step : rawMax;
      return [{ ...definition, domainMin, domainMax, min: domainMin, max: domainMax, includeMissing: false, availableCount: values.length }];
    });
  }

  function rangeActive(range: RangeDefinition): boolean {
    const epsilon = Math.max(range.step / 10, 1e-9);
    return Math.abs(range.min - range.domainMin) > epsilon ||
      Math.abs(range.max - range.domainMax) > epsilon || range.includeMissing;
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
    return total + ranges.filter(rangeActive).length;
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

    if (selectedOxidationStates.size && !record.oxidationStates.some((state) => selectedOxidationStates.has(state))) return false;
    if (selectedDomains.size && !Array.from(selectedDomains).every((domain) => record.domains.has(domain))) return false;

    for (const range of ranges) {
      if (!rangeActive(range)) continue;
      const value = record.numeric[range.id];
      if (value === null) {
        if (!range.includeMissing) return false;
      } else if (value < range.min || value > range.max) {
        return false;
      }
    }
    return true;
  }

  function applyFilters(): void {
    if (!records.length) return;

    // Se calcula aquí, no mediante un valor reactivo pendiente del siguiente ciclo de Svelte.
    const currentActiveCount = countActiveFilters();
    const active = currentActiveCount > 0;
    const recordBySymbol = new Map(records.map((record) => [record.symbol, record]));
    let matches = 0;

    document.querySelectorAll<HTMLElement>('.element-cell[data-element-symbol]').forEach((cell) => {
      const record = recordBySymbol.get(cell.dataset.elementSymbol ?? '');
      const matched = Boolean(record && recordMatches(record));
      if (matched) matches += 1;
      cell.classList.toggle('filter-match', active && matched);
      cell.classList.toggle('filter-dimmed', active && !matched);
      cell.dataset.filterMatch = matched ? 'true' : 'false';
    });

    activeCount = currentActiveCount;
    matchingCount = active ? matches : records.length;
    document.documentElement.classList.toggle('element-filters-active', active);
    dispatch('change', { active: activeCount, matches: matchingCount, total: records.length });
    saveFilters();
  }

  function scheduleReapply(): void {
    cancelAnimationFrame(reapplyFrame);
    reapplyFrame = requestAnimationFrame(applyFilters);
  }

  function toggleValue<T>(set: Set<T>, value: T): Set<T> {
    const next = new Set(set);
    if (next.has(value)) next.delete(value); else next.add(value);
    return next;
  }

  function toggleCategory(value: string): void { selectedCategories = toggleValue(selectedCategories, value); applyFilters(); }
  function toggleBlock(value: string): void { selectedBlocks = toggleValue(selectedBlocks, value); applyFilters(); }
  function toggleMetalType(value: string): void { selectedMetalTypes = toggleValue(selectedMetalTypes, value); applyFilters(); }
  function toggleState(value: string): void { selectedStates = toggleValue(selectedStates, value); applyFilters(); }
  function toggleGroup(value: number): void { selectedGroups = toggleValue(selectedGroups, value); applyFilters(); }
  function togglePeriod(value: number): void { selectedPeriods = toggleValue(selectedPeriods, value); applyFilters(); }
  function toggleOxidation(value: string): void { selectedOxidationStates = toggleValue(selectedOxidationStates, value); applyFilters(); }
  function toggleDomain(value: string): void { selectedDomains = toggleValue(selectedDomains, value); applyFilters(); }

  function setRange(id: string, edge: 'min' | 'max', rawValue: string): void {
    const parsed = Number(rawValue);
    if (!Number.isFinite(parsed)) return;
    ranges = ranges.map((range) => {
      if (range.id !== id) return range;
      if (edge === 'min') return { ...range, min: Math.min(Math.max(parsed, range.domainMin), range.max) };
      return { ...range, max: Math.max(Math.min(parsed, range.domainMax), range.min) };
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
      : range);
    applyFilters();
  }

  function clearAll(): void {
    selectedCategories = new Set(); selectedBlocks = new Set(); selectedMetalTypes = new Set();
    selectedStates = new Set(); selectedGroups = new Set(); selectedPeriods = new Set();
    selectedOxidationStates = new Set(); selectedDomains = new Set();
    ranges = ranges.map((range) => ({ ...range, min: range.domainMin, max: range.domainMax, includeMissing: false }));
    expandedRangeId = '';
    applyFilters();
  }

  function formatValue(value: number, step: number): string {
    if (step >= 1) return Math.round(value).toLocaleString('es-ES');
    return value.toLocaleString('es-ES', { maximumFractionDigits: step <= 0.001 ? 3 : 2 });
  }

  function percent(value: number, range: RangeDefinition): number {
    return ((value - range.domainMin) / Math.max(range.domainMax - range.domainMin, Number.EPSILON)) * 100;
  }

  function saveFilters(): void {
    const snapshot: SavedFilters = {
      categories: [...selectedCategories], blocks: [...selectedBlocks], metalTypes: [...selectedMetalTypes],
      states: [...selectedStates], groups: [...selectedGroups], periods: [...selectedPeriods],
      oxidationStates: [...selectedOxidationStates], domains: [...selectedDomains],
      ranges: Object.fromEntries(ranges.map((range) => [range.id, { min: range.min, max: range.max, includeMissing: range.includeMissing }]))
    };
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot)); } catch { /* opcional */ }
  }

  function restoreFilters(): void {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw) as SavedFilters;
      selectedCategories = new Set(saved.categories ?? []); selectedBlocks = new Set(saved.blocks ?? []);
      selectedMetalTypes = new Set(saved.metalTypes ?? []); selectedStates = new Set(saved.states ?? []);
      selectedGroups = new Set(saved.groups ?? []); selectedPeriods = new Set(saved.periods ?? []);
      selectedOxidationStates = new Set(saved.oxidationStates ?? []); selectedDomains = new Set(saved.domains ?? []);
      ranges = ranges.map((range) => {
        const savedRange = saved.ranges?.[range.id];
        if (!savedRange) return range;
        const min = Math.max(range.domainMin, Math.min(savedRange.min, range.domainMax));
        const max = Math.max(min, Math.min(savedRange.max, range.domainMax));
        return { ...range, min, max, includeMissing: Boolean(savedRange.includeMissing) };
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
      categories = [...new Set(records.map((record) => record.category))].sort((a, b) => a.localeCompare(b, 'es'));
      oxidationOptions = [...new Set(records.flatMap((record) => record.oxidationStates))].sort((a, b) => Number(a) - Number(b));
      domainOptions = [...new Set(records.flatMap((record) => [...record.domains]))]
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
    gridObserver = new MutationObserver(scheduleReapply);
    gridObserver.observe(document.body, { childList: true, subtree: true });

    const handleKey = (event: KeyboardEvent): void => {
      if (open && event.key === 'Escape') dispatch('close');
    };
    window.addEventListener('keydown', handleKey);
    return () => {
      window.removeEventListener('keydown', handleKey);
      gridObserver?.disconnect();
      cancelAnimationFrame(reapplyFrame);
    };
  });
</script>

{#if open}
  <aside class="element-filter-panel-v2" aria-label="Filtros científicos de la tabla">
    <header class="filter-v2-head">
      <div><p>Selección científica</p><h2>Filtros</h2></div>
      <div class="filter-v2-head-actions">
        <button type="button" aria-label="Restablecer filtros" title="Restablecer filtros" disabled={!activeCount} on:click={clearAll}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.35-5.65L4 8.7M4 4v4.7h4.7"></path></svg>
        </button>
        <button type="button" aria-label="Cerrar filtros" title="Cerrar" on:click={() => dispatch('close')}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"></path></svg>
        </button>
      </div>
    </header>

    <div class="filter-v2-status">
      <div><strong>{matchingCount}</strong><span>de {records.length}</span></div>
      <p>{activeCount ? `${activeCount} criterios activos` : 'Tabla completa'}</p>
    </div>

    <div class="filter-v2-logic">
      <span><b>O</b> dentro del mismo bloque</span>
      <span><b>Y</b> entre bloques diferentes</span>
    </div>

    <nav class="filter-v2-tabs" aria-label="Familias de filtros">
      {#each sections as section}
        <button type="button" class:active={activeSection === section.id} on:click={() => (activeSection = section.id)}>
          <span>{section.short}</span>
        </button>
      {/each}
    </nav>

    {#if loading}
      <div class="filter-v2-state">Preparando propiedades y rangos…</div>
    {:else if loadError}
      <div class="filter-v2-state problem">No se pudieron cargar los filtros: {loadError}</div>
    {:else}
      <div class="filter-v2-scroll">
        {#if activeSection === 'classification'}
          <section class="filter-v2-card accent-category">
            <header><div><small>Familias</small><h3>Categoría química</h3></div><span>{selectedCategories.size || 'Todas'}</span></header>
            <div class="filter-v2-options category-options">
              {#each categories as category}
                <button type="button" class:active={selectedCategories.has(category)} on:click={() => toggleCategory(category)}>{displayCategory(category)}</button>
              {/each}
            </div>
          </section>

          <div class="filter-v2-two-columns">
            <section class="filter-v2-card accent-block">
              <header><div><small>Orbital</small><h3>Bloque</h3></div><span>{selectedBlocks.size || 'Todos'}</span></header>
              <div class="filter-v2-options compact">
                {#each ['s', 'p', 'd', 'f', 'sin dato'] as block}
                  <button type="button" class:active={selectedBlocks.has(block)} on:click={() => toggleBlock(block)}>{block === 'sin dato' ? '—' : block}</button>
                {/each}
              </div>
            </section>

            <section class="filter-v2-card accent-metal">
              <header><div><small>Naturaleza</small><h3>Tipo</h3></div><span>{selectedMetalTypes.size || 'Todos'}</span></header>
              <div class="filter-v2-options">
                {#each ['Metal', 'Metaloide', 'No metal', 'Sin clasificar'] as type}
                  <button type="button" class:active={selectedMetalTypes.has(type)} on:click={() => toggleMetalType(type)}>{type}</button>
                {/each}
              </div>
            </section>
          </div>

          <section class="filter-v2-card accent-state">
            <header><div><small>Condiciones estándar</small><h3>Estado físico</h3></div><span>{selectedStates.size || 'Todos'}</span></header>
            <div class="filter-v2-options">
              {#each ['Sólido', 'Líquido', 'Gas', 'Sin dato'] as state}
                <button type="button" class:active={selectedStates.has(state)} on:click={() => toggleState(state)}>{state}</button>
              {/each}
            </div>
          </section>

          <section class="filter-v2-card accent-position">
            <header><div><small>Posición periódica</small><h3>Periodo y grupo</h3></div><span>{selectedPeriods.size + selectedGroups.size || 'Todos'}</span></header>
            <div class="filter-v2-subtitle">Periodo</div>
            <div class="filter-v2-options numeric-options">
              {#each Array.from({ length: 7 }, (_, index) => index + 1) as period}
                <button type="button" class:active={selectedPeriods.has(period)} on:click={() => togglePeriod(period)}>{period}</button>
              {/each}
            </div>
            <div class="filter-v2-subtitle">Grupo</div>
            <div class="filter-v2-options numeric-options group-grid">
              {#each Array.from({ length: 18 }, (_, index) => index + 1) as group}
                <button type="button" class:active={selectedGroups.has(group)} on:click={() => toggleGroup(group)}>{group}</button>
              {/each}
            </div>
          </section>

          {#if oxidationOptions.length}
            <section class="filter-v2-card accent-oxidation">
              <header><div><small>Química</small><h3>Estados de oxidación</h3></div><span>{selectedOxidationStates.size || 'Todos'}</span></header>
              <div class="filter-v2-options numeric-options">
                {#each oxidationOptions as state}
                  <button type="button" class:active={selectedOxidationStates.has(state)} on:click={() => toggleOxidation(state)}>{state}</button>
                {/each}
              </div>
            </section>
          {/if}
        {:else}
          {#each ranges.filter((range) => range.section === activeSection) as range}
            <article class:active={rangeActive(range)} class="filter-v2-range-card">
              <button class="filter-v2-range-title" type="button" aria-expanded={expandedRangeId === range.id} on:click={() => (expandedRangeId = expandedRangeId === range.id ? '' : range.id)}>
                <span><small>{range.availableCount} valores disponibles</small><strong>{range.label}</strong></span>
                <span class="range-reading">{formatValue(range.min, range.step)} – {formatValue(range.max, range.step)} <em>{range.unit}</em></span>
                <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 8l4 4 4-4"></path></svg>
              </button>

              {#if expandedRangeId === range.id}
                <div class="filter-v2-range-body">
                  <div class="filter-v2-dual-range" style={`--range-start:${percent(range.min, range).toFixed(3)}%;--range-end:${percent(range.max, range).toFixed(3)}%;`}>
                    <div></div>
                    <input type="range" min={range.domainMin} max={range.domainMax} step={range.step} value={range.min} aria-label={`Mínimo de ${range.label}`} on:input={(event) => setRange(range.id, 'min', event.currentTarget.value)} />
                    <input type="range" min={range.domainMin} max={range.domainMax} step={range.step} value={range.max} aria-label={`Máximo de ${range.label}`} on:input={(event) => setRange(range.id, 'max', event.currentTarget.value)} />
                  </div>
                  <div class="filter-v2-number-row">
                    <label><span>Mínimo</span><input type="number" min={range.domainMin} max={range.max} step={range.step} value={range.min} on:change={(event) => setRange(range.id, 'min', event.currentTarget.value)} /></label>
                    <b>{range.unit}</b>
                    <label><span>Máximo</span><input type="number" min={range.min} max={range.domainMax} step={range.step} value={range.max} on:change={(event) => setRange(range.id, 'max', event.currentTarget.value)} /></label>
                  </div>
                  <footer>
                    <label><input type="checkbox" checked={range.includeMissing} on:change={() => toggleMissing(range.id)} /> Incluir elementos sin dato</label>
                    <button type="button" disabled={!rangeActive(range)} on:click={() => resetRange(range.id)}>Restablecer</button>
                  </footer>
                </div>
              {/if}
            </article>
          {/each}

          {#if activeSection === 'dataset'}
            <section class="filter-v2-card accent-domain">
              <header><div><small>Cobertura</small><h3>Información disponible</h3></div><span>{selectedDomains.size || 'Cualquiera'}</span></header>
              <p class="filter-v2-help">El elemento debe contener todos los bloques seleccionados.</p>
              <div class="filter-v2-options domain-options">
                {#each domainOptions as domain}
                  <button type="button" class:active={selectedDomains.has(domain)} on:click={() => toggleDomain(domain)}>{DOMAIN_LABELS[domain] ?? domain}</button>
                {/each}
              </div>
            </section>
          {/if}
        {/if}
      </div>
    {/if}
  </aside>
{/if}
