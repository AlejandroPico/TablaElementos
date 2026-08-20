<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';

  export let open = false;

  const dispatch = createEventDispatcher<{ close: void }>();

  function closeOnBackdrop(event: MouseEvent): void {
    if (event.currentTarget === event.target) dispatch('close');
  }

  onMount(() => {
    const handleKeydown = (event: KeyboardEvent): void => {
      if (open && event.key === 'Escape') dispatch('close');
    };
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
</script>

{#if open}
  <div class="about-backdrop" role="presentation" on:click={closeOnBackdrop}>
    <div class="about-dialog" role="dialog" aria-modal="true" aria-labelledby="about-title" tabindex="-1">
      <header class="about-header">
        <div>
          <p>Acerca del proyecto</p>
          <h2 id="about-title">Tabla Elementos</h2>
        </div>
        <button type="button" aria-label="Cerrar acerca del proyecto" title="Cerrar" on:click={() => dispatch('close')}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"></path></svg>
        </button>
      </header>

      <div class="about-body">
        <div class="about-introduction">
          <span class="about-mark" aria-hidden="true">Te</span>
          <div>
            <strong>Una tabla periódica científica, visual e interactiva</strong>
            <p>Explora cada elemento desde su estructura electrónica y cristalina hasta sus propiedades materiales, nucleares, termodinámicas, espectrales y radiológicas.</p>
          </div>
        </div>

        <dl class="about-facts">
          <div><dt>Versión</dt><dd>0.5.1</dd></div>
          <div><dt>Tecnología</dt><dd>Svelte · TypeScript · D3</dd></div>
          <div><dt>Cobertura</dt><dd>118 elementos</dd></div>
          <div><dt>Datos</dt><dd>NIST · PubChem · CIAAW · IAEA</dd></div>
        </dl>

        <section class="about-author">
          <p>Autor</p>
          <h3>Alejandro Pico</h3>
          <span>Desarrollador de software y creador de proyectos interactivos centrados en ciencia, visualización de datos y herramientas digitales.</span>
        </section>
      </div>

      <footer class="about-links">
        <a href="https://alejandropico.github.io/Portfolio/" target="_blank" rel="noreferrer">
          <span>Portfolio</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5h11v11M19 5 7 17"></path></svg>
        </a>
        <a href="https://github.com/AlejandroPico/TablaElementos" target="_blank" rel="noreferrer">
          <span>Repositorio en GitHub</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5h11v11M19 5 7 17"></path></svg>
        </a>
      </footer>
    </div>
  </div>
{/if}
