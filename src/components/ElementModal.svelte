<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import ElementPanel from './ElementPanel.svelte';
  import EnergyLevels from './EnergyLevels.svelte';
  import SpectrumViewer from './SpectrumViewer.svelte';
  import type { ElementWithLines, SpectralLine, SpectrumMode } from '../lib/atomicTypes';
  import { formatEv, formatNm, wavelengthRegion } from '../lib/wavelengthColor';

  type TabId = 'wavelengths' | 'levels' | 'element' | 'lines';

  export let element: ElementWithLines | null = null;
  export let comparedSymbols: string[] = [];

  let activeTab: TabId = 'wavelengths';
  let mode: SpectrumMode = 'emission';
  let lastSymbol = '';

  const dispatch = createEventDispatcher<{
    close: void;
    compare: string;
  }>();

  $: if (element && element.symbol !== lastSymbol) {
    activeTab = 'wavelengths';
    mode = 'emission';
    lastSymbol = element.symbol;
  }

  $: isCompared = element ? comparedSymbols.includes(element.symbol) : false;

  function closeOnBackdrop(event: MouseEvent): void {
    if (event.currentTarget === event.target) {
      dispatch('close');
    }
  }

  function energyJump(line: SpectralLine): number {
    return line.upper_level_ev - line.lower_level_ev;
  }
</script>

{#if element}
  <div class="modal-backdrop" role="presentation" on:click={closeOnBackdrop}>
    <section class="element-modal" aria-modal="true" role="dialog" aria-label={`Ficha espectral de ${element.name_es}`}>
      <header class="modal-header">
        <div class="modal-identity">
          <div class="modal-symbol">
            <span>{element.atomic_number}</span>
            <strong>{element.symbol}</strong>
          </div>
          <div>
            <p class="eyebrow">{element.category}</p>
            <h2>{element.name_es}</h2>
            <small>{element.name_en} · Grupo {element.group} · Periodo {element.period}</small>
          </div>
        </div>

        <div class="modal-actions">
          <button class:active={isCompared} type="button" on:click={() => dispatch('compare', element.symbol)}>
            {isCompared ? 'En comparador' : 'Añadir al comparador'}
          </button>
          <button class="close-button" type="button" on:click={() => dispatch('close')} aria-label="Cerrar ficha">
            ×
          </button>
        </div>
      </header>

      <nav class="modal-tabs" aria-label="Pestañas de la ficha">
        <button class:active={activeTab === 'wavelengths'} type="button" on:click={() => (activeTab = 'wavelengths')}>
          Longitudes de onda
        </button>
        <button class:active={activeTab === 'levels'} type="button" on:click={() => (activeTab = 'levels')}>
          Niveles de energía
        </button>
        <button class:active={activeTab === 'element'} type="button" on:click={() => (activeTab = 'element')}>
          Elemento
        </button>
        <button class:active={activeTab === 'lines'} type="button" on:click={() => (activeTab = 'lines')}>
          Datos de líneas
        </button>
      </nav>

      <div class="modal-content">
        {#if activeTab === 'wavelengths'}
          <div class="mode-row">
            <div>
              <p class="eyebrow">Modo de visualización</p>
              <h3>Emisión / absorción</h3>
            </div>
            <div class="segmented-control small">
              <button class:active={mode === 'emission'} type="button" on:click={() => (mode = 'emission')}>Emisión</button>
              <button class:active={mode === 'absorption'} type="button" on:click={() => (mode = 'absorption')}>Absorción</button>
            </div>
          </div>

          <SpectrumViewer lines={element.lines} {mode} title={`${element.name_es} (${element.symbol})`} />
        {:else if activeTab === 'levels'}
          <EnergyLevels lines={element.lines} />
        {:else if activeTab === 'element'}
          <ElementPanel {element} />
        {:else if activeTab === 'lines'}
          <section class="modal-data-card">
            <div class="section-title-row compact">
              <div>
                <p class="eyebrow">Tabla técnica</p>
                <h2>Líneas espectrales</h2>
              </div>
              <span class="range-pill">{element.lines.length} líneas</span>
            </div>

            <div class="technical-table modal-table">
              <table>
                <thead>
                  <tr>
                    <th>Línea</th>
                    <th>Especie</th>
                    <th>λ</th>
                    <th>Región</th>
                    <th>Intensidad</th>
                    <th>Nivel inferior</th>
                    <th>Nivel superior</th>
                    <th>ΔE</th>
                    <th>Transición</th>
                  </tr>
                </thead>
                <tbody>
                  {#each element.lines as line}
                    <tr>
                      <td>{line.label}</td>
                      <td>{line.species}</td>
                      <td>{formatNm(line.wavelength_nm)}</td>
                      <td>{wavelengthRegion(line.wavelength_nm)}</td>
                      <td>{line.intensity.toFixed(2)}</td>
                      <td>{formatEv(line.lower_level_ev)}</td>
                      <td>{formatEv(line.upper_level_ev)}</td>
                      <td>{formatEv(energyJump(line))}</td>
                      <td>{line.transition}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </section>
        {/if}
      </div>
    </section>
  </div>
{/if}
