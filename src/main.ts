import { mount } from 'svelte';
import './styles/global.css';
import './styles/expanded.css';
import './styles/diagnostics.css';
import './styles/refinement.css';
import './styles/layout-modes.css';
import './styles/themes.css';
import './styles/interaction-refinement.css';
import './styles/modal-data.css';
import './styles/modal-refinement.css';
import './styles/workspace-redesign.css';
import './styles/ficha-density.css';
import './styles/cell-progressive.css';
import './styles/periodic-info-guide.css';
import './styles/filter-panel.css';
import './styles/filter-panel-v2.css';
import './styles/visual-consistency.css';
import './styles/layout-transition-v2.css';
import './styles/layout-transition-v4.css';
import './styles/zoom-stability.css';
import './styles/advanced-science.css';
import './styles/science-phase-2.css';
import './styles/scientific-workspaces.css';
import './styles/unified-science.css';
import './lib/progressiveCellEnhancer';
import './lib/zoomRenderStabilizer';
import App from './app/App.svelte';

const target = document.getElementById('app');

if (!target) {
  throw new Error('No se encontró el contenedor principal #app.');
}

const app = mount(App, { target });

export default app;
