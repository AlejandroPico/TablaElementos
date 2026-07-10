<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import ElementPanel from './ElementPanel.svelte';
  import EnergyLevels from './EnergyLevels.svelte';
  import SpectrumViewer from './SpectrumViewer.svelte';
  import type { ElementWithLines, NistFileStatus, SpectralLine, SpectrumMode } from '../lib/atomicTypes';
  import { formatEv, formatNm, wavelengthRegion } from '../lib/wavelengthColor';

  type TabId = 'element' | 'wavelengths' | 'levels' | 'lines' | 'nist';

  export let element: ElementWithLines | null = null;
  export let comparedSymbols: string[] = [];

  let activeTab: TabId = 'element';
  let mode: SpectrumMode = 'emission';
  let lastSymbol = '';

  const dispatch = createEventDispatcher<{ close: void; compare: string }>();

  $: hasNistProblem = element
    ? Boolean(
        element.nist &&
          ((element.nist.espectro.present && !element.nist.espectro.table_like) ||
            (element.nist.niveles.present && !element.nist.niveles.table_like))
      )
    : false;

  $: if (element && element.symbol !== lastSymbol) {
    activeTab = 'element';
    mode = 'emission';
    lastSymbol = element.symbol;
  }

  $: isCompared = element ? comparedSymbols.includes(element.symbol) : false;
  $: nistFiles = element?.nist
    ? [
        { label: 'Espectro / líneas', item: element.nist.espectro },
        { label: 'Niveles de energía', item: element.nist.niveles }
      ]
    : [];

  function closeOnBackdrop(event: MouseEvent): void {
    if (event.currentTarget === event.target) dispatch('close');
  }

  function energyJump(line: SpectralLine): number {
    return line.upper_level_ev - line.lower_level_ev;
  }

  function statusLabel(file: NistFileStatus): string {
    if (!file.present) return 'No encontrado';
    if (file.table_like) return 'CSV tabular';
    if (file.status === 'invalid_single_column_script') return 'No tabular: contiene JavaScript';
    if (file.status === 'invalid_html_export') return 'No tabular: parece HTML';
    if (file.status === 'single_column_csv') return 'No tabular: una columna';
    return file.status;
  }
</script>

