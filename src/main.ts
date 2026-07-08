import { mount } from 'svelte';
import './styles/global.css';
import App from './app/App.svelte';

const target = document.getElementById('app');

if (!target) {
  throw new Error('No se encontró el contenedor principal #app.');
}

const app = mount(App, { target });

export default app;
