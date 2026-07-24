<script lang="ts">
  import type { DataRow, ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;
  export let loading = false;
  let recordPage = 0;
  const recordPageSize = 8;

  interface Point {
    x: number;
    y: number;
    label: string;
    rawX: number;
    rawY: number;
  }

  interface SeriesValue {
    x: number;
    y: number;
    label: string;
  }

  interface ShomateBlock {
    phase: string;
    index: string;
    minTemperature: number;
    maxTemperature: number;
    coefficients: Partial<Record<'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H', number>>;
  }

  function num(value: unknown): number | null {
    const text = String(value ?? '')
      .replace(/−/g, '-')
      .replace(/,/g, '.')
      .replace(/×\s*10\s*\^?\s*\{?([-+]?\d+)\}?/gi, 'e$1');
    const match = text.match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i);
    if (!match) return null;
    const parsed = Number(match[0]);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function numbers(value: unknown): number[] {
    const text = String(value ?? '').replace(/−/g, '-').replace(/,/g, '.');
    return (text.match(/[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/gi) ?? [])
      .map((part) => Number(part))
      .filter(Number.isFinite);
  }

  function findRow(sourceRows: DataRow[], ...properties: string[]): DataRow | null {
    return sourceRows.find((row) => properties.includes(String(row.property ?? ''))) ?? null;
  }

  function textValue(sourceRows: DataRow[], properties: string[], fallback = '—'): string {
    const row = findRow(sourceRows, ...properties);
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

  function series(sourceRows: DataRow[], propertyNames: string[], xKeys: string[]): SeriesValue[] {
    return sourceRows.flatMap((row) => {
      if (!propertyNames.includes(String(row.property ?? ''))) return [];
      const y = num(row.value);
      const x = xKeys.map((key) => num(row[key])).find((value) => value !== null) ?? null;
      if (x === null || y === null || x <= 0 || y <= 0) return [];
      return [{ x, y, label: `${row.value}${row.unit ? ` ${row.unit}` : ''}` }];
    }).sort((a, b) => a.x - b.x);
  }

  function shomateBlocks(sourceRows: DataRow[]): ShomateBlock[] {
    const groups = new Map<string, ShomateBlock>();
    for (const row of sourceRows) {
      const match = String(row.property ?? '').match(/^shomate_([A-H])_([a-z]+|unspecified)_(\d+)$/i);
      if (!match) continue;
      const [, coefficientRaw, phase, index] = match;
      const coefficient = coefficientRaw.toUpperCase() as keyof ShomateBlock['coefficients'];
      const value = num(row.value);
      if (value === null) continue;
      const temperatures = numbers(row.temperature_k);
      const minTemperature = temperatures[0] ?? 298.15;
      const maxTemperature = temperatures[1] ?? minTemperature;
      const key = `${phase}_${index}`;
      const group = groups.get(key) ?? {
        phase,
        index,
        minTemperature,
        maxTemperature,
        coefficients: {},
      };
      group.minTemperature = minTemperature;
      group.maxTemperature = maxTemperature;
      group.coefficients[coefficient] = value;
      groups.set(key, group);
    }
    return [...groups.values()]
      .filter((block) => ['A', 'B', 'C', 'D', 'E'].every((key) => block.coefficients[key as keyof ShomateBlock['coefficients']] !== undefined))
      .sort((a, b) => a.minTemperature - b.minTemperature);
  }

  function cpFromShomate(blocks: ShomateBlock[]): SeriesValue[] {
    const values: SeriesValue[] = [];
    for (const block of blocks) {
      const { A = 0, B = 0, C = 0, D = 0, E = 0 } = block.coefficients;
      const span = Math.max(0, block.maxTemperature - block.minTemperature);
      const steps = span > 0 ? 28 : 1;
      for (let index = 0; index <= steps; index += 1) {
        const temperature = span > 0
          ? block.minTemperature + (span * index) / steps
          : block.minTemperature;
        if (temperature <= 0) continue;
        const t = temperature / 1000;
        const cp = A + B * t + C * t ** 2 + D * t ** 3 + E / t ** 2;
        if (!Number.isFinite(cp) || cp <= 0) continue;
        values.push({
          x: temperature,
          y: cp,
          label: `${cp.toLocaleString('es-ES', { maximumFractionDigits: 4 })} J/(mol·K) · ${block.phase}`,
        });
      }
    }
    return values.sort((a, b) => a.x - b.x);
  }

  function plotPoints(values: SeriesValue[], logY = false): Point[] {
    if (!values.length) return [];
    const xs = values.map((item) => item.x);
    const ys = values.map((item) => logY ? Math.log10(item.y) : item.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    return values.map((item) => {
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

  $: thermodynamicRows = elementData?.domains.thermodynamics?.rows ?? [];
  $: physicalRows = elementData?.domains.physical?.rows ?? [];
  $: allRows = [...thermodynamicRows, ...physicalRows];
  $: meltingRow = findRow(allRows, 'melting_point');
  $: boilingRow = findRow(allRows, 'boiling_point');
  $: tripleRow = findRow(allRows, 'triple_point', 'triple_point_temperature');
  $: criticalRow = findRow(allRows, 'critical_temperature');
  $: melting = kelvin(meltingRow);
  $: boiling = kelvin(boilingRow);
  $: triple = kelvin(tripleRow);
  $: critical = kelvin(criticalRow);
  $: phaseMax = Math.max(melting ?? 0, boiling ?? 0, triple ?? 0, critical ?? 0, 300);
  $: directCpSeries = series(allRows, ['heat_capacity_cp', 'specific_heat', 'specific_heat_capacity'], ['temperature_k']);
  $: shomate = shomateBlocks(thermodynamicRows);
  $: shomateCpSeries = cpFromShomate(shomate);
  $: cpDerivedFromShomate = directCpSeries.length <= 1 && shomateCpSeries.length > 1;
  $: cpSeries = directCpSeries.length > 1 ? directCpSeries : shomateCpSeries;
  $: vaporSeries = series(allRows, ['vapor_pressure'], ['temperature_k']);
  $: cpPoints = plotPoints(cpSeries);
  $: vaporPoints = plotPoints(vaporSeries, true);
  $: recordPages = Math.max(1, Math.ceil(thermodynamicRows.length / recordPageSize));
  $: visibleRecords = thermodynamicRows.slice(recordPage * recordPageSize, (recordPage + 1) * recordPageSize);
</script>

<div class="advanced-science-pane thermodynamics-pane">
  {#if loading}
    <div class="modal-load-state"><span></span><p>Cargando termodinámica…</p></div>
  {:else}
    <section class="science-inline-stats" aria-label="Resumen termodinámico">
      <span><small>Estado</small><strong>{textValue(allRows, ['standard_state'])}</strong></span>
      <span><small>Fusión</small><strong>{textValue(allRows, ['melting_point'])}</strong></span>
      <span><small>Ebullición</small><strong>{textValue(allRows, ['boiling_point'])}</strong></span>
      <span><small>Cp</small><strong>{textValue(allRows, ['heat_capacity_cp', 'specific_heat'])}</strong></span>
    </section>

    <details class="science-detail-drawer">
      <summary>Más magnitudes termodinámicas</summary>
      <dl>
        <div><dt>Entalpía de fusión</dt><dd>{textValue(allRows, ['enthalpy_fusion'])}</dd></div>
        <div><dt>Entalpía de vaporización</dt><dd>{textValue(allRows, ['enthalpy_vaporization'])}</dd></div>
        <div><dt>Entropía molar</dt><dd>{textValue(allRows, ['standard_molar_entropy_solid', 'standard_molar_entropy_liquid', 'standard_molar_entropy_gas', 'standard_molar_entropy'])}</dd></div>
        <div><dt>Punto triple</dt><dd>{textValue(allRows, ['triple_point', 'triple_point_temperature'])}</dd></div>
        <div><dt>Punto crítico</dt><dd>{textValue(allRows, ['critical_temperature'])}</dd></div>
      </dl>
    </details>

    <section class="flat-science-section phase-landmark-card">
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
      <section class="flat-science-section thermo-series-card">
        <header>
          <div><small>Respuesta térmica</small><h3>Cp frente a temperatura</h3></div>
          <span>{cpSeries.length} puntos{cpDerivedFromShomate ? ' · NIST Shomate' : ''}</span>
        </header>
        {#if cpPoints.length > 1}
          <svg class="thermo-line-chart" viewBox="0 0 720 260" role="img" aria-label="Capacidad calorífica frente a temperatura">
            <g class="chart-grid">{#each [42, 88, 134, 180, 226] as y}<line x1="44" x2="676" y1={y} y2={y}></line>{/each}</g>
            <polyline points={pointsString(cpPoints)}></polyline>
            {#each cpPoints as point}<circle cx={point.x} cy={point.y} r="4"><title>{`${point.rawX.toLocaleString('es-ES', { maximumFractionDigits: 2 })} K · ${point.label}`}</title></circle>{/each}
            <text class="axis-caption" x="360" y="252" text-anchor="middle">Temperatura (K)</text>
          </svg>
          {#if cpDerivedFromShomate}<p class="chart-source-note">Curva calculada con los coeficientes A–E y los intervalos de fase publicados por NIST Chemistry WebBook.</p>{/if}
        {:else}
          <div class="science-empty-state compact"><strong>Serie Cp(T) no disponible</strong><p>Un único valor se muestra en la ficha; una curva requiere varios puntos o coeficientes Shomate completos.</p></div>
        {/if}
      </section>

      <section class="flat-science-section thermo-series-card">
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
      <section class="flat-science-section thermo-record-list">
        <header><div><small>Registros y condiciones</small><h3>Dataset termodinámico</h3></div><span>{thermodynamicRows.length} filas</span></header>
        <div class="compact-science-table">
          <table>
            <thead><tr><th>Magnitud</th><th>Valor</th><th>Temperatura</th><th>Presión / fase</th><th>Fuente</th></tr></thead>
            <tbody>
              {#each visibleRecords as row}
                <tr title={row.notes || undefined}>
                  <td>{String(row.property ?? '').replaceAll('_', ' ')}</td>
                  <td>{row.value || '—'}{row.unit ? ` ${row.unit}` : ''}</td>
                  <td>{row.temperature_k ? `${row.temperature_k} K` : '—'}</td>
                  <td>{[row.pressure, row.phase].filter(Boolean).join(' · ') || '—'}</td>
                  <td>{row.source || '—'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        {#if recordPages > 1}<div class="inline-pagination"><button type="button" disabled={recordPage === 0} on:click={() => (recordPage -= 1)}>Anterior</button><span>{recordPage + 1} / {recordPages}</span><button type="button" disabled={recordPage >= recordPages - 1} on:click={() => (recordPage += 1)}>Siguiente</button></div>{/if}
      </section>
    {/if}

    <p class="science-method-note">Un punto de fusión, una capacidad calorífica o una presión de vapor no son números universales: dependen de fase, presión, pureza y temperatura. Las curvas Shomate se calculan únicamente cuando NIST publica todos los coeficientes necesarios.</p>
  {/if}
</div>