{#if element}
  <div class="modal-backdrop" role="presentation" on:click={closeOnBackdrop}>
    <section class="element-modal master-modal" aria-modal="true" role="dialog" aria-label={`Ficha maestra de ${element.name_es}`}>
      <header class="modal-header">
        <div class="modal-identity">
          <div class="modal-symbol">
            <span>{element.atomic_number}</span>
            <strong>{element.symbol}</strong>
          </div>
          <div>
            <p class="eyebrow">Ficha maestra · {element.category}</p>
            <h2>{element.name_es}</h2>
            <small>{element.name_en} · Grupo {element.group} · Periodo {element.period}</small>
          </div>
        </div>

        <div class="modal-actions">
          <button class:active={isCompared} type="button" on:click={() => dispatch('compare', element.symbol)}>
            {isCompared ? 'En comparador' : 'Comparar'}
          </button>
          <button class="close-button" type="button" on:click={() => dispatch('close')} aria-label="Cerrar ficha">×</button>
        </div>
      </header>

      {#if hasNistProblem}
        <aside class="spectral-warning compact-warning">
          <strong>NIST pendiente de nueva exportación</strong>
          <span>Los archivos actuales contienen contenido de página, no tablas científicas. La ficha no dibuja datos falsos.</span>
        </aside>
      {/if}

      <nav class="modal-tabs master-tabs" aria-label="Secciones de la ficha maestra">
        <button class:active={activeTab === 'element'} type="button" on:click={() => (activeTab = 'element')}>Resumen</button>
        <button class:active={activeTab === 'wavelengths'} type="button" on:click={() => (activeTab = 'wavelengths')}>Espectro</button>
        <button class:active={activeTab === 'levels'} type="button" on:click={() => (activeTab = 'levels')}>Niveles</button>
        <button class:active={activeTab === 'lines'} type="button" on:click={() => (activeTab = 'lines')}>Líneas</button>
        <button class:active={activeTab === 'nist'} type="button" on:click={() => (activeTab = 'nist')}>
          Fuentes / NIST{hasNistProblem ? ' · revisar' : ''}
        </button>
      </nav>

      <div class="modal-content">
        {#if activeTab === 'element'}
          <ElementPanel {element} />
        {:else if activeTab === 'wavelengths'}
          <div class="mode-row">
            <div><p class="eyebrow">Modo de visualización</p><h3>Emisión / absorción</h3></div>
            <div class="segmented-control small">
              <button class:active={mode === 'emission'} type="button" on:click={() => (mode = 'emission')}>Emisión</button>
              <button class:active={mode === 'absorption'} type="button" on:click={() => (mode = 'absorption')}>Absorción</button>
            </div>
          </div>
          <SpectrumViewer lines={element.lines} {mode} title={`${element.name_es} (${element.symbol})`} />
        {:else if activeTab === 'levels'}
          <EnergyLevels lines={element.lines} />
        {:else if activeTab === 'lines'}
          <section class="modal-data-card">
            <div class="section-title-row compact">
              <div><p class="eyebrow">Tabla técnica</p><h2>Líneas espectrales</h2></div>
              <span class="range-pill">{element.lines.length} líneas</span>
            </div>

            {#if element.lines.length}
              <div class="technical-table modal-table">
                <table>
                  <thead><tr><th>Línea</th><th>Especie</th><th>λ</th><th>Región</th><th>Intensidad</th><th>Nivel inferior</th><th>Nivel superior</th><th>ΔE</th><th>Transición</th></tr></thead>
                  <tbody>
                    {#each element.lines as line}
                      <tr>
                        <td>{line.label}</td><td>{line.species}</td><td>{formatNm(line.wavelength_nm)}</td>
                        <td>{wavelengthRegion(line.wavelength_nm)}</td><td>{line.intensity.toFixed(2)}</td>
                        <td>{formatEv(line.lower_level_ev)}</td><td>{formatEv(line.upper_level_ev)}</td>
                        <td>{formatEv(energyJump(line))}</td><td>{line.transition}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            {:else}
              <p class="empty-copy technical-empty">No hay líneas espectrales tabulares para mostrar.</p>
            {/if}
          </section>
        {:else if activeTab === 'nist'}
          <section class="modal-data-card nist-panel">
            <div class="section-title-row compact">
              <div><p class="eyebrow">Procedencia y validación</p><h2>Estado de las fuentes NIST</h2></div>
              <span class="range-pill">{element.nist?.imported_line_count ?? 0} líneas importadas</span>
            </div>
            <p class="empty-copy">Esta sección valida la estructura de los CSV antes de utilizarlos en visualizaciones científicas.</p>

            {#if element.nist}
              <div class="nist-status-grid">
                {#each nistFiles as file}
                  <article class:problem={file.item.present && !file.item.table_like} class="nist-status-card">
                    <header><strong>{file.label}</strong><span>{statusLabel(file.item)}</span></header>
                    <dl>
                      <div><dt>Archivo</dt><dd>{file.item.file}</dd></div>
                      <div><dt>Ruta</dt><dd>{file.item.path || '—'}</dd></div>
                      <div><dt>Filas</dt><dd>{file.item.row_count}</dd></div>
                      <div><dt>Columnas</dt><dd>{file.item.columns.length ? file.item.columns.slice(0, 8).join(', ') : '—'}</dd></div>
                    </dl>
                    <p>{file.item.notes}</p>
                  </article>
                {/each}
              </div>
            {:else}
              <p class="empty-copy">No hay información NIST asociada a este elemento.</p>
            {/if}
          </section>
        {/if}
      </div>
    </section>
  </div>
{/if}
