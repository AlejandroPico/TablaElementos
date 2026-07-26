import { GUIDE_TOPIC_LABELS } from './guideTopics';
import { openScientificGuide } from './guideBridge';

export {};

interface TabGuideLink {
  topic: string;
  shortLabel: string;
}

const GUIDE_BY_TAB: Record<string, TabGuideLink[]> = {
  Resumen: [
    { topic: 'vision', shortLabel: 'Cómo leer la ficha' },
    { topic: 'missing-data', shortLabel: 'Datos ausentes' }
  ],
  'Átomo 3D': [
    { topic: 'atom-model', shortLabel: 'Modelo 3D' },
    { topic: 'configuration', shortLabel: 'Configuración' }
  ],
  Electrones: [
    { topic: 'valence', shortLabel: 'Valencia' },
    { topic: 'ionization', shortLabel: 'Ionización' },
    { topic: 'affinity', shortLabel: 'Afinidad' }
  ],
  Radios: [
    { topic: 'radii', shortLabel: 'Tipos de radio' },
    { topic: 'ionic-radii', shortLabel: 'Radios iónicos' }
  ],
  'Cristal 3D': [
    { topic: 'crystals', shortLabel: 'Cristalografía' },
    { topic: 'allotropes', shortLabel: 'Alótropos' }
  ],
  Material: [
    { topic: 'material-properties', shortLabel: 'Propiedades' },
    { topic: 'transport', shortLabel: 'Transporte' },
    { topic: 'allotropes', shortLabel: 'Fases' }
  ],
  Nuclear: [
    { topic: 'nuclear-map', shortLabel: 'Mapa nuclear' },
    { topic: 'decay', shortLabel: 'Decaimiento' },
    { topic: 'nuclear-quantum', shortLabel: 'Espín y Q' }
  ],
  Termodinámica: [
    { topic: 'thermodynamics', shortLabel: 'Magnitudes' },
    { topic: 'phase-map', shortLabel: 'Fases' },
    { topic: 'thermal-series', shortLabel: 'Curvas térmicas' }
  ],
  Radiación: [
    { topic: 'xray', shortLabel: 'Rayos X' },
    { topic: 'attenuation', shortLabel: 'Atenuación' },
    { topic: 'xps-auger', shortLabel: 'XPS / Auger' },
    { topic: 'neutrons', shortLabel: 'Neutrones' }
  ],
  Propiedades: [
    { topic: 'physical', shortLabel: 'Propiedades físicas' },
    { topic: 'thermodynamics', shortLabel: 'Condiciones' }
  ],
  Isótopos: [
    { topic: 'isotopes', shortLabel: 'Qué es un isótopo' },
    { topic: 'decay', shortLabel: 'Vida media' },
    { topic: 'nuclear-quantum', shortLabel: 'Espín nuclear' }
  ],
  Espectro: [
    { topic: 'spectra', shortLabel: 'Espectro' },
    { topic: 'spectral-lines', shortLabel: 'Cobertura' }
  ],
  Líneas: [
    { topic: 'spectral-lines', shortLabel: 'Líneas' },
    { topic: 'levels', shortLabel: 'Niveles' }
  ],
  Niveles: [
    { topic: 'levels', shortLabel: 'Estados electrónicos' },
    { topic: 'spectra', shortLabel: 'Transiciones' }
  ],
  Tendencias: [
    { topic: 'trends', shortLabel: 'Tendencias' },
    { topic: 'comparison', shortLabel: 'Comparar' }
  ],
  Química: [
    { topic: 'chemistry', shortLabel: 'Química' },
    { topic: 'oxidation', shortLabel: 'Redox' },
    { topic: 'bonding', shortLabel: 'Enlace' }
  ],
  Contexto: [
    { topic: 'context', shortLabel: 'Historia y usos' },
    { topic: 'abundance', shortLabel: 'Abundancia' },
    { topic: 'biology', shortLabel: 'Biología' }
  ],
  Fuentes: [
    { topic: 'sources', shortLabel: 'Trazabilidad' },
    { topic: 'missing-data', shortLabel: 'Conflictos y huecos' }
  ]
};

const enhancedModals = new WeakSet<HTMLElement>();

function cleanTabLabel(button: HTMLButtonElement): string {
  return (button.textContent ?? '').replace(/\s*·\s*revisar\s*$/i, '').trim();
}

function makeEdgeButton(direction: -1 | 1): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = `master-tabs-edge ${direction < 0 ? 'edge-left' : 'edge-right'}`;
  button.setAttribute('aria-label', direction < 0 ? 'Mostrar pestañas anteriores' : 'Mostrar más pestañas');
  button.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${direction < 0 ? 'M15 5l-7 7 7 7' : 'M9 5l7 7-7 7'}"></path></svg>`;
  return button;
}

function buildGuideDock(content: HTMLElement): HTMLElement {
  const dock = document.createElement('aside');
  dock.className = 'context-guide-dock';
  dock.setAttribute('aria-label', 'Ayuda relacionada con esta pestaña');
  content.appendChild(dock);
  return dock;
}

function renderGuideDock(dock: HTMLElement, tabLabel: string): void {
  const links = GUIDE_BY_TAB[tabLabel] ?? [{ topic: 'vision', shortLabel: 'Guía general' }];
  dock.replaceChildren();

  const heading = document.createElement('span');
  heading.className = 'context-guide-heading';
  heading.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 10v7M12 7h.01"></path></svg><b>Entender esta pestaña</b>';
  dock.appendChild(heading);

  const list = document.createElement('div');
  list.className = 'context-guide-links';
  for (const link of links) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.guideTopic = link.topic;
    button.title = `Abrir en la guía: ${GUIDE_TOPIC_LABELS[link.topic] ?? link.shortLabel}`;
    button.innerHTML = `<span>${link.shortLabel}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5h11v11M19 5 7 17"></path></svg>`;
    button.addEventListener('click', () => openScientificGuide(link.topic));
    list.appendChild(button);
  }
  dock.appendChild(list);
}

