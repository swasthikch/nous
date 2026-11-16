/**
 * NOUS Service Worker (Phase 9 - Progressive Web App Edition)
 * Enables offline shell caching, cross-device background sync, and push notifications.
 */

const CACHE_NAME = "nous-cache-v1.1.0";
const ASSETS_TO_CACHE = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/manifest.json"
];

// Install Event - Pre-cache App Shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[NOUS SW] Pre-caching offline app shell");
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn("[NOUS SW] Pre-caching partial warning:", err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate Event - Clean up stale caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[NOUS SW] Removing deprecated cache:", key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event - Network first with Cache fallback for static assets
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Skip caching API requests, SSE streams, or external endpoints
  if (url.pathname.startsWith("/api/") || event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(async () => {
        const cachedResponse = await caches.match(event.request);
        if (cachedResponse) return cachedResponse;
        if (event.request.mode === "navigate") {
          return caches.match("/");
        }
        return new Response("Offline · NOUS local cache fallback", {
          status: 503,
          statusText: "Service Unavailable",
          headers: { "Content-Type": "text/plain" }
        });
      })
  );
});

// Push Notification Event
self.addEventListener("push", (event) => {
  let data = { title: "NOUS Alert", body: "Notification from your AI Operating System" };
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: "/static/icons/icon-192.png",
    badge: "/static/icons/icon-192.png",
    data: data.url || "/"
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification Click Event
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      if (clientList.length > 0) {
        let client = clientList[0];
        for (let i = 0; i < clientList.length; i++) {
          if (clientList[i].focused) {
            client = clientList[i];
            break;
          }
        }
        return client.focus();
      }
      return clients.openWindow(event.notification.data || "/");
    })
  );
});
