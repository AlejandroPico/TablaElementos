<script lang="ts">
  import type { ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elements: ElementWithLines[] = [];

  interface TrendDefinition {
    key: string;
    label: string;
    unit: string;
  }

  const definitions: TrendDefinition[] = [
    { key: 'atomic_mass', label: 'Masa atómica', unit: 'u' },
    { key: 'electronegativity', label: 'Electronegatividad', unit: 'Pauling' },
    { key: 'ionization_energy', label: 'Primera ionización', unit: 'kJ/mol' },
    { key: 'electron_affinity', label: 'Afinidad electrónica', unit: 'kJ/mol' },
    { key: 'atomic_radius', label: 'Radio atómico', unit: 'pm' },
    { key: 'melting_point', label: 'Punto de fusión', unit: 'K' },
    { key: 'boiling_point', label: 'Punto de ebullición', unit: 'K' },
    { key: 'density', label: 'Densidad', unit: 'g/cm³' },
    { key: 'specific_heat', label: 'Calor específico', unit: 'J/(g·K)' },
    { key: 'thermal_conductivity', label: 'Conductividad térmica', unit: 'W/(m·K)' },
    { key: 'electrical_conductivity', label: 'Conductividad eléctrica', unit: 'MS/m' },
    { key: 'electrical_resistivity', label: 'Resistividad eléctrica', unit: 'Ω·m' },
    { key: 'young_modulus', label: 'Módulo de Young', unit: 'GPa' },
    { key: 'shear_modulus', label: 'Módulo de cizallamiento', unit: 'GPa' },
    { key: 'bulk_modulus', label: 'Módulo volumétrico', unit: 'GPa' },
    { key: 'abundance_universe', label: 'Abundancia en el Universo', unit: '%' },
    { key: 'abundance_crust', label: 'Abundancia en la corteza', unit: '%' },
    { key: 'abundance_ocean', label: 'Abundancia en el océano', unit: '%' },
    { key: 'abundance_human', label: 'Abundancia en el cuerpo humano', unit: '%' },
    { key: 'relative_supply_risk', label: 'Riesgo de suministro', unit: '1–10' },
    { key: 'price_per_kg', label: 'Precio orientativo', unit: 'USD/kg' },
    { key: 'spectral_line_count', label: 'Líneas espectrales', unit: 'registros' },
    { key: 'isotope_count', label: 'Nucleídos registrados', unit: 'registros' },
    { key: 'level_count', label: 'Niveles NIST', unit: 'registros' },
  ];

  let propertyKey = 'electronegativity';

  function numeric(item: ElementWithLines): number | null {
    if (propertyKey === 'spectral_line_count') return item.lines.length;
    const value = item.dataIndex?.filter_values?.[propertyKey];
    return typeof value === 'number' && Number.isFinite(value) ? value : null;
  }

  $: definition = definitions.find((item) => item.key === propertyKey) ?? definitions[0];
  $: values = elements
    .map((item) => ({ element: item, value: numeric(item) }))
    .filter((item): item is { element: ElementWithLines; value: number } => item.value !== null);
  $: positiveValues = values.map((item) => item.value).filter((value) => value > 0);
  $: useLog = positiveValues.length > 1 && Math.max(...positiveValues) / Math.min(...positiveValues) >= 1000;
  $: transformed = values.map((item) => ({ ...item, plot: useLog && item.value > 0 ? Math.log10(item.value) : item.value }));
  $: minPlot = transformed.length ? Math.min(...transformed.map((item) => item.plot)) : 0;
  $: maxPlot = transformed.length ? Math.max(...transformed.map((item) => item.plot)) : 1;
  $: points = transformed.map((item) => ({
    ...item,
    x: 48 + ((item.element.atomic_number - 1) / 117) * 624,
    y: maxPlot === minPlot ? 132 : 224 - ((item.plot - minPlot) / (maxPlot - minPlot)) * 184,
  }));
  $: selected = points.find((point) => point.element.symbol === element?.symbol) ?? null;
  $: ordered = [...values].sort((a, b) => a.value - b.value);
  $: rank = selected ? ordered.findIndex((item) => item.element.symbol === selected.element.symbol) + 1 : 0;
</script>

<div class="advanced-science-pane element-trends-pane">
  <div class="trend-inline-toolbar">
    <label>
      <span>Propiedad</span>
      <select bind:value={propertyKey}>
        {#each definitions as item}<option value={item.key}>{item.label}</option>{/each}
      </select>
    </label>
    <p><strong>{values.length}</strong>/118 datos · escala {useLog ? 'logarítmica' : 'lineal'}</p>
  </div>

  {#if points.length}
    <section class="flat-science-section trend-element-chart">
      <header><div><small>Comparación frente al número atómico</small><h3>{definition.label}</h3></div><span>{definition.unit}</span></header>
      <svg viewBox="0 0 720 270" role="img" aria-label={`${definition.label} frente a Z`}>
        <g class="chart-grid">{#each [40, 86, 132, 178, 224] as y}<line x1="48" x2="672" y1={y} y2={y}></line>{/each}</g>
        <polyline points={points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' ')}></polyline>
        {#each points as point}
          <circle class:selected={point.element.symbol === element?.symbol} cx={point.x} cy={point.y} r={point.element.symbol === element?.symbol ? 6 : 2.7}>
            <title>{point.element.symbol} · {point.value.toLocaleString('es-ES')} {definition.unit}</title>
          </circle>
        {/each}
        <text x="360" y="262" text-anchor="middle">Número atómico Z</text>
      </svg>
    </section>

    <dl class="trend-current-reading">
      <div><dt>Elemento</dt><dd>{element?.name_es} ({element?.symbol})</dd></div>
      <div><dt>Valor</dt><dd>{selected ? `${selected.value.toLocaleString('es-ES')} ${definition.unit}` : 'Sin dato'}</dd></div>
      <div><dt>Posición entre datos disponibles</dt><dd>{rank ? `${rank} de ${ordered.length}` : '—'}</dd></div>
      <div><dt>Cobertura</dt><dd>{values.length} de 118 elementos</dd></div>
    </dl>
  {:else}
    <div class="science-empty-state"><strong>Sin valores normalizados</strong><p>La propiedad no se representa hasta disponer de datos trazables.</p></div>
  {/if}
</div>
