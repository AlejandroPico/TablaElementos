<script lang="ts">
  import type { DataRow, ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;
  export let loading = false;

  interface Point {
    x: number;
    y: number;
    label: string;
    rawX: number;
    rawY: number;
  }

  function rows(): DataRow[] {
    return [
      ...(elementData?.domains.thermodynamics?.rows ?? []),
      ...(elementData?.domains.physical?.rows ?? []),
    ];
  }

  function num(value: unknown): number | null {
    const text = String(value ?? '').replace(/−/g, '-').replace(/,/g, '.');
    const match = text.match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    if (!match) return null;
    const parsed = Number(match[0]);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function findRow(...properties: string[]): DataRow | null {
    return rows().find((row) => properties.includes(String(row.property ?? ''))) ?? null;
  }

  function textValue(properties: string[], fallback = '—'): string {
    const row = findRow(...properties);
    if (!row?.value) return fallback;
    return `${row.value}${row.unit ? ` ${row.unit}` : ''}`;
  }

  function kelvin(row: DataRow | null): number | null {
    if (!row) return null;
    const direct = num(row.temperature_k);
    if (direct !== null) return direct;
    const value = num(row.value);
    if (value === null) return null;
    const unit = String(row.unit ?? '').toLowerCase();
    if (unit.includes('°c') || unit === 'c') return value + 273.15;
    if (unit.includes('°f') || unit === 'f') return (value - 32) * 5 / 9 + 273.15;
    return value;
  }

  function series(propertyNames: string[], xKeys: string[]): Array<{ x: number; y: number; label: string }> {
    return rows().flatMap((row) => {
      if (!propertyNames.includes(String(row.property ?? ''))) return [];
      const y = num(row.value);
      const x = xKeys.map((key) => num(row[key])).find((value) => value !== null) ?? null;
      if (x === null || y === null || x <= 0 || y <= 0) return [];
      return [{ x, y, label: `${row.value}${row.unit ? ` ${row.unit}` : ''}` }];
    }).sort((a, b) => a.x - b.x);
  }

  function plotPoints(values: Array<{ x: number; y: number; label: string }>, logY = false): Point[] {
    if (!values.length) return [];
    const xs = values.map((item) => item.x);
    const ys = values.map((item) => logY ? Math.log10(item.y) : item.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    return values.map((item, index) => {
      const normalizedY = logY ? Math.log10(item.y) : item.y;
      return {
        x: maxX === minX ? 360 : 44 + ((item.x - minX) / (maxX - minX)) * 632,
        y: maxY === minY ? 130 : 226 - ((normalizedY - minY) / (maxY - minY)) * 190,
        label: item.label,
        rawX: item.x,
        rawY: item.y,
      };
    });
  }

  function pointsString(points: Point[]): string {
    return points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' ');
  }

  function landmarkPosition(value: number, max: number): number {
    return 52 + Math.max(0, Math.min(1, value / Math.max(max, 1))) * 616;
  }

  $: meltingRow = findRow('melting_point');
  $: boilingRow = findRow('boiling_point');
  $: tripleRow = findRow('triple_point', 'triple_point_temperature');
  $: criticalRow = findRow('critical_temperature');
  $: melting = kelvin(meltingRow);
  $: boiling = kelvin(boilingRow);
  $: triple = kelvin(tripleRow);
  $: critical = kelvin(criticalRow);
  $: phaseMax = Math.max(melting ?? 0, boiling ?? 0, triple ?? 0, critical ?? 0, 300);
  $: cpSeries = series(['heat_capacity_cp', 'specific_heat', 'specific_heat_capacity'], ['temperature_k']);
  $: vaporSeries = series(['vapor_pressure'], ['temperature_k']);
  $: cpPoints = plotPoints(cpSeries);
  $: vaporPoints = plotPoints(vaporSeries, true);
  $: thermodynamicRows = elementData?.domains.thermodynamics?.rows ?? [];
</script>

<div class="advanced-science-pane thermodynamics-pane">
  {#if loading}
    <div class="modal-load-state"><span></span><p>Cargando termodinámica…</p></div>
  {:else}
    <section class="science-hero thermo-hero">
      <div>
        <p>Termodinámica y fases</p>
        <h3>Materia, energía y transiciones</h3>
        <small>Las magnitudes conservan fase, temperatura, presión, fuente y condiciones cuando la fuente las proporciona.</small>
      </div>
      <div class="thermo-gauge" aria-label={`Estado estándar: ${textValue(['standard_state'])}`}><strong>{element?.symbol}</strong><span>{textValue(['standard_state'])}</span></div>
    </section>

    <section class="science-card-grid thermo-summary-grid">
      <article><small>Punto de fusión</small><strong>{textValue(['melting_point'])}</strong></article>
      <article><small>Punto de ebullición</small><strong>{textValue(['boiling_point'])}</strong></article>
      <article><small>Entalpía de fusión</small><strong>{textValue(['enthalpy_fusion'])}</strong></article>
      <article><small>Entalpía de vaporización</small><strong>{textValue(['enthalpy_vaporization'])}</strong></article>
      <article><small>Capacidad calorífica Cp</small><strong>{textValue(['heat_capacity_cp', 'specific_heat'])}</strong></article>
      <article><small>Entropía molar estándar</small><strong>{textValue(['standard_molar_entropy'])}</strong></article>
      <article><small>Punto triple</small><strong>{textValue(['triple_point', 'triple_point_temperature'])}</strong></article>
      <article><small>Punto crítico</small><strong>{textValue(['critical_temperature'])}</strong></article>
    </section>

    <section class="science-visual-card phase-landmark-card">
      <header>
        <div><small>Temperatura absoluta</small><h3>Mapa de transiciones de fase</h3></div>
        <span>Solo se dibujan puntos publicados</span>
      </header>
      {#if melting !== null || boiling !== null || triple !== null || critical !== null}
        <svg class="phase-landmark-chart" viewBox="0 0 720 180" role="img" aria-label={`Transiciones de fase de ${element?.name_es}`}>
          <line class="phase-axis" x1="52" x2="668" y1="100" y2="100"></line>
          <text x="52" y="130">0 K</text><text x="668" y="130" text-anchor="end">{phaseMax.toLocaleString('es-ES', { maximumFractionDigits: 0 })} K</text>
          {#if melting !== null}
            <g transform={`translate(${landmarkPosition(melting, phaseMax)} 0)`}><line y1="64" y2="112"></line><circle cy="100" r="6"></circle><text y="51" text-anchor="middle">Fusión</text><text y="145" text-anchor="middle">{melting.toLocaleString('es-ES')} K</text></g>
          {/if}
          {#if boiling !== null}
            <g transform={`translate(${landmarkPosition(boiling, phaseMax)} 0)`}><line y1="64" y2="112"></line><circle cy="100" r="6"></circle><text y="51" text-anchor="middle">Ebullición</text><text y="145" text-anchor="middle">{boiling.toLocaleString('es-ES')} K</text></g>
          {/if}
          {#if triple !== null}
            <g class="secondary-landmark" transform={`translate(${landmarkPosition(triple, phaseMax)} 0)`}><line y1="78" y2="122"></line><circle cy="100" r="5"></circle><text y="164" text-anchor="middle">Triple · {triple.toLocaleString('es-ES')} K</text></g>
          {/if}
          {#if critical !== null}
            <g class="secondary-landmark" transform={`translate(${landmarkPosition(critical, phaseMax)} 0)`}><line y1="78" y2="122"></line><circle cy="100" r="5"></circle><text y="30" text-anchor="middle">Crítico · {critical.toLocaleString('es-ES')} K</text></g>
          {/if}
        </svg>
      {:else}
        <div class="science-empty-state compact"><strong>Sin temperaturas de transición</strong><p>El panel se completará al incorporar registros termodinámicos trazables.</p></div>
      {/if}
    </section>

    <div class="thermo-chart-grid">
      <section class="science-visual-card thermo-series-card">
        <header><div><small>Respuesta térmica</small><h3>Cp frente a temperatura</h3></div><span>{cpSeries.length} puntos</span></header>
        {#if cpPoints.length > 1}
          <svg class="thermo-line-chart" viewBox="0 0 720 260" role="img" aria-label="Capacidad calorífica frente a temperatura">
            <g class="chart-grid">{#each [42, 88, 134, 180, 226] as y}<line x1="44" x2="676" y1={y} y2={y}></line>{/each}</g>
            <polyline points={pointsString(cpPoints)}></polyline>
            {#each cpPoints as point}<circle cx={point.x} cy={point.y} r="4"><title>{`${point.rawX} K · ${point.label}`}</title></circle>{/each}
            <text class="axis-caption" x="360" y="252" text-anchor="middle">Temperatura (K)</text>
          </svg>
        {:else}
          <div class="science-empty-state compact"><strong>Serie Cp(T) no disponible</strong><p>Un único valor se muestra en la ficha; una curva requiere varias temperaturas.</p></div>
        {/if}
      </section>

      <section class="science-visual-card thermo-series-card">
        <header><div><small>Equilibrio líquido–vapor</small><h3>Presión de vapor</h3></div><span>{vaporSeries.length} puntos · escala log</span></header>
        {#if vaporPoints.length > 1}
          <svg class="thermo-line-chart vapor-chart" viewBox="0 0 720 260" role="img" aria-label="Presión de vapor frente a temperatura">
            <g class="chart-grid">{#each [42, 88, 134, 180, 226] as y}<line x1="44" x2="676" y1={y} y2={y}></line>{/each}</g>
            <polyline points={pointsString(vaporPoints)}></polyline>
            {#each vaporPoints as point}<circle cx={point.x} cy={point.y} r="4"><title>{`${point.rawX} K · ${point.label}`}</title></circle>{/each}
            <text class="axis-caption" x="360" y="252" text-anchor="middle">Temperatura (K)</text>
          </svg>
        {:else}
          <div class="science-empty-state compact"><strong>Curva de presión no disponible</strong><p>El texto o punto aislado se conserva en el CSV, pero no se inventa una curva.</p></div>
        {/if}
      </section>
    </div>

    {#if thermodynamicRows.length}
      <section class="science-visual-card thermo-record-list">
        <header><div><small>Registros y condiciones</small><h3>Dataset termodinámico</h3></div><span>{thermodynamicRows.length} filas</span></header>
        <div>
          {#each thermodynamicRows as row}
            <article title={row.notes || undefined}>
              <span>{String(row.property ?? '').replaceAll('_', ' ')}</span>
              <strong>{row.value || '—'}{row.unit ? ` ${row.unit}` : ''}</strong>
              <small>{[row.temperature_k ? `${row.temperature_k} K` : '', row.pressure, row.phase, row.source].filter(Boolean).join(' · ')}</small>
            </article>
          {/each}
        </div>
      </section>
    {/if}

    <p class="science-method-note">Un punto de fusión, una capacidad calorífica o una presión de vapor no son números universales: dependen de fase, presión, pureza y temperatura. El panel no interpola cuando solo existe un registro.</p>
  {/if}
</div>
