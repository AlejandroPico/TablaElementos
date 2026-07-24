<script lang="ts">
  import type { DataRow, ElementDataPayload } from '../lib/atomicTypes';

  export let elementData: ElementDataPayload | null = null;
  export let loading = false;

  type Mode = 'transport' | 'mechanics' | 'magnetism';
  let mode: Mode = 'transport';

  const groups: Record<Mode, Array<{ property: string; label: string }>> = {
    transport: [
      { property: 'electrical_type', label: 'Comportamiento eléctrico' },
      { property: 'electrical_conductivity', label: 'Conductividad eléctrica' },
      { property: 'electrical_resistivity', label: 'Resistividad eléctrica' },
      { property: 'thermal_conductivity', label: 'Conductividad térmica' },
      { property: 'thermal_expansion', label: 'Expansión térmica' },
      { property: 'speed_of_sound', label: 'Velocidad del sonido' },
    ],
    mechanics: [
      { property: 'young_modulus', label: 'Módulo de Young' },
      { property: 'shear_modulus', label: 'Módulo de cizallamiento' },
      { property: 'bulk_modulus', label: 'Módulo volumétrico' },
      { property: 'poisson_ratio', label: 'Coeficiente de Poisson' },
      { property: 'mohs_hardness', label: 'Dureza Mohs' },
      { property: 'vickers_hardness', label: 'Dureza Vickers' },
      { property: 'brinell_hardness', label: 'Dureza Brinell' },
    ],
    magnetism: [
      { property: 'magnetic_type', label: 'Orden magnético' },
      { property: 'magnetic_susceptibility_mass', label: 'Susceptibilidad másica' },
      { property: 'magnetic_susceptibility_molar', label: 'Susceptibilidad molar' },
      { property: 'magnetic_susceptibility_volume', label: 'Susceptibilidad volumétrica' },
      { property: 'curie_point', label: 'Temperatura de Curie' },
      { property: 'neel_point', label: 'Temperatura de Néel' },
      { property: 'superconducting_point', label: 'Transición superconductora' },
    ],
  };

  function number(value: unknown): number | null {
    const match = String(value ?? '').replace(/−/g, '-').replace(/,/g, '.').match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    const parsed = match ? Number(match[0]) : Number.NaN;
    return Number.isFinite(parsed) ? parsed : null;
  }

  function row(property: string): DataRow | null {
    return elementData?.domains.materials?.rows.find((item) => item.property === property) ?? null;
  }

  function display(item: DataRow | null): string {
    if (!item?.value) return 'Sin dato';
    return `${item.value}${item.unit ? ` ${item.unit}` : ''}`;
  }

  $: visible = groups[mode].map((item) => ({ ...item, row: row(item.property) }));
  $: numeric = visible
    .map((item) => ({ ...item, numeric: number(item.row?.value) }))
    .filter((item): item is typeof item & { numeric: number } => item.numeric !== null && item.numeric >= 0);
  $: maxValue = Math.max(...numeric.map((item) => item.numeric), 1);
</script>

<div class="advanced-science-pane material-properties-pane">
  {#if loading}
    <div class="modal-load-state"><span></span><p>Cargando propiedades del material…</p></div>
  {:else}
    <nav class="science-mode-tabs material-mode-tabs" aria-label="Familias de propiedades del material">
      <button class:active={mode === 'transport'} type="button" on:click={() => (mode = 'transport')}>Transporte</button>
      <button class:active={mode === 'mechanics'} type="button" on:click={() => (mode = 'mechanics')}>Mecánica</button>
      <button class:active={mode === 'magnetism'} type="button" on:click={() => (mode = 'magnetism')}>Magnetismo</button>
    </nav>

    <section class="material-dashboard">
      <div class="material-plot" aria-label={`Comparación de propiedades de ${mode}`}>
        <header>
          <div>
            <small>{mode === 'transport' ? 'Respuesta eléctrica y térmica' : mode === 'mechanics' ? 'Rigidez, deformación y dureza' : 'Respuesta a campos y orden colectivo'}</small>
            <h3>{mode === 'transport' ? 'Transporte' : mode === 'mechanics' ? 'Comportamiento mecánico' : 'Magnetismo'}</h3>
          </div>
          <span>Escala relativa dentro de cada familia</span>
        </header>

        <div class="material-bars">
          {#each visible as item}
            {@const value = number(item.row?.value)}
            <article class:missing={value === null}>
              <div><span>{item.label}</span><strong>{display(item.row)}</strong></div>
              <i><b style={`width:${value === null ? 0 : Math.max(2, (value / maxValue) * 100)}%;`}></b></i>
            </article>
          {/each}
        </div>
      </div>

      <aside class="material-reading">
        <h3>Lectura científica</h3>
        {#if mode === 'transport'}
          <p>Conductividad y resistividad dependen de temperatura, pureza, defectos y fase. Las barras permiten comparar magnitudes, pero no mezclan sus unidades.</p>
        {:else if mode === 'mechanics'}
          <p>Los módulos describen respuestas diferentes: tracción, cizallamiento y compresión. La dureza pertenece a otra familia y depende del método de ensayo.</p>
        {:else}
          <p>Diamagnetismo, paramagnetismo y órdenes colectivos no son sinónimos. Curie y Néel indican transiciones distintas y solo aparecen cuando existe un valor publicado.</p>
        {/if}
        <dl>
          {#each visible.filter((item) => item.row) as item}
            <div><dt>{item.label}</dt><dd>{display(item.row)}</dd></div>
          {/each}
        </dl>
      </aside>
    </section>

    <p class="science-method-note">Los valores de referencia actuales proceden de una compilación secundaria versionada. La fase, pureza, orientación y temperatura pueden cambiar sustancialmente estas propiedades; la ficha conserva la procedencia de cada fila.</p>
  {/if}
</div>
