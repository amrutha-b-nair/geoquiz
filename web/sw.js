// Offline support: cache the app shell up front, country images as they are seen.
// Bump VERSION whenever you change files in web/ so users get the update.
const VERSION = 'geoquiz-v1';
const SHELL = [
  './',
  'index.html',
  'css/style.css',
  'js/app.js',
  'js/match.js',
  'data/countries.json',
  'sound/correct.wav',
  'sound/wrong.mp3',
  'manifest.webmanifest',
  'icons/icon-192.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(VERSION).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET' || new URL(request.url).origin !== location.origin) return;
  event.respondWith(
    caches.match(request).then((cached) =>
      cached ||
      fetch(request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(VERSION).then((cache) => cache.put(request, copy));
        }
        return response;
      })
    )
  );
});
