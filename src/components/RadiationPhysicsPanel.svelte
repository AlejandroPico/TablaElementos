<script lang="ts">
  import type { DataRow, ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;
  export let loading = false;

  type RadiationMode = 'xray' | 'attenuation' | 'xps' | 'neutrons';
  let mode: RadiationMode = 'xray';

  interface NumericRow {
    row: DataRow;
    x: number;
    y: number;
    label: string;
  }

  function rows(): DataRow[] {
    return elementData?.domains.radiation?.rows ?? [];
  }

  function num(value: unknown): number | null {
    const text = String(value ?? '').replace(/−/g, '-').replace(/,/g, '.');
    const match = text.match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    if (!match) return null;
    const parsed = Number(match[0]);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function energyValue(row: DataRow): number | null {
    return num(row.energy) ?? num(row.value);
  }

  function xrayRows(): DataRow[] {
    return rows().filter((row) => row.property === 'xray_transition_energy');
  }

  function xpsRows(): DataRow[] {
    return rows().filter((row) => ['xps_binding_energy', 'auger_line_energy'].includes(String(row.property ?? '')));
  }

  function attenuationRows(property: string): NumericRow[] {
    return rows().flatMap((row) => {
      if (row.property !== property) return [];
      const energy = num(row.energy);
      const value = num(row.value);
      if (energy === null || value === null || energy <= 0 || value <= 0) return [];
      return [{ row, x: energy, y: value, label: `${row.energy} · ${row.value} ${row.unit}` }];
    }).sort((a, b) => a.x - b.x);
  }

  function neutronRows(): DataRow[] {
    return rows().filter((row) => String(row.property ?? '').startsWith('neutron_'));
  }

  function logPoints(values: NumericRow[], width = 720, height = 260): Array<NumericRow & { px: number; py: number }> {
    if (!values.length) return [];
    const lx = values.map((item) => Math.log10(item.x));
    const ly = values.map((item) => Math.log10(item.y));
    const minX = Math.min(...lx);
    const maxX = Math.max(...lx);
    const minY = Math.min(...ly);
    const maxY = Math.max(...ly);
    return values.map((item) => ({
      ...item,
      px: maxX === minX ? width / 2 : 46 + ((Math.log10(item.x) - minX) / (maxX - minX)) * (width - 92),
      py: maxY === minY ? height / 2 : height - 34 - ((Math.log10(item.y) - minY) / (maxY - minY)) * (height - 70),
    }));
  }

  function polyline(points: Array<{ px: number; py: number }>): string {
    return points.map((point) => `${point.px.toFixed(1)},${point.py.toFixed(1)}`).join(' ');
  }

  function xrayPosition(row: DataRow, list: DataRow[]): number {
    const energies = list.map((item) => energyValue(item)).filter((value): value is number => value !== null && value > 0);
    const value = energyValue(row);
    if (value === null || !energies.length) return 0;
    const min = Math.min(...energies);
    const max = Math.max(...energies);
    if (max === min) return 50;
    return 4 + ((Math.log10(value) - Math.log10(min)) / (Math.log10(max) - Math.log10(min))) * 92;
  }

  function xpsPosition(row: DataRow, list: DataRow[]): number {
    const energies = list.map((item) => energyValue(item)).filter((value): value is number => value !== null);
    const value = energyValue(row);
    if (value === null || !energies.length) return 0;
    const min = Math.min(...energies);
    const max = Math.max(...energies);
    return max === min ? 50 : 4 + ((value - min) / (max - min)) * 92;
  }

  function neutronAggregate(property: string): number | null {
    const natural = neutronRows().find((row) => row.property === property && ['natural', element?.symbol, ''].includes(String(row.isotope ?? '')));
    if (natural) return num(natural.value);
    const values = neutronRows().filter((row) => row.property === property).map((row) => num(row.value)).filter((value): value is number => value !== null);
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
  }

  function modeLabel(current: RadiationMode): string {
    if (current === 'xray') return 'Rayos X';
    if (current === 'attenuation') return 'Atenuación';
    if (current === 'xps') return 'XPS / Auger';
    return 'Neutrones';
  }

  $: xray = xrayRows();
  $: xps = xpsRows();
  $: attenuation = attenuationRows('mass_attenuation_coefficient');
  $: absorption = attenuationRows('mass_energy_absorption_coefficient');
  $: attenuationPoints = logPoints(attenuation);
  $: absorptionPoints = logPoints(absorption);
  $: neutrons = neutronRows();
  $: neutronMetrics = [
    { label: 'Dispersión coherente', property: 'neutron_coherent_cross_section', value: neutronAggregate('neutron_coherent_cross_section') },
    { label: 'Dispersión incoherente', property: 'neutron_incoherent_cross_section', value: neutronAggregate('neutron_incoherent_cross_section') },
    { label: 'Dispersión total', property: 'neutron_total_scattering_cross_section', value: neutronAggregate('neutron_total_scattering_cross_section') },
    { label: 'Absorción térmica', property: 'neutron_absorption_cross_section', value: neutronAggregate('neutron_absorption_cross_section') },
  ];
  $: maxNeutron = Math.max(...neutronMetrics.map((item) => item.value ?? 0), 1);
</script>

<div class="advanced-science-pane radiation-physics-pane">
  {#if loading}
    <div class="modal-load-state"><span></span><p>Cargando interacción con radiación…</p></div>
  {:else}
    <section class="science-hero radiation-hero">
      <div>
        <p>Fotones, electrones y neutrones</p>
        <h3>Laboratorio de interacción radiológica</h3>
        <small>Transiciones características de rayos X, coeficientes de atenuación, energías XPS/Auger y secciones eficaces neutrónicas.</small>
      </div>
      <div class="radiation-symbol"><strong>{element?.symbol}</strong><span>{rows().length} registros</span></div>
    </section>

    <nav class="science-mode-tabs" aria-label="Ámbitos de radiación">
      {#each ['xray', 'attenuation', 'xps', 'neutrons'] as current}
        <button class:active={mode === current} type="button" on:click={() => (mode = current as RadiationMode)}>{modeLabel(current as RadiationMode)}</button>
      {/each}
    </nav>

    {#if mode === 'xray'}
      <section class="science-visual-card xray-stick-card">
        <header><div><small>Transiciones K, L, M y bordes</small><h3>Espectro característico de rayos X</h3></div><span>{xray.length} líneas</span></header>
        {#if xray.length}
          <div class="xray-stick-spectrum" aria-label={`Líneas de rayos X de ${element?.name_es}`}>
            <div class="xray-axis"><span>menor energía</span><span>energía logarítmica (eV)</span><span>mayor energía</span></div>
            <div class="xray-sticks">
              {#each xray as row, index}
                <button type="button" style={`left:${xrayPosition(row, xray)}%;--stick-height:${34 + (index % 5) * 10}%;`} title={`${row.transition || 'Transición'} · ${row.value} ${row.unit}`}>
                  <i></i><span>{row.transition || 'X'}</span>
                </button>
              {/each}
            </div>
          </div>
          <div class="radiation-record-grid compact-record-grid">
            {#each xray as row}
              <article><span>{row.transition || 'Transición'}</span><strong>{row.value} {row.unit}</strong><small>{row.experimental_energy_ev ? 'experimental' : 'teórico'}</small></article>
            {/each}
          </div>
        {:else}
          <div class="science-empty-state"><strong>Sin líneas características importadas</strong><p>NIST X-Ray Transition Energies cubre de Ne a Fm. El importador conserva energías teóricas y experimentales por separado.</p></div>
        {/if}
      </section>
    {:else if mode === 'attenuation'}
      <section class="science-visual-card attenuation-card">
        <header><div><small>Interacción del fotón con la materia</small><h3>Atenuación másica frente a energía</h3></div><span>Escalas logarítmicas</span></header>
        {#if attenuationPoints.length > 1}
          <div class="attenuation-chart-wrap">
            <svg class="attenuation-chart" viewBox="0 0 720 260" role="img" aria-label={`Coeficiente de atenuación de ${element?.name_es}`}>
              <g class="chart-grid">{#each [42, 88, 134, 180, 226] as y}<line x1="46" x2="674" y1={y} y2={y}></line>{/each}</g>
              <polyline class="total-line" points={polyline(attenuationPoints)}></polyline>
              {#if absorptionPoints.length > 1}<polyline class="absorption-line" points={polyline(absorptionPoints)}></polyline>{/if}
              {#each attenuationPoints as point}<circle class="total-point" cx={point.px} cy={point.py} r="3"><title>{point.label}</title></circle>{/each}
              <text class="axis-caption" x="360" y="252" text-anchor="middle">Energía del fotón (MeV, escala log)</text>
            </svg>
          </div>
          <div class="attenuation-legend"><span><i class="total"></i>μ/ρ total</span><span><i class="absorbed"></i>μen/ρ absorción de energía</span></div>
          <div class="absorption-edge-list">
            {#each attenuation.filter((item) => item.row.transition) as point}<span><b>{point.row.transition}</b>{point.row.energy}</span>{/each}
          </div>
        {:else}
          <div class="science-empty-state"><strong>Sin curva de atenuación</strong><p>NIST publica μ/ρ y μen/ρ entre 1 keV y 20 MeV para elementos hasta Z = 92.</p></div>
        {/if}
      </section>
    {:else if mode === 'xps'}
      <section class="science-visual-card xps-card">
        <header><div><small>Fotoelectrones y electrones Auger</small><h3>Energías XPS / Auger</h3></div><span>{xps.length} líneas</span></header>
        {#if xps.length}
          <div class="xps-axis"><span>energía mínima</span><span>eV</span><span>energía máxima</span></div>
          <div class="xps-line-track">
            {#each xps as row}
              <button type="button" class:auger={row.property === 'auger_line_energy'} style={`left:${xpsPosition(row, xps)}%;`} title={`${row.transition || row.property} · ${row.value} ${row.unit}`}><i></i><span>{row.transition || (row.property === 'auger_line_energy' ? 'Auger' : 'XPS')}</span></button>
            {/each}
          </div>
          <div class="radiation-record-grid">
            {#each xps as row}<article><span>{row.transition || row.property}</span><strong>{row.value} {row.unit}</strong><small>{[row.compound, row.chemical_state].filter(Boolean).join(' · ') || row.source}</small></article>{/each}
          </div>
        {:else}
          <div class="science-empty-state"><strong>Sin exportación XPS/Auger local</strong><p>La pestaña está preparada para CSV del NIST XPS Database. Las energías dependen del compuesto y del estado químico; no se inventa una línea “del elemento” universal.</p></div>
        {/if}
      </section>
    {:else}
      <div class="neutron-workspace">
        <section class="science-visual-card neutron-summary-card">
          <header><div><small>Neutrones térmicos · 2200 m/s</small><h3>Secciones eficaces</h3></div><span>barn</span></header>
          <div class="neutron-bars">
            {#each neutronMetrics as metric}
              <article>
                <span>{metric.label}</span>
                <i><b style={`width:${((metric.value ?? 0) / maxNeutron) * 100}%;`}></b></i>
                <strong>{metric.value === null ? '—' : metric.value.toLocaleString('es-ES', { maximumFractionDigits: 6 })}</strong>
              </article>
            {/each}
          </div>
        </section>
        <section class="science-visual-card neutron-isotope-card">
          <header><div><small>Variación isotópica</small><h3>Tabla neutrónica</h3></div><span>{neutrons.length} registros</span></header>
          {#if neutrons.length}
            <div class="neutron-table-scroll">
              <table><thead><tr><th>Isótopo</th><th>Magnitud</th><th>Valor</th><th>Abundancia</th></tr></thead><tbody>
                {#each neutrons as row}<tr><td>{row.isotope || 'natural'}</td><td>{String(row.property ?? '').replaceAll('neutron_', '').replaceAll('_', ' ')}</td><td>{row.value} {row.unit}</td><td>{row.abundance || '—'}</td></tr>{/each}
              </tbody></table>
            </div>
          {:else}
            <div class="science-empty-state compact"><strong>Sin datos neutrónicos</strong><p>La fuente NIST NCNR cubre longitudes de dispersión y secciones térmicas hasta curio.</p></div>
          {/if}
        </section>
      </div>
    {/if}

    <p class="science-method-note">XCOM y las tablas de atenuación describen átomos o medios elementales bajo supuestos definidos por NIST. XPS depende fuertemente del entorno químico; las secciones neutrónicas mostradas son térmicas y no sustituyen curvas dependientes de energía.</p>
  {/if}
</div>
