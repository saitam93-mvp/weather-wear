// sw.js - Service Worker básico para cumplir requisitos PWA
self.addEventListener('install', (e) => {
  console.log('[Service Worker] Instalado');
});

self.addEventListener('fetch', (e) => {
  // Streamlit requiere conexión, así que solo pasamos las peticiones normalmente
  e.respondWith(fetch(e.request));
});