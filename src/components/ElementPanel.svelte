<script lang="ts">
  import type { ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  interface SummaryFact {
    label: string;
    value: string;
    wide?: boolean;
  }

  interface PropertyLocation {
    domain: string;
    properties: string[];
  }

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;
  export let loadingData = false;

  function propertyValue(payload: ElementDataPayload | null, domainId: string, property: string): string {
    const rows = payload?.domains[domainId]?.rows ?? [];
    const match = rows.find((row) => row.property === property);
    if (!match) return '—';
    const value = String(match.value ?? '').trim();
    const unit = String(match.unit ?? '').trim();
    if (!value) return '—';
    return unit ? `${value} ${unit}` : value;
  }

  function firstProperty(payload: ElementDataPayload | null, domainId: string, properties: string[]): string {
    for (const property of properties) {
      const value = propertyValue(payload, domainId, property);
      if (value !== '—') return value;
    }
    return '—';
  }

  function firstAcross(payload: ElementDataPayload | null, locations: PropertyLocation[]): string {
    for (const location of locations) {
      const value = firstProperty(payload, location.domain, location.properties);
      if (value !== '—') return value;
    }
    return '—';
  }

  function stableCount(payload: ElementDataPayload | null): string {
    const rows = payload?.domains.isotopes?.rows ?? [];
    return String(rows.filter((row) => String(row.half_life ?? '').toUpperCase() === 'STABLE').length);
  }

  function propertyCount(payload: ElementDataPayload | null, domainId: string, prefix: string): string {
    const rows = payload?.domains[domainId]?.rows ?? [];
    return String(rows.filter((row) => String(row.property ?? '').startsWith(prefix)).length);
  }

  function buildSummaryFacts(payload: ElementDataPayload | null): SummaryFact[] {
    if (!element) return [];
    return [
      { label: 'Número atómico', value: String(element.atomic_number) },
      { label: 'Grupo', value: element.group ? String(element.group) : '—' },
      { label: 'Periodo', value: String(element.period) },
      { label: 'Bloque', value: element.block || '—' },
      { label: 'Categoría', value: element.category },
      { label: 'Masa atómica', value: propertyValue(payload, 'atomic', 'atomic_mass') },
      { label: 'Peso atómico CIAAW', value: propertyValue(payload, 'atomic', 'standard_atomic_weight') },
      { label: 'Configuración electrónica', value: propertyValue(payload, 'atomic', 'electron_configuration'), wide: true },
      { label: 'Configuración de valencia', value: propertyValue(payload, 'atomic', 'valence_shell_configuration'), wide: true },
      { label: 'Electrones de valencia', value: propertyValue(payload, 'atomic', 'valence_electron_count') },
      { label: 'Valencias comunes', value: propertyValue(payload, 'atomic', 'common_valences') },
      { label: 'Estados de oxidación', value: propertyValue(payload, 'chemical', 'oxidation_states') },
      { label: 'Electronegatividad', value: propertyValue(payload, 'atomic', 'electronegativity') },
      { label: 'Radio de Van der Waals', value: firstProperty(payload, 'atomic', ['van_der_waals_radius', 'atomic_radius']) },
      { label: 'Radio covalente', value: propertyValue(payload, 'atomic', 'covalent_radius') },
      { label: 'Primera ionización', value: firstProperty(payload, 'atomic', ['ionization_energy_1', 'ionization_energy']) },
      { label: 'Afinidad electrónica', value: propertyValue(payload, 'atomic', 'electron_affinity') },
      {
        label: 'Estado estándar',
        value: firstAcross(payload, [
          { domain: 'thermodynamics', properties: ['standard_state'] },
          { domain: 'physical', properties: ['standard_state', 'phase', 'state'] }
        ])
      },
      { label: 'Densidad', value: propertyValue(payload, 'physical', 'density') },
      {
        label: 'Punto de fusión',
        value: firstAcross(payload, [
          { domain: 'thermodynamics', properties: ['melting_point'] },
          { domain: 'physical', properties: ['melting_point'] }
        ])
      },
      {
        label: 'Punto de ebullición',
        value: firstAcross(payload, [
          { domain: 'thermodynamics', properties: ['boiling_point'] },
          { domain: 'physical', properties: ['boiling_point'] }
        ])
      },
      { label: 'Entalpía de fusión', value: firstProperty(payload, 'thermodynamics', ['enthalpy_fusion']) },
      { label: 'Entalpía de vaporización', value: firstProperty(payload, 'thermodynamics', ['enthalpy_vaporization']) },
      { label: 'Estructura cristalina', value: propertyValue(payload, 'materials', 'crystal_structure') },
      { label: 'Grupo espacial', value: propertyValue(payload, 'materials', 'space_group') },
      { label: 'Nucleídos registrados', value: String(payload?.domains.isotopes?.row_count ?? 0) },
      { label: 'Isótopos estables', value: stableCount(payload) },
      { label: 'Líneas de rayos X', value: propertyCount(payload, 'radiation', 'xray_transition_energy') },
      { label: 'Registros de atenuación', value: propertyCount(payload, 'radiation', 'mass_attenuation_coefficient') },
      { label: 'Registros neutrónicos', value: propertyCount(payload, 'radiation', 'neutron_') },
      { label: 'Líneas espectrales ópticas', value: String(element.lines.length) },
      { label: 'Niveles NIST', value: String(payload?.domains.nist_levels?.row_count ?? 0) }
    ];
  }

  $: summaryFacts = buildSummaryFacts(elementData);
</script>

<aside class="element-panel master-summary">
  {#if element}
    <section class="summary-introduction compact-summary-introduction">
      <p><strong>Resumen científico</strong><span>—</span>{element.summary}</p>
    </section>

    {#if loadingData}
      <div class="summary-data-loading" aria-live="polite">
        <span></span><p>Cargando propiedades de {element.name_es}…</p>
      </div>
    {:else}
      <section class="summary-sheet" aria-label={`Resumen de ${element.name_es}`}>
        <header class="inline-summary-header">
          <div><strong>Ficha esencial</strong><span>—</span><small>Identidad, estructura, termodinámica, núcleo y radiación</small></div>
          <i>Datos consolidados desde los CSV locales</i>
        </header>
        <dl class="summary-facts expanded-summary-facts">
          {#each summaryFacts as fact}
            <div class:wide={fact.wide}>
              <dt>{fact.label}</dt>
              <dd class:missing={fact.value === '—'}>{fact.value}</dd>
            </div>
          {/each}
        </dl>
      </section>
    {/if}
  {:else}
    <div class="empty-panel">
      <h2>Selecciona un elemento</h2>
      <p>La ficha reúne identidad, estructura electrónica, cristalografía, termodinámica, núcleo, espectros, radiación, química, contexto y fuentes.</p>
    </div>
  {/if}
</aside>
