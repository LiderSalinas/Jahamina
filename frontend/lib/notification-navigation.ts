import type { JahaminaNotification } from "./types";

const ALLOWED_PREFIXES = ["/reservas", "/viajes", "/mis-viajes"];

export function safeNotificationTarget(item: Pick<JahaminaNotification, "url_destino" | "tipo" | "reserva_id" | "viaje_id" | "conversacion_id">): string {
  const value = item.url_destino?.trim();
  if (value && value.startsWith("/") && !value.startsWith("//")) {
    try {
      const parsed = new URL(value, window.location.origin);
      if (parsed.origin === window.location.origin && ALLOWED_PREFIXES.some((prefix) => parsed.pathname === prefix || parsed.pathname.startsWith(`${prefix}/`))) return `${parsed.pathname}${parsed.search}`;
    } catch {
      // Fall through to metadata-based compatibility for old notifications.
    }
  }
  if (item.reserva_id) {
    return `/reservas/${item.reserva_id}${item.tipo === "mensaje_nuevo" && item.conversacion_id ? `?chat=${item.conversacion_id}` : ""}`;
  }
  if (item.viaje_id) return "/mis-viajes";
  return "/reservas";
}
