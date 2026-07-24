<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type {
    ComparisonScope,
    ElementDataPayload,
    ElementWithLines,
    SpectralLine
  } from '../lib/atomicTypes';
  import { loadElementData } from '../lib/dataLoader';
  import { formatNm } from '../lib/wavelengthColor';
  import { getStrongestLines } from '../lib/filters';

  interface MatrixRow {
    label: string;
    value: (element: ElementWithLines) => string;
  }

  export let selected: ElementWithLines[] = [];
  export let scope: ComparisonScope = 'global';

  let payloads: Record<string, ElementDataPayload | null> = {};
  let loadingKey = '';

  const dispatch = createEventDispatcher<{
    remove: string;
    clear: void;
    scope: ComparisonScope;
  }>();

  const scopes: Array<{ id: ComparisonScope; label: string }> = [
    { id: 'global', label: 'Global' },
    { id: 'summary', label: 'Resumen' },
    { id: 'atom', label: 'Átomo' },
    { id: 'electronic', label: 'Electrones' },
    { id: 'radii', label: 'Radios' },
    { id: 'crystal', label: 'Cristal' },
    { id: 'nuclear', label: 'Nuclear' },
    { id: 'thermodynamics', label: 'Termodinámica' },
    { id: 'radiation', label: 'Radiación' },
    { id: 'properties', label: 'Propiedades' },
    { id: 'isotopes', label: 'Isótopos' },
    { id: 'spectrum', label: 'Espectro' },
    { id: 'lines', label: 'Líneas' },
    { id: 'levels', label: 'Niveles' },
    { id: 'chemistry', label: 'Química' },
    { id: 'context', label: 'Contexto' },
    { id: 'sources', label: 'Fuentes' }
  ];

  $: selectionKey = selected.map((element) => element.symbol).join('|');
  $: if (selectionKey !== loadingKey) {
    loadingKey = selectionKey;
    void loadPayloads(selected);
  }
  $: matrixRows = rowsFor(scope);

  async function loadPayloads(elements: ElementWithLines[]): Promise<void> {
    const entries = await Promise.all(
      elements.map(async (element) => {
        try {
          return [element.symbol, await loadElementData(element.symbol, element.dataIndex)] as const;
        } catch (_) {
          return [element.symbol, null] as const;
        }
      })
    );
    if (elements.map((element) => element.symbol).join('|') === loadingKey) {
      payloads = Object.fromEntries(entries);
    }
  }

  function payload(element: ElementWithLines): ElementDataPayload | null {
    return payloads[element.symbol] ?? null;
  }

  function domainRows(element: ElementWithLines, domainId: string) {
    return payload(element)?.domains[domainId]?.rows ?? [];
  }

  function propertyValue(element: ElementWithLines, domainId: string, property: string): string {
    const row = domainRows(element, domainId).find((item) => item.property === property);
    if (!row?.value) return '—';
    return `${row.value}${row.unit ? ` ${row.unit}` : ''}`;
  }

  function firstAvailable(element: ElementWithLines, domainId: string, properties: string[]): string {
    for (const property of properties) {
      const value = propertyValue(element, domainId, property);
      if (value !== '—') return value;
    }
    return '—';
  }

  function domainCount(element: ElementWithLines, domainId: string): string {
    return String(payload(element)?.domains[domainId]?.row_count ?? 0);
  }

  function propertyCount(element: ElementWithLines, domainId: string, predicate: (property: string) => boolean): string {
    return String(domainRows(element, domainId).filter((row) => predicate(String(row.property ?? ''))).length);
  }

  function estimateNeutrons(element: ElementWithLines): string {
    const mass = Number.parseFloat(propertyValue(element, 'atomic', 'atomic_mass').replace(',', '.'));
    return Number.isFinite(mass) ? String(Math.max(0, Math.round(mass) - element.atomic_number)) : '—';
  }

  function shellText(element: ElementWithLines): string {
    const capacities = [2, 8, 18, 32, 32, 18, 8];
    let remaining = element.atomic_number;
    const result: number[] = [];
    for (const capacity of capacities) {
      if (remaining <= 0) break;
      const count = Math.min(capacity, remaining);
      result.push(count);
      remaining -= count;
    }
    return result.join(' · ');
  }

  function stableIsotopeCount(element: ElementWithLines): string {
    return String(domainRows(element, 'isotopes').filter((row) => String(row.half_life ?? '').toUpperCase() === 'STABLE').length);
  }

  function naturalIsotopeCount(element: ElementWithLines): string {
    return String(domainRows(element, 'isotopes').filter((row) => Number.parseFloat(String(row.abundance ?? '0')) > 0).length);
  }

  function rowsFor(currentScope: ComparisonScope): MatrixRow[] {
    const common: MatrixRow[] = [
      { label: 'Número atómico', value: (element) => String(element.atomic_number) },
      { label: 'Grupo', value: (element) => element.group ? String(element.group) : '—' },
      { label: 'Periodo', value: (element) => String(element.period) },
      { label: 'Bloque', value: (element) => element.block || '—' },
      { label: 'Categoría', value: (element) => element.category }
    ];

    if (currentScope === 'atom') {
      return [
        ...common.slice(0, 1),
        { label: 'Protones', value: (element) => String(element.atomic_number) },
        { label: 'Neutrones estimados', value: estimateNeutrons },
        { label: 'Electrones', value: (element) => String(element.atomic_number) },
        { label: 'Capas', value: shellText },
        { label: 'Configuración', value: (element) => propertyValue(element, 'atomic', 'electron_configuration') }
      ];
    }

    if (currentScope === 'electronic') {
      return [
        ...common.slice(0, 1),
        { label: 'Configuración', value: (element) => propertyValue(element, 'atomic', 'electron_configuration') },
        { label: 'Configuración de valencia', value: (element) => propertyValue(element, 'atomic', 'valence_shell_configuration') },
        { label: 'Electrones exteriores', value: (element) => propertyValue(element, 'atomic', 'outer_shell_electron_count') },
        { label: 'Electrones de valencia', value: (element) => propertyValue(element, 'atomic', 'valence_electron_count') },
        { label: 'Valencias comunes', value: (element) => propertyValue(element, 'atomic', 'common_valences') },
        { label: 'Estados de oxidación', value: (element) => propertyValue(element, 'chemical', 'oxidation_states') },
        { label: 'Primera ionización', value: (element) => firstAvailable(element, 'atomic', ['ionization_energy_1', 'ionization_energy']) },
        { label: 'Segunda ionización', value: (element) => propertyValue(element, 'atomic', 'ionization_energy_2') },
        { label: 'Tercera ionización', value: (element) => propertyValue(element, 'atomic', 'ionization_energy_3') }
      ];
    }

    if (currentScope === 'radii') {
      return [
        ...common.slice(0, 1),
        { label: 'Van der Waals', value: (element) => firstAvailable(element, 'atomic', ['van_der_waals_radius', 'atomic_radius']) },
        { label: 'Covalente', value: (element) => propertyValue(element, 'atomic', 'covalent_radius') },
        { label: 'Metálico', value: (element) => propertyValue(element, 'atomic', 'metallic_radius') },
        { label: 'Cristalino', value: (element) => propertyValue(element, 'atomic', 'crystal_radius') },
        { label: 'Registros iónicos', value: (element) => propertyCount(element, 'atomic', (property) => property.startsWith('ionic_radius_')) }
      ];
    }

    if (currentScope === 'crystal') {
      return [
        ...common.slice(0, 1),
        { label: 'Estructura', value: (element) => propertyValue(element, 'materials', 'crystal_structure') },
        { label: 'Grupo espacial', value: (element) => propertyValue(element, 'materials', 'space_group') },
        { label: 'Parámetro a', value: (element) => propertyValue(element, 'materials', 'lattice_a') },
        { label: 'Parámetro b', value: (element) => propertyValue(element, 'materials', 'lattice_b') },
        { label: 'Parámetro c', value: (element) => propertyValue(element, 'materials', 'lattice_c') },
        { label: 'Registros de materiales', value: (element) => domainCount(element, 'materials') }
      ];
    }

    if (currentScope === 'nuclear') {
      return [
        ...common.slice(0, 1),
        { label: 'Nucleídos registrados', value: (element) => domainCount(element, 'isotopes') },
        { label: 'Isótopos estables', value: stableIsotopeCount },
        { label: 'Con abundancia natural', value: naturalIsotopeCount },
        { label: 'Momentos magnéticos disponibles', value: (element) => String(domainRows(element, 'isotopes').filter((row) => row.magnetic_dipole).length) },
        { label: 'Cuadrupolos disponibles', value: (element) => String(domainRows(element, 'isotopes').filter((row) => row.electric_quadrupole).length) },
        { label: 'Energías Q disponibles', value: (element) => String(domainRows(element, 'isotopes').filter((row) => row.qa || row.qec || row.qbm).length) }
      ];
    }

    if (currentScope === 'thermodynamics') {
      return [
        ...common.slice(0, 1),
        { label: 'Estado estándar', value: (element) => firstAvailable(element, 'thermodynamics', ['standard_state']) },
        { label: 'Fusión', value: (element) => firstAvailable(element, 'thermodynamics', ['melting_point']) },
        { label: 'Ebullición', value: (element) => firstAvailable(element, 'thermodynamics', ['boiling_point']) },
        { label: 'Entalpía de fusión', value: (element) => firstAvailable(element, 'thermodynamics', ['enthalpy_fusion']) },
        { label: 'Entalpía de vaporización', value: (element) => firstAvailable(element, 'thermodynamics', ['enthalpy_vaporization']) },
        { label: 'Capacidad calorífica', value: (element) => firstAvailable(element, 'thermodynamics', ['heat_capacity_cp', 'specific_heat']) },
        { label: 'Punto triple', value: (element) => firstAvailable(element, 'thermodynamics', ['triple_point', 'triple_point_temperature']) },
        { label: 'Punto crítico', value: (element) => firstAvailable(element, 'thermodynamics', ['critical_temperature']) }
      ];
    }

    if (currentScope === 'radiation') {
      return [
        ...common.slice(0, 1),
        { label: 'Líneas características X', value: (element) => propertyCount(element, 'radiation', (property) => property === 'xray_transition_energy') },
        { label: 'Puntos de atenuación', value: (element) => propertyCount(element, 'radiation', (property) => property === 'mass_attenuation_coefficient') },
        { label: 'Líneas XPS', value: (element) => propertyCount(element, 'radiation', (property) => property === 'xps_binding_energy') },
        { label: 'Líneas Auger', value: (element) => propertyCount(element, 'radiation', (property) => property === 'auger_line_energy') },
        { label: 'Registros neutrónicos', value: (element) => propertyCount(element, 'radiation', (property) => property.startsWith('neutron_')) },
        { label: 'Absorción neutrónica', value: (element) => firstAvailable(element, 'radiation', ['neutron_absorption_cross_section']) }
      ];
    }

    const properties: MatrixRow[] = [
      { label: 'Masa atómica', value: (element) => propertyValue(element, 'atomic', 'atomic_mass') },
      { label: 'Peso CIAAW', value: (element) => propertyValue(element, 'atomic', 'standard_atomic_weight') },
      { label: 'Configuración electrónica', value: (element) => propertyValue(element, 'atomic', 'electron_configuration') },
      { label: 'Electronegatividad', value: (element) => propertyValue(element, 'atomic', 'electronegativity') },
      { label: 'Radio Van der Waals', value: (element) => firstAvailable(element, 'atomic', ['van_der_waals_radius', 'atomic_radius']) },
      { label: 'Ionización', value: (element) => firstAvailable(element, 'atomic', ['ionization_energy_1', 'ionization_energy']) },
      { label: 'Estado estándar', value: (element) => propertyValue(element, 'physical', 'standard_state') },
      { label: 'Densidad', value: (element) => propertyValue(element, 'physical', 'density') },
      { label: 'Fusión', value: (element) => propertyValue(element, 'physical', 'melting_point') },
      { label: 'Ebullición', value: (element) => propertyValue(element, 'physical', 'boiling_point') }
    ];

    if (currentScope === 'properties') return properties;
    if (currentScope === 'summary') return [...common, ...properties.slice(0, 6)];
    return [
      ...common,
      ...properties,
      { label: 'Isótopos', value: (element) => domainCount(element, 'isotopes') },
      { label: 'Líneas espectrales', value: (element) => String(element.lines.length) },
      { label: 'Niveles NIST', value: (element) => domainCount(element, 'nist_levels') },
      { label: 'Termodinámica', value: (element) => domainCount(element, 'thermodynamics') },
      { label: 'Radiación', value: (element) => domainCount(element, 'radiation') },
      { label: 'Bloques con datos', value: (element) => String(element.dataIndex?.available_file_count ?? 0) }
    ];
  }

  function lineLeft(wavelength: number): number {
    return Math.max(0, Math.min(100, ((wavelength - 320) / 460) * 100));
  }

  function lineTitle(line: SpectralLine): string {
    return `${line.label}: ${formatNm(line.wavelength_nm)}`;
  }

  function scopeDomains(currentScope: ComparisonScope): string[] {
    if (currentScope === 'isotopes') return ['isotopes'];
    if (currentScope === 'levels') return ['nist_levels'];
    if (currentScope === 'chemistry') return ['chemical', 'materials', 'thermodynamics', 'compounds', 'computational'];
    if (currentScope === 'context') return ['history', 'geochemistry', 'astrophysics', 'biology', 'environment', 'industry', 'analytical', 'radiation'];
    if (currentScope === 'sources') return ['sources'];
    return [];
  }
