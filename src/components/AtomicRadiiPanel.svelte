<script lang="ts">
  import type { DataRow, ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;
  export let loading = false;

  interface RadiusItem {
    id: string;
    label: string;
    value: number;
    unit: string;
    qualifier: string;
    source: string;
  }

  const LABELS: Record<string, string> = {
    van_der_waals_radius: 'Van der Waals',
    covalent_radius: 'Covalente',
    covalent_radius_single: 'Covalente · enlace simple',
    covalent_radius_double: 'Covalente · enlace doble',
    covalent_radius_triple: 'Covalente · enlace triple',
    metallic_radius: 'Metálico',
    crystal_radius: 'Cristalino',
    ionic_radius: 'Iónico',
    atomic_radius: 'Radio publicado por PubChem'
  };

  function parseNumber(value: string): number | null {
    const match = String(value ?? '').replace(',', '.').match(/[-+]?\d+(?:\.\d+)?/);
    if (!match) return null;
    const parsed = Number(match[0]);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function radiusRows(): RadiusItem[] {
    const rows = elementData?.domains.atomic?.rows ?? [];
    return rows.flatMap((row: DataRow) => {
      const id = row.property ?? '';
      if (!(id in LABELS) && !id.startsWith('ionic_radius_')) return [];
      const value = parseNumber(row.value);
      if (value === null) return [];
      const qualifier = [row.oxidation_state, row.coordination_number, row.phase, row.notes]
        .filter(Boolean)
        .join(' · ');
      return [{
        id,
        label: id.startsWith('ionic_radius_') ? 'Iónico' : LABELS[id],
        value,
        unit: row.unit || 'pm',
        qualifier,
        source: row.source || ''
      }];
    });
  }

  function circleRadius(value: number, max: number): number {
    return 24 + Math.sqrt(value / Math.max(max, 1)) * 112;
  }

  $: radii = radiusRows();
  $: maxRadius = Math.max(...radii.map((item) => item.value), 1);
  $: sorted = [...radii].sort((a, b) => b.value - a.value);
</script>

<div class="advanced-science-pane radii-pane">
  {#if loading}
    <div class="modal-load-state"><span></span><p>Cargando radios atómicos…</p></div>
  {:else}
    <section class="science-hero radii-hero">
      <div>
        <p>Geometría atómica</p>
        <h3>Radios y tamaños comparados</h3>
        <small>No existe un único “radio atómico”: cada definición responde a un contexto físico o químico distinto.</small>
      </div>
      <strong class="science-symbol-mark">{element?.symbol}</strong>
    </section>

    {#if radii.length}
      <section class="radii-workspace">
        <div class="radii-concentric" role="img" aria-label={`Comparación proporcional de radios de ${element?.name_es}`}>
          <svg viewBox="0 0 360 360">
            {#each sorted as item, index}
              {@const radius = circleRadius(item.value, maxRadius)}
              <circle class={`radius-circle radius-${index % 6}`} cx="180" cy="180" r={radius}>
                <title>{`${item.label}: ${item.value} ${item.unit}${item.qualifier ? ` · ${item.qualifier}` : ''}`}</title>
              </circle>
            {/each}
            <circle class="radius-nucleus" cx="180" cy="180" r="10"></circle>
            <text x="180" y="186" text-anchor="middle">{element?.symbol}</text>
          </svg>
        </div>

        <div class="radii-list">
          {#each sorted as item, index}
            <article>
              <i class={`radius-swatch radius-${index % 6}`}></i>
              <div><small>{item.label}</small><strong>{item.value.toLocaleString('es-ES')} {item.unit}</strong>{#if item.qualifier}<span>{item.qualifier}</span>{/if}</div>
            </article>
          {/each}
        </div>
      </section>
    {:else}
      <div class="science-empty-state"><strong>Sin radios diferenciados</strong><p>El modelo ya admite radios de Van der Waals, covalentes, metálicos, cristalinos e iónicos con carga y coordinación.</p></div>
    {/if}

    <section class="science-definition-grid">
      <article><strong>Van der Waals</strong><p>Aproximación de contacto entre átomos no enlazados.</p></article>
      <article><strong>Covalente</strong><p>Mitad de la distancia internuclear en un enlace, dependiente del orden de enlace.</p></article>
      <article><strong>Metálico</strong><p>Mitad de la distancia entre vecinos en una red metálica.</p></article>
      <article><strong>Iónico</strong><p>Depende de carga, coordinación, estado de espín y parametrización.</p></article>
    </section>

    <p class="science-method-note">La circunferencia es proporcional a la raíz del valor para conservar legibilidad. No representa una frontera cuántica rígida de la nube electrónica.</p>
  {/if}
</div>
