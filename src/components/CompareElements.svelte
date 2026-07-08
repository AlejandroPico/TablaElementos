<script lang="ts">
  import * as d3 from 'd3';
  import type { ElementWithLines } from '../lib/atomicTypes';
  import { formatNm } from '../lib/wavelengthColor';

  export let selected: ElementWithLines[] = [];

  const width = 900;
  const x = d3.scaleLinear().domain([320, 780]).range([0, width]);

  function lineLeft(wavelength: number): number {
    return x(wavelength);
  }
</script>

<section class="compare-card">
  <div class="section-title-row">
    <div>
      <p class="eyebrow">Comparador</p>
      <h2>Firmas superpuestas</h2>
    </div>
    <span class="range-pill">{selected.length}/4</span>
  </div>

  {#if selected.length === 0}
    <p class="empty-copy">
      Usa el botón <strong>+</strong> de la tabla periódica para añadir elementos al comparador.
    </p>
  {:else}
    <div class="compare-stack">
      {#each selected as element}
        <article>
          <header>
            <strong>{element.symbol}</strong>
            <span>{element.name_es}</span>
          </header>
          <div class="mini-spectrum">
            {#each element.lines as line}
              <span
                style={`
                  left:${lineLeft(line.wavelength_nm)}px;
                  opacity:${0.35 + line.intensity * 0.65};
                  --line-color:${line.approximate_color};
                `}
                title={`${line.label}: ${formatNm(line.wavelength_nm)}`}
              ></span>
            {/each}
          </div>
        </article>
      {/each}
    </div>
  {/if}
</section>
