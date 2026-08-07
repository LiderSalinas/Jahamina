const FALLBACK_URL = "/reservas";
const ALLOWED_ROUTES = ["/reservas", "/viajes", "/mis-viajes"];

function safeInternalUrl(value) {
  if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//")) return FALLBACK_URL;
  try {
    const parsed = new URL(value, self.location.origin);
    const allowed = parsed.origin === self.location.origin && ALLOWED_ROUTES.some((prefix) => parsed.pathname === prefix || parsed.pathname.startsWith(`${prefix}/`));
    return allowed ? `${parsed.pathname}${parsed.search}` : FALLBACK_URL;
  } catch {
    return FALLBACK_URL;
  }
}

self.addEventListener("push", (event) => {
  let payload = {};
  try { payload = event.data ? event.data.json() : {}; } catch { payload = {}; }
  const url = safeInternalUrl(payload.data?.url ?? payload.url);
  event.waitUntil(self.registration.showNotification(payload.title || "Jahamina", {
    body: payload.body || "Tenés una novedad en tu viaje.",
    icon: payload.icon || "/icons/jahamina.svg",
    badge: payload.badge || "/icons/jahamina.svg",
    tag: payload.tag || "jahamina",
    data: { url },
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = safeInternalUrl(event.notification.data?.url);
  event.waitUntil((async () => {
    const windows = await clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const client of windows) {
      if ("navigate" in client) await client.navigate(url);
      if ("focus" in client) return client.focus();
    }
    return clients.openWindow(url);
  })());
});
