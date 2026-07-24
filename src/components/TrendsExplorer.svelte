<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ElementWithLines } from '../lib/atomicTypes';

  export let open = false;
  export let elements: ElementWithLines[] = [];

  type ViewMode = 'line' | 'table';
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
    { key: 'atomic_radius', label: 'Radio', unit: 'pm' },
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
    { key: 'isotope_count', label: 'Nucleídos registrados', unit: 'recuento' },
    { key: 'level_count', label: 'Niveles NIST', unit: 'recuento' },
  ];

  let propertyKey = 'electronegativity';
  let viewMode: ViewMode = 'line';
  const dispatch = createEventDispatcher<{ close: void; open: string }>();

  function numeric(element: ElementWithLines): number | null {
    const value = element.dataIndex?.filter_values?.[propertyKey];
    return typeof value === 'number' && Number.isFinite(value) ? value : null;
  }

  function position(element: ElementWithLines): { column: number; row: number } {
    const z = element.atomic_number;
    if (z >= 58 && z <= 71) return { column: 4 + (z - 58), row: 8 };
    if (z >= 90 && z <= 103) return { column: 4 + (z - 90), row: 9 };
    return { column: Math.max(1, element.group || 1), row: Math.max(1, element.period || 1) };
  }

  function closeOnBackdrop(event: MouseEvent): void {
    if (event.currentTarget === event.target) dispatch('close');
  }

  $: definition = definitions.find((item) => item.key === propertyKey) ?? definitions[0];
  $: values = elements
    .map((element) => ({ element, value: numeric(element) }))
    .filter((item): item is { element: ElementWithLines; value: number } => item.value !== null);
  $: positiveValues = values.map((item) => item.value).filter((value) => value > 0);
  $: sortedValues = [...values].sort((a, b) => a.value - b.value);
  $: useLog = positiveValues.length > 1 && Math.max(...positiveValues) / Math.min(...positiveValues) >= 1000;
  $: transformed = values.map((item) => ({ ...item, plot: useLog && item.value > 0 ? Math.log10(item.value) : item.value }));
  $: minPlot = transformed.length ? Math.min(...transformed.map((item) => item.plot)) : 0;
  $: maxPlot = transformed.length ? Math.max(...transformed.map((item) => item.plot)) : 1;
  $: linePoints = transformed.map((item) => ({
    ...item,
    x: 44 + ((item.element.atomic_number - 1) / 117) * 632,
    y: maxPlot === minPlot ? 130 : 224 - ((item.plot - minPlot) / (maxPlot - minPlot)) * 184,
  }));

  function color(value: number | null): string {
    if (value === null) return 'transparent';
    const plot = useLog && value > 0 ? Math.log10(value) : value;
    const ratio = maxPlot === minPlot ? 0.65 : Math.max(0, Math.min(1, (plot - minPlot) / (maxPlot - minPlot)));
    return `color-mix(in srgb, var(--accent) ${18 + ratio * 78}%, var(--panel-strong))`;
  }
</script>

{#if open}
  <div class="trends-backdrop" role="presentation" on:click={closeOnBackdrop}>
    <div class="trends-modal" role="dialog" aria-modal="true" aria-label="Explorador global de tendencias">
      <header>
        <div><p>Exploración periódica</p><h2>Tendencias globales</h2><small>Selecciona una propiedad normalizada y compárala frente a Z o sobre la geometría periódica.</small></div>
        <button type="button" aria-label="Cerrar tendencias" on:click={() => dispatch('close')}>×</button>
      </header>

      <div class="trends-controls">
        <label><span>Propiedad</span><select bind:value={propertyKey}>{#each definitions as item}<option value={item.key}>{item.label}</option>{/each}</select></label>
        <div class="segmented-control small">
          <button class:active={viewMode === 'line'} type="button" on:click={() => (viewMode = 'line')}>Frente a Z</button>
          <button class:active={viewMode === 'table'} type="button" on:click={() => (viewMode = 'table')}>Tabla coloreada</button>
        </div>
        <span class="trend-scale-badge">{values.length}/118 datos · escala {useLog ? 'logarítmica' : 'lineal'} · {definition.unit}</span>
      </div>

      <div class="trends-stage">
        {#if viewMode === 'line'}
          {#if linePoints.length}
            <svg class="global-trend-chart" viewBox="0 0 720 270" role="img" aria-label={`${definition.label} frente al número atómico`}>
              <g class="chart-grid">{#each [40, 86, 132, 178, 224] as y}<line x1="44" x2="676" y1={y} y2={y}></line>{/each}</g>
              <polyline points={linePoints.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' ')}></polyline>
              {#each linePoints as point}
                <g role="button" tabindex="0" aria-label={`Abrir ${point.element.name_es}`} on:click={() => dispatch('open', point.element.symbol)} on:keydown={(event) => event.key === 'Enter' && dispatch('open', point.element.symbol)}>
                  <circle cx={point.x} cy={point.y} r="4"><title>{point.element.symbol} · {point.value.toLocaleString('es-ES')} {definition.unit}</title></circle>
                </g>
              {/each}
              <text x="360" y="262" text-anchor="middle">Número atómico Z</text>
            </svg>
          {:else}
            <div class="science-empty-state"><strong>Sin datos normalizados</strong><p>La propiedad no se representa hasta disponer de al menos un valor trazable.</p></div>
          {/if}
        {:else}
          <div class="trend-periodic-map" aria-label={`Tabla periódica coloreada por ${definition.label}`}>
            {#each elements as element}
              {@const value = numeric(element)}
              {@const cell = position(element)}
              <button
                class:missing={value === null}
                type="button"
                style={`grid-column:${cell.column};grid-row:${cell.row};--trend-color:${color(value)};`}
                title={`${element.name_es} · ${value === null ? 'sin dato' : `${value.toLocaleString('es-ES')} ${definition.unit}`}`}
                on:click={() => dispatch('open', element.symbol)}
              >
                <small>{element.atomic_number}</small><strong>{element.symbol}</strong><span>{value === null ? '—' : value.toLocaleString('es-ES', { maximumFractionDigits: 2 })}</span>
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <footer><span><i style={`background:${color(sortedValues[0]?.value ?? null)}`}></i>menor</span><span><i style={`background:${color(sortedValues[Math.floor(sortedValues.length / 2)]?.value ?? null)}`}></i>intermedio</span><span><i style={`background:${color(sortedValues.at(-1)?.value ?? null)}`}></i>mayor</span><p>Haz clic en un punto o casilla para abrir su ficha.</p></footer>
    </div>
  </div>
{/if}
