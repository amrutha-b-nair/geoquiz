// Offline support.
//
// Strategy: network first, cache as fallback. While online, players always
// get the latest deployed files; the cache is only used when the network
// fails (offline play). Requests revalidate with the server ("no-cache"), so
// the browser's HTTP cache (GitHub Pages allows 10 minutes) can never serve
// an outdated file after a deploy.
//
// VERSION is replaced with the commit id on every deploy (see
// .github/workflows/pages.yml) so old caches are cleaned up.
const VERSION = 'geoquiz-v4';
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
  event.waitUntil(
    caches.open(VERSION)
      // cache: 'reload' skips the HTTP cache so the new version stores new files.
      .then((cache) => cache.addAll(SHELL.map((url) => new Request(url, { cache: 'reload' }))))
      .then(() => self.skipWaiting())
  );
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
    fetch(request.url, { cache: 'no-cache', credentials: 'same-origin' })
      .then((response) => {
        if (response.ok) {
          const copy = response.clone();
          event.waitUntil(caches.open(VERSION).then((cache) => cache.put(request, copy)));
        }
        return response;
      })
      .catch(() => caches.match(request, { ignoreSearch: true }).then((cached) => cached || Response.error()))
  );
});
