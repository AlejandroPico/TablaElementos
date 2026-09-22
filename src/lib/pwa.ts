const isSecureContextForServiceWorker =
  window.isSecureContext || window.location.hostname === 'localhost';

if ('serviceWorker' in navigator && isSecureContextForServiceWorker) {
  window.addEventListener('load', () => {
    const baseUrl = new URL('./', document.baseURI);
    const serviceWorkerUrl = new URL('./service-worker.js', baseUrl);

    void navigator.serviceWorker.register(serviceWorkerUrl, {
      scope: baseUrl.pathname
    }).catch((error: unknown) => {
      console.warn('[TablaElementos] No se pudo registrar el modo instalable.', error);
    });
  });
}
