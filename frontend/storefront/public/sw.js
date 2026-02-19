const CACHE_NAME = 'shopapp-v1'
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
]

// Install: cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    )
    self.skipWaiting()
})

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    )
    self.clients.claim()
})

// Fetch strategy:
//  - API calls: Network-first (never cache POST/auth)
//  - Static assets: Cache-first
//  - Navigation: Network-first with offline fallback
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url)

    // Skip non-GET and API calls
    if (event.request.method !== 'GET') return
    if (url.pathname.startsWith('/api/')) return

    // Navigation requests — serve from network, fallback to cache
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() =>
                caches.match('/index.html')
            )
        )
        return
    }

    // Image requests — cache-first with network fallback
    if (event.request.destination === 'image') {
        event.respondWith(
            caches.match(event.request).then((cached) => {
                if (cached) return cached
                return fetch(event.request).then((response) => {
                    if (response.ok) {
                        const clone = response.clone()
                        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone))
                    }
                    return response
                })
            }).catch(() => new Response('', { status: 404 }))
        )
        return
    }

    // Other static assets: cache-first
    event.respondWith(
        caches.match(event.request).then((cached) => cached || fetch(event.request))
    )
})

// Background sync for offline cart operations (future)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-cart') {
        console.log('[SW] Background sync: cart')
    }
})
