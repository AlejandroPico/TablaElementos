<script lang="ts">
  import type { DataRow, ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;
  export let loading = false;

  interface StructureRecord {
    name: string;
    structure: string;
    spaceGroup: string;
    a: string;
    b: string;
    c: string;
    alpha: string;
    beta: string;
    gamma: string;
    phase: string;
    source: string;
    materialId: string;
  }

  let selectedIndex = 0;
  let rotationX = -22;
  let rotationY = 34;
  let dragging = false;
  let pointerX = 0;
  let pointerY = 0;

  function valueFrom(rows: DataRow[], property: string, fallback = ''): string {
    return rows.find((row) => row.property === property)?.value || fallback;
  }

  function structures(): StructureRecord[] {
    const rows = elementData?.domains.materials?.rows ?? [];
    const grouped = new Map<string, DataRow[]>();

    for (const row of rows) {
      const key = row.structure_id || row.material_id || row.phase || row.structure || 'principal';
      const list = grouped.get(key) ?? [];
      list.push(row);
      grouped.set(key, list);
    }

    return Array.from(grouped.entries()).flatMap(([key, group]) => {
      const structure = valueFrom(group, 'crystal_structure', group[0]?.structure || '');
      const allotrope = valueFrom(group, 'allotrope', group[0]?.allotrope || '');
      const spaceGroup = valueFrom(group, 'space_group', group[0]?.space_group || '');
      if (!structure && !allotrope && !spaceGroup) return [];
      return [{
        name: allotrope || group[0]?.phase || structure || key,
        structure,
        spaceGroup,
        a: valueFrom(group, 'lattice_a', group[0]?.lattice_a || ''),
        b: valueFrom(group, 'lattice_b', group[0]?.lattice_b || ''),
        c: valueFrom(group, 'lattice_c', group[0]?.lattice_c || ''),
        alpha: valueFrom(group, 'lattice_alpha', group[0]?.lattice_alpha || '90'),
        beta: valueFrom(group, 'lattice_beta', group[0]?.lattice_beta || '90'),
        gamma: valueFrom(group, 'lattice_gamma', group[0]?.lattice_gamma || '90'),
        phase: group[0]?.phase || '',
        source: group[0]?.source || '',
        materialId: group[0]?.material_id || ''
      }];
    });
  }

  function structureClass(record: StructureRecord | undefined): string {
    const text = `${record?.structure ?? ''} ${record?.spaceGroup ?? ''}`.toLowerCase();
    if (text.includes('face') || text.includes('fcc') || text.includes('fm-3m')) return 'fcc';
    if (text.includes('body') || text.includes('bcc') || text.includes('im-3m')) return 'bcc';
    if (text.includes('hex') || text.includes('hcp') || text.includes('p63/mmc')) return 'hcp';
    if (text.includes('diamond') || text.includes('fd-3m')) return 'diamond';
    return 'generic';
  }

  function beginDrag(event: PointerEvent): void {
    dragging = true;
    pointerX = event.clientX;
    pointerY = event.clientY;
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function drag(event: PointerEvent): void {
    if (!dragging) return;
    rotationY += (event.clientX - pointerX) * 0.45;
    rotationX -= (event.clientY - pointerY) * 0.35;
    rotationX = Math.max(-75, Math.min(75, rotationX));
    pointerX = event.clientX;
    pointerY = event.clientY;
  }

  function endDrag(): void {
    dragging = false;
  }

  $: records = structures();
  $: if (selectedIndex >= records.length) selectedIndex = 0;
  $: selected = records[selectedIndex];
  $: latticeClass = structureClass(selected);
</script>

<div class="advanced-science-pane crystal-pane">
  {#if loading}
    <div class="modal-load-state"><span></span><p>Cargando estructuras cristalinas…</p></div>
  {:else}
    <section class="science-hero crystal-hero">
      <div>
        <p>Materia condensada</p>
        <h3>Estructuras cristalinas y alótropos</h3>
        <small>Cada fase se mantiene como un registro independiente con grupo espacial, parámetros de red y procedencia.</small>
      </div>
      <strong class="science-symbol-mark">{element?.symbol}</strong>
    </section>

    {#if records.length}
      <section class="crystal-workspace flat-split-workspace">
        <div class="crystal-viewer-shell">
          <div
            class="crystal-stage"
            role="application"
            aria-label="Visor tridimensional de celda unidad; arrastra para girar"
            on:pointerdown={beginDrag}
            on:pointermove={drag}
            on:pointerup={endDrag}
            on:pointercancel={endDrag}
          >
            <div class={`unit-cell unit-cell-${latticeClass}`} style={`--rx:${rotationX}deg;--ry:${rotationY}deg;`}>
              <span class="cell-face face-front"></span><span class="cell-face face-back"></span>
              <span class="cell-face face-left"></span><span class="cell-face face-right"></span>
              <span class="cell-face face-top"></span><span class="cell-face face-bottom"></span>
              {#each Array.from({ length: 8 }) as _, index}<i class={`lattice-atom atom-corner atom-${index}`}></i>{/each}
              {#if latticeClass === 'bcc'}<i class="lattice-atom atom-center"></i>{/if}
              {#if latticeClass === 'fcc'}
                {#each Array.from({ length: 6 }) as _, index}<i class={`lattice-atom atom-face atom-face-${index}`}></i>{/each}
              {/if}
              {#if latticeClass === 'diamond'}
                {#each Array.from({ length: 4 }) as _, index}<i class={`lattice-atom atom-inner atom-inner-${index}`}></i>{/each}
              {/if}
              {#if latticeClass === 'hcp'}
                {#each Array.from({ length: 6 }) as _, index}<i class={`lattice-atom atom-hex atom-hex-${index}`}></i>{/each}
              {/if}
            </div>
            <span class="crystal-drag-hint">Arrastrar para girar</span>
          </div>
        </div>

        <aside class="crystal-data-panel">
          <header><small>Fase seleccionada</small><h3>{selected?.name}</h3></header>
          <dl>
            <div><dt>Estructura</dt><dd>{selected?.structure || '—'}</dd></div>
            <div><dt>Grupo espacial</dt><dd>{selected?.spaceGroup || '—'}</dd></div>
            <div><dt>Parámetro a</dt><dd>{selected?.a || '—'}</dd></div>
            <div><dt>Parámetro b</dt><dd>{selected?.b || '—'}</dd></div>
            <div><dt>Parámetro c</dt><dd>{selected?.c || '—'}</dd></div>
            <div><dt>Ángulos</dt><dd>{selected ? `${selected.alpha || '—'} · ${selected.beta || '—'} · ${selected.gamma || '—'}` : '—'}</dd></div>
            <div><dt>Material ID</dt><dd>{selected?.materialId || '—'}</dd></div>
            <div><dt>Fuente</dt><dd>{selected?.source || '—'}</dd></div>
          </dl>
        </aside>
      </section>

      {#if records.length > 1}
        <nav class="allotrope-selector" aria-label="Seleccionar alótropo o fase">
          {#each records as record, index}
            <button class:active={selectedIndex === index} type="button" on:click={() => (selectedIndex = index)}><strong>{record.name}</strong><small>{record.structure || record.spaceGroup || 'estructura'}</small></button>
          {/each}
        </nav>
      {/if}
    {:else}
      <div class="science-empty-state"><strong>Sin estructura cristalina importada</strong><p>El visor está preparado para leer fases desde <code>materials.csv</code>. La importación completa desde Materials Project requiere una clave API.</p></div>
    {/if}

    <p class="science-method-note">El visor representa la topología de la celda de forma didáctica. Para reproducción cristalográfica exacta se conservarán también coordenadas fraccionarias y archivos CIF cuando la fuente lo permita.</p>
  {/if}
</div>