function enhanceModal(modal: HTMLElement): void {
  if (enhancedModals.has(modal)) return;
  const nav = modal.querySelector<HTMLElement>('.modal-tabs.master-tabs');
  const content = modal.querySelector<HTMLElement>('.modal-content.master-content');
  if (!nav || !content || !nav.parentElement) return;

  enhancedModals.add(modal);
  modal.dataset.navigationEnhanced = 'true';

  const shell = document.createElement('div');
  shell.className = 'master-tabs-shell';
  nav.parentElement.insertBefore(shell, nav);

  const left = makeEdgeButton(-1);
  const right = makeEdgeButton(1);
  shell.append(left, nav, right);

  const dock = buildGuideDock(content);
  let scrollFrame = 0;
  let scrollDirection = 0;
  let scrollSpeed = 0;

  const stopAutoScroll = (): void => {
    scrollDirection = 0;
    scrollSpeed = 0;
    if (scrollFrame) cancelAnimationFrame(scrollFrame);
    scrollFrame = 0;
  };

  const autoScrollTick = (): void => {
    if (!nav.isConnected || !scrollDirection) {
      stopAutoScroll();
      return;
    }
    nav.scrollLeft += scrollDirection * scrollSpeed;
    scrollFrame = requestAnimationFrame(autoScrollTick);
  };

  const startAutoScroll = (direction: -1 | 1, speed = 8): void => {
    scrollDirection = direction;
    scrollSpeed = speed;
    if (!scrollFrame) scrollFrame = requestAnimationFrame(autoScrollTick);
  };

  const scrollPage = (direction: -1 | 1): void => {
    nav.scrollBy({ left: direction * Math.max(180, nav.clientWidth * 0.72), behavior: 'smooth' });
  };

  left.addEventListener('pointerenter', () => startAutoScroll(-1, 9));
  right.addEventListener('pointerenter', () => startAutoScroll(1, 9));
  left.addEventListener('pointerleave', stopAutoScroll);
  right.addEventListener('pointerleave', stopAutoScroll);
  left.addEventListener('click', () => scrollPage(-1));
  right.addEventListener('click', () => scrollPage(1));

  nav.addEventListener('pointermove', (event) => {
    if (event.pointerType !== 'mouse') return;
    const rect = nav.getBoundingClientRect();
    const threshold = Math.min(86, rect.width * 0.16);
    const fromLeft = event.clientX - rect.left;
    const fromRight = rect.right - event.clientX;
    if (fromLeft < threshold) {
      startAutoScroll(-1, 4 + (1 - fromLeft / threshold) * 13);
    } else if (fromRight < threshold) {
      startAutoScroll(1, 4 + (1 - fromRight / threshold) * 13);
    } else {
      stopAutoScroll();
    }
  });
  nav.addEventListener('pointerleave', stopAutoScroll);

  nav.addEventListener('wheel', (event) => {
    const verticalGesture = Math.abs(event.deltaY) > Math.abs(event.deltaX);
    if (!verticalGesture || nav.scrollWidth <= nav.clientWidth) return;
    event.preventDefault();
    nav.scrollLeft += event.deltaY;
  }, { passive: false });

  const updateEdges = (): void => {
    const max = Math.max(0, nav.scrollWidth - nav.clientWidth);
    shell.classList.toggle('at-start', nav.scrollLeft <= 2);
    shell.classList.toggle('at-end', nav.scrollLeft >= max - 2);
    shell.classList.toggle('has-overflow', max > 4);
  };

  const updateActiveTab = (): void => {
    const active = nav.querySelector<HTMLButtonElement>('button.active');
    if (!active) return;
    const label = cleanTabLabel(active);
    renderGuideDock(dock, label);
    active.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
    requestAnimationFrame(updateEdges);
  };

  nav.addEventListener('scroll', updateEdges, { passive: true });
  nav.addEventListener('click', () => requestAnimationFrame(updateActiveTab));

  const activeObserver = new MutationObserver((mutations) => {
    if (mutations.some((mutation) => mutation.type === 'attributes' && mutation.attributeName === 'class')) {
      updateActiveTab();
    }
  });
  activeObserver.observe(nav, { subtree: true, attributes: true, attributeFilter: ['class'] });

  requestAnimationFrame(() => {
    updateActiveTab();
    updateEdges();
    if (nav.scrollWidth > nav.clientWidth + 8 && nav.scrollLeft < 2) {
      window.setTimeout(() => {
        if (!nav.isConnected) return;
        nav.scrollTo({ left: 68, behavior: 'smooth' });
        window.setTimeout(() => nav.isConnected && nav.scrollTo({ left: 0, behavior: 'smooth' }), 520);
      }, 220);
    }
  });
}

function scanForModals(root: ParentNode = document): void {
  root.querySelectorAll<HTMLElement>('.master-modal').forEach(enhanceModal);
}

function startModalGuideEnhancer(): void {
  scanForModals();
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (!(node instanceof HTMLElement)) continue;
        if (node.matches('.master-modal')) enhanceModal(node);
        scanForModals(node);
      }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startModalGuideEnhancer, { once: true });
} else {
  startModalGuideEnhancer();
}
