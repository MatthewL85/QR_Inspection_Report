const LOGIXPM_APP_SHELL_CACHE = "logixpm-app-shell-v21";

const STATIC_ASSETS = [
  "/static/manifest.webmanifest",
  "/static/styles.css",
  "/static/sidebar_mobile_collapse.js",
  "/static/js/register_app_shell.js",
  "/static/assets/img/favicon.png",
  "/static/assets/img/apple-icon.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(LOGIXPM_APP_SHELL_CACHE)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .catch(() => undefined)
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys
        .filter((key) => key !== LOGIXPM_APP_SHELL_CACHE)
        .map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  if (!url.pathname.startsWith("/static/")) {
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => (
      cached || fetch(request).then((response) => {
        const copy = response.clone();
        caches.open(LOGIXPM_APP_SHELL_CACHE).then((cache) => cache.put(request, copy));
        return response;
      })
    ))
  );
});
