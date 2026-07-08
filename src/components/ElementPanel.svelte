<script lang="ts">
  import type { ElementWithLines, SpectralLine } from '../lib/atomicTypes';
  import { formatEv, formatNm, wavelengthRegion } from '../lib/wavelengthColor';
  import { getStrongestLines } from '../lib/filters';

  export let element: ElementWithLines | null = null;

  $: strongest = element ? getStrongestLines(element.lines, 5) : [];

  function energyJump(line: SpectralLine): number {
    return line.upper_level_ev - line.lower_level_ev;
  }
</script>

<aside class="element-panel">
  {#if element}
    <div class="element-hero">
      <div class="element-symbol">
        <span>{element.atomic_number}</span>
        <strong>{element.symbol}</strong>
      </div>
      <div>
        <p class="eyebrow">{element.category}</p>
        <h2>{element.name_es}</h2>
        <p>{element.summary}</p>
      </div>
    </div>

    <div class="stat-grid">
      <div>
        <span>Grupo</span>
        <strong>{element.group}</strong>
      </div>
      <div>
        <span>Periodo</span>
        <strong>{element.period}</strong>
      </div>
      <div>
        <span>Líneas</span>
        <strong>{element.lines.length}</strong>
      </div>
    </div>

    <h3>Líneas más intensas</h3>
    <div class="line-table">
      {#each strongest as line}
        <article>
          <span class="line-swatch" style={`background:${line.approximate_color};`}></span>
          <div>
            <strong>{line.label}</strong>
            <small>
              {formatNm(line.wavelength_nm)} · {wavelengthRegion(line.wavelength_nm)} · ΔE {formatEv(energyJump(line))}
            </small>
          </div>
        </article>
      {/each}
    </div>

    <h3>Datos técnicos</h3>
    <div class="technical-table">
      <table>
        <thead>
          <tr>
            <th>Línea</th>
            <th>λ</th>
            <th>Int.</th>
            <th>Transición</th>
          </tr>
        </thead>
        <tbody>
          {#each element.lines as line}
            <tr>
              <td>{line.label}</td>
              <td>{formatNm(line.wavelength_nm)}</td>
              <td>{line.intensity.toFixed(2)}</td>
              <td>{line.transition}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="empty-panel">
      <h2>Selecciona un elemento</h2>
      <p>La ficha mostrará su firma espectral, sus líneas principales y una lectura educativa de los saltos electrónicos.</p>
    </div>
  {/if}
</aside>
