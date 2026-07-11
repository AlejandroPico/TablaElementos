<script lang="ts">
  import type { ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  interface SummaryFact {
    label: string;
    value: string;
    wide?: boolean;
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
      { label: 'Electronegatividad', value: propertyValue(payload, 'atomic', 'electronegativity') },
      { label: 'Radio atómico', value: propertyValue(payload, 'atomic', 'atomic_radius') },
      { label: 'Primera ionización', value: propertyValue(payload, 'atomic', 'ionization_energy') },
      { label: 'Afinidad electrónica', value: propertyValue(payload, 'atomic', 'electron_affinity') },
      { label: 'Estado estándar', value: propertyValue(payload, 'physical', 'standard_state') },
      { label: 'Densidad', value: propertyValue(payload, 'physical', 'density') },
      { label: 'Punto de fusión', value: propertyValue(payload, 'physical', 'melting_point') },
      { label: 'Punto de ebullición', value: propertyValue(payload, 'physical', 'boiling_point') },
      { label: 'Isótopos registrados', value: String(payload?.domains.isotopes?.row_count ?? 0) },
      { label: 'Líneas espectrales', value: String(element.lines.length) },
      { label: 'Niveles NIST', value: String(payload?.domains.nist_levels?.row_count ?? 0) }
    ];
  }

  $: summaryFacts = buildSummaryFacts(elementData);
</script>

<aside class="element-panel master-summary">
  {#if element}
    <section class="summary-introduction">
      <p class="eyebrow">Resumen científico</p>
      <p class="summary-description">{element.summary}</p>
    </section>

    {#if loadingData}
      <div class="summary-data-loading" aria-live="polite">
        <span></span><p>Cargando propiedades de {element.name_es}…</p>
      </div>
    {:else}
      <section class="summary-sheet" aria-label={`Resumen de ${element.name_es}`}>
        <header>
          <div><p class="eyebrow">Ficha esencial</p><h3>Identidad, estructura y propiedades principales</h3></div>
          <small>Datos consolidados desde los CSV locales</small>
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
      <p>La ficha reúne identidad, propiedades, isótopos, espectros, química, contexto y fuentes.</p>
    </div>
  {/if}
</aside>
