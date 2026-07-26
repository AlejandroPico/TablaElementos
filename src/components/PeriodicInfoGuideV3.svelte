<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { GUIDE_TOPICS, type GuideTopic } from '../lib/guideTopics';

  export let open = false;
  export let topic = 'vision';

  const dispatch = createEventDispatcher<{ close: void }>();
  let activeId = 'vision';
  let query = '';
  let scrollElement: HTMLDivElement;
  let guideNav: HTMLElement;
  let lastAppliedTopic = '';

  $: normalizedQuery = query.trim().toLocaleLowerCase('es-ES');
  $: filteredTopics = normalizedQuery
    ? GUIDE_TOPICS.filter((item) => {
        const haystack = [item.label, item.title, item.summary, item.section, ...item.paragraphs]
          .join(' ')
          .toLocaleLowerCase('es-ES');
        return haystack.includes(normalizedQuery);
      })
    : GUIDE_TOPICS;
  $: activeTopic = GUIDE_TOPICS.find((item) => item.id === activeId) ?? GUIDE_TOPICS[0]!;

  $: if (open && topic !== lastAppliedTopic) {
    const requested = GUIDE_TOPICS.some((item) => item.id === topic) ? topic : 'vision';
    activeId = requested;
    query = '';
    lastAppliedTopic = topic;
    requestAnimationFrame(() => {
      scrollElement?.scrollTo({ top: 0, behavior: 'auto' });
      revealActiveTopic();
    });
  }

  $: if (!open && lastAppliedTopic) lastAppliedTopic = '';

  function selectTopic(id: string): void {
    activeId = id;
    scrollElement?.scrollTo({ top: 0, behavior: 'smooth' });
    requestAnimationFrame(revealActiveTopic);
  }

  function revealActiveTopic(): void {
    const button = guideNav?.querySelector<HTMLElement>(`[data-guide-topic="${activeId}"]`);
    button?.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' });
  }

  function closeFromBackdrop(event: MouseEvent): void {
    if (event.currentTarget === event.target) dispatch('close');
  }

  function clearSearch(): void {
    query = '';
    requestAnimationFrame(revealActiveTopic);
  }

  function sectionStartsAt(items: GuideTopic[], index: number): boolean {
    return index === 0 || items[index - 1]?.section !== items[index]?.section;
  }

  onMount(() => {
    const handleKey = (event: KeyboardEvent): void => {
      if (open && event.key === 'Escape') dispatch('close');
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  });
</script>

{#if open}
  <div class="periodic-guide-backdrop guide-v3-backdrop" role="presentation" on:click={closeFromBackdrop}>
    <div class="periodic-guide guide-v3" role="dialog" aria-modal="true" aria-label="Guía científica completa de la tabla periódica">
      <header class="periodic-guide-head guide-v3-head">
        <div>
          <p>Guía científica · {GUIDE_TOPICS.length} capítulos</p>
          <h2>Tabla periódica de los elementos</h2>
          <small>Explicaciones contextuales para cada pestaña, visualización, magnitud, ausencia de datos y fuente.</small>
        </div>
        <button type="button" aria-label="Cerrar guía" title="Cerrar" on:click={() => dispatch('close')}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"></path></svg>
        </button>
      </header>

      <aside class="guide-v3-index">
        <label class="guide-v3-search">
          <span>Buscar en la guía</span>
          <div>
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"></circle><path d="m15.5 15.5 5 5"></path></svg>
            <input bind:value={query} type="search" placeholder="Valencia, isótopos, XPS…" />
            {#if query}<button type="button" aria-label="Limpiar búsqueda" on:click={clearSearch}>×</button>{/if}
          </div>
        </label>

        <nav bind:this={guideNav} class="periodic-guide-tabs guide-v3-tabs" aria-label="Capítulos de la guía">
          {#each filteredTopics as item, index}
            {#if sectionStartsAt(filteredTopics, index)}<span class="guide-section-label">{item.section}</span>{/if}
            <button
              class:active={activeId === item.id}
              data-guide-topic={item.id}
              type="button"
              on:click={() => selectTopic(item.id)}
            >
              <b>{item.label}</b>
              <small>{item.summary}</small>
            </button>
          {:else}
            <div class="guide-search-empty"><strong>Sin coincidencias</strong><span>Prueba con otro concepto o elimina la búsqueda.</span></div>
          {/each}
        </nav>
      </aside>

      <div bind:this={scrollElement} class="periodic-guide-scroll guide-v3-scroll" role="region" aria-label="Contenido del capítulo">
        <section class="periodic-guide-section guide-v3-section">
          <p class="guide-topic-section">{activeTopic.section}</p>
          <h3>{activeTopic.title}</h3>
          <strong class="guide-topic-summary">{activeTopic.summary}</strong>
          {#each activeTopic.paragraphs as paragraph}<p>{paragraph}</p>{/each}

          {#if activeTopic.rows?.length}
            <div class="periodic-guide-table guide-v3-table">
              {#each activeTopic.rows as row}
                <div><b>{row.term}</b><span>{row.description}</span></div>
              {/each}
            </div>
          {/if}

          {#if activeTopic.callout}<div class="periodic-guide-callout">{activeTopic.callout}</div>{/if}

          {#if activeTopic.links?.length}
            <div class="periodic-guide-links">
              <span>Fuentes y ampliación:</span>
              {#each activeTopic.links as link}<a href={link.url} target="_blank" rel="noreferrer">{link.label}</a>{/each}
            </div>
          {/if}
        </section>
      </div>
    </div>
  </div>
{/if}
