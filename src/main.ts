import { mount } from 'svelte';
import './styles/global.css';
import './styles/expanded.css';
import './styles/diagnostics.css';
import './styles/refinement.css';
import './styles/layout-modes.css';
import './styles/themes.css';
import './styles/interaction-refinement.css';
import App from './app/App.svelte';

const target = document.getElementById('app');

if (!target) {
  throw new Error('No se encontró el contenedor principal #app.');
}

const app = mount(App, { target });

export default app;
