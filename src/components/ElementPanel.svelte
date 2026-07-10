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

  function propertyValue(
    payload: ElementDataPayload | null,
    domainId: string,
    property: string
  ): string {
    const rows = payload?.domains[domainId]?.rows ?? [];
    const match = rows.find((row) => row.property === property);
    if (!match) return '—';

    const value = String(match.value ?? '').trim();
    const unit = String(match.unit ?? '').trim();
    if (!value) return '—';
    return unit ? `${value} ${unit}` : value;
  }

  function buildSummaryFacts(payload: ElementDataPayload | null): SummaryFact[] {
    return [
      { label: 'Masa atómica', value: propertyValue(payload, 'atomic', 'atomic_mass') },
      { label: 'Peso atómico CIAAW', value: propertyValue(payload, 'atomic', 'standard_atomic_weight') },
      {
        label: 'Configuración electrónica',
        value: propertyValue(payload, 'atomic', 'electron_configuration'),
        wide: true
      },
      { label: 'Electronegatividad', value: propertyValue(payload, 'atomic', 'electronegativity') },
      { label: 'Radio atómico', value: propertyValue(payload, 'atomic', 'atomic_radius') },
      { label: 'Primera ionización', value: propertyValue(payload, 'atomic', 'ionization_energy') },
      { label: 'Afinidad electrónica', value: propertyValue(payload, 'atomic', 'electron_affinity') },
      { label: 'Estado estándar', value: propertyValue(payload, 'physical', 'standard_state') },
      { label: 'Densidad', value: propertyValue(payload, 'physical', 'density') },
      { label: 'Punto de fusión', value: propertyValue(payload, 'physical', 'melting_point') },
      { label: 'Punto de ebullición', value: propertyValue(payload, 'physical', 'boiling_point') }
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
        <span></span>
        <p>Cargando propiedades de {element.name_es}…</p>
      </div>
    {:else}
      <section class="summary-sheet" aria-label={`Propiedades principales de ${element.name_es}`}>
        <header>
          <div>
            <p class="eyebrow">Datos principales</p>
            <h3>Identidad atómica y propiedades físicas</h3>
          </div>
          <small>Valores procedentes de los CSV locales del proyecto</small>
        </header>

        <dl class="summary-facts">
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
