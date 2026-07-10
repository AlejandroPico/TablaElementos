<script lang="ts">
  import type { ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';
  import { formatEv, formatNm, wavelengthRegion } from '../lib/wavelengthColor';
  import { getStrongestLines } from '../lib/filters';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;
  export let loadingData = false;

  $: strongest = element ? getStrongestLines(element.lines, 5) : [];
  $: availableDomains = elementData
    ? Object.values(elementData.domains).filter((domain) => domain.available)
    : [];

  function propertyValue(domainId: string, property: string): string {
    const rows = elementData?.domains[domainId]?.rows ?? [];
    const match = rows.find((row) => row.property === property);
    if (!match) return '—';
    return `${match.value || '—'}${match.unit ? ` ${match.unit}` : ''}`;
  }

  function domainState(domainId: string): string {
    if (loadingData) return 'Cargando';
    const domain = elementData?.domains[domainId];
    return domain?.available ? `${domain.row_count.toLocaleString('es-ES')} registros` : 'Pendiente';
  }
</script>

<aside class="element-panel master-summary">
  {#if element}
    <div class="element-hero">
      <div class="element-symbol">
        <span>{element.atomic_number}</span>
        <strong>{element.symbol}</strong>
      </div>
      <div>
        <p class="eyebrow">Ficha maestra · {element.category}</p>
        <h2>{element.name_es}</h2>
        <p>{element.summary}</p>
      </div>
    </div>

    <div class="stat-grid master-stats enriched-stats">
      <div><span>Masa atómica</span><strong>{propertyValue('atomic', 'atomic_mass')}</strong></div>
      <div><span>Peso CIAAW</span><strong>{propertyValue('atomic', 'standard_atomic_weight')}</strong></div>
      <div><span>Configuración electrónica</span><strong>{propertyValue('atomic', 'electron_configuration')}</strong></div>
      <div><span>Electronegatividad</span><strong>{propertyValue('atomic', 'electronegativity')}</strong></div>
      <div><span>Estado estándar</span><strong>{propertyValue('physical', 'standard_state')}</strong></div>
      <div><span>Densidad</span><strong>{propertyValue('physical', 'density')}</strong></div>
      <div><span>Fusión</span><strong>{propertyValue('physical', 'melting_point')}</strong></div>
      <div><span>Ebullición</span><strong>{propertyValue('physical', 'boiling_point')}</strong></div>
    </div>

    <section class="coverage-section">
      <div class="section-title-row compact">
        <div>
          <p class="eyebrow">Cobertura del elemento</p>
          <h3>Datos incorporados al proyecto</h3>
        </div>
        <span class="range-pill">{availableDomains.length} bloques con datos</span>
      </div>

      <div class="coverage-grid">
        <article class:available={elementData?.domains.identity?.available}>
          <span>Identidad</span><strong>{domainState('identity')}</strong>
        </article>
        <article class:available={elementData?.domains.atomic?.available}>
          <span>Propiedades atómicas</span><strong>{domainState('atomic')}</strong>
        </article>
        <article class:available={elementData?.domains.physical?.available}>
          <span>Propiedades físicas</span><strong>{domainState('physical')}</strong>
        </article>
        <article class:available={elementData?.domains.chemical?.available}>
          <span>Química</span><strong>{domainState('chemical')}</strong>
        </article>
        <article class:available={elementData?.domains.isotopes?.available}>
          <span>Isótopos</span><strong>{domainState('isotopes')}</strong>
        </article>
        <article class:available={element.lines.length > 0}>
          <span>Líneas espectrales</span><strong>{element.lines.length.toLocaleString('es-ES')} interpretadas</strong>
        </article>
        <article class:available={elementData?.domains.nist_levels?.available}>
          <span>Niveles NIST</span><strong>{domainState('nist_levels')}</strong>
        </article>
        <article class:available={elementData?.domains.history?.available}>
          <span>Historia</span><strong>{domainState('history')}</strong>
        </article>
        <article class:available={elementData?.domains.sources?.available}>
          <span>Fuentes</span><strong>{domainState('sources')}</strong>
        </article>
      </div>
    </section>

    <section class="strong-lines-section">
      <div class="section-title-row compact">
        <div><p class="eyebrow">Vista rápida</p><h3>Líneas más intensas</h3></div>
        <span class="range-pill">{element.lines.length} líneas</span>
      </div>

      {#if strongest.length}
        <div class="line-table">
          {#each strongest as line}
            <article>
              <span class="line-swatch" style={`background:${line.approximate_color};`}></span>
              <div>
                <strong>{line.label}</strong>
                <small>{formatNm(line.wavelength_nm)} · {wavelengthRegion(line.wavelength_nm)} · ΔE {formatEv(line.upper_level_ev - line.lower_level_ev)}</small>
              </div>
            </article>
          {/each}
        </div>
      {:else}
        <p class="empty-copy master-empty">No hay líneas espectrales interpretadas para este elemento.</p>
      {/if}
    </section>
  {:else}
    <div class="empty-panel">
      <h2>Selecciona un elemento</h2>
      <p>La ficha maestra reúne identidad, propiedades, isótopos, espectros, materiales, seguridad, historia y fuentes.</p>
    </div>
  {/if}
</aside>