</script>

<section class="compare-card comparison-workspace">
  <header class="comparison-header">
    <div>
      <p class="eyebrow">Comparador total</p>
      <strong>{selected.length} elementos · {scopes.find((item) => item.id === scope)?.label}</strong>
    </div>
    <div class="comparison-header-actions">
      <button type="button" on:click={() => dispatch('clear')}>Cerrar y limpiar</button>
    </div>
  </header>

  <nav class="comparison-scopes" aria-label="Ámbito de comparación">
    {#each scopes as item}
      <button class:active={scope === item.id} type="button" on:click={() => dispatch('scope', item.id)}>{item.label}</button>
    {/each}
  </nav>

  <div class="comparison-selection" aria-label="Elementos seleccionados">
    {#each selected as element}
      <button type="button" on:click={() => dispatch('remove', element.symbol)} title={`Quitar ${element.name_es}`}>
        <b>{element.symbol}</b><span>{element.name_es}</span><i>×</i>
      </button>
    {/each}
  </div>

  <div class="comparison-body">
    {#if scope === 'spectrum' || scope === 'lines'}
      <div class="comparison-spectra">
        {#each selected as element}
          <article>
            <header><b>{element.symbol}</b><span>{element.name_es}</span><small>{element.lines.length} líneas</small></header>
            <div class="comparison-spectrum-track">
              {#each element.lines as line}
                <span style={`left:${lineLeft(line.wavelength_nm)}%;opacity:${0.24 + line.intensity * 0.76};--line-color:${line.approximate_color};`} title={lineTitle(line)}></span>
              {/each}
            </div>
            {#if scope === 'lines'}
              <div class="comparison-strong-lines">
                {#each getStrongestLines(element.lines, 8) as line}
                  <span><i style={`--line-color:${line.approximate_color};`}></i>{formatNm(line.wavelength_nm)}</span>
                {/each}
              </div>
            {/if}
          </article>
        {/each}
      </div>
    {:else if ['isotopes', 'levels', 'chemistry', 'context', 'sources'].includes(scope)}
      <div class="comparison-domain-grid">
        {#each selected as element}
          <article>
            <header><b>{element.symbol}</b><span>{element.name_es}</span></header>
            {#each scopeDomains(scope) as domainId}
              {@const domain = payload(element)?.domains[domainId]}
              <div><span>{domain?.label ?? domainId}</span><strong>{domain?.row_count ?? 0}</strong></div>
            {/each}
          </article>
        {/each}
      </div>
    {:else}
      <div class="comparison-matrix-wrap">
        <table class="comparison-matrix">
          <thead>
            <tr><th>Propiedad</th>{#each selected as element}<th><b>{element.symbol}</b><span>{element.name_es}</span></th>{/each}</tr>
          </thead>
          <tbody>
            {#each matrixRows as row}
              <tr><th>{row.label}</th>{#each selected as element}<td>{row.value(element)}</td>{/each}</tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</section>
