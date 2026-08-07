import { api, ApiError } from "@/lib/api";
import type { PushSubscriptionItem } from "@/lib/types";


export function urlBase64ToUint8Array(value: string): Uint8Array<ArrayBuffer> {
  const normalized = value.trim();
  if (!normalized) throw new Error("La clave pública VAPID no está configurada.");
  const padding = "=".repeat((4 - normalized.length % 4) % 4);
  const base64 = (normalized + padding).replace(/-/g, "+").replace(/_/g, "/");
  let decoded: string;
  try {
    decoded = globalThis.atob(base64);
  } catch {
    throw new Error("La clave pública VAPID no es válida.");
  }
  const bytes = Uint8Array.from(decoded, (character) => character.charCodeAt(0));
  if (bytes.length !== 65) throw new Error("La clave pública VAPID no es una clave P-256 válida.");
  return bytes;
}

export function configuredVapidPublicKey(): string | null {
  return process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY?.trim() || null;
}

export function pushSupportState(): "supported" | "unsupported" | "insecure" {
  if (typeof window === "undefined" || !("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) return "unsupported";
  return window.isSecureContext ? "supported" : "insecure";
}

async function registrationForActivation(): Promise<ServiceWorkerRegistration> {
  const existing = await navigator.serviceWorker.getRegistration("/");
  if (!existing) await navigator.serviceWorker.register("/sw.js", { scope: "/" });
  return navigator.serviceWorker.ready;
}

function subscriptionPayload(subscription: PushSubscription) {
  const serialized = subscription.toJSON();
  if (!serialized.endpoint || !serialized.keys?.p256dh || !serialized.keys.auth) throw new Error("La suscripción Push está incompleta.");
  return {
    endpoint: serialized.endpoint,
    keys: { p256dh: serialized.keys.p256dh, auth: serialized.keys.auth },
    dispositivo_nombre: /Mobi|Android/i.test(navigator.userAgent) ? "Teléfono" : "Computadora",
  };
}

async function saveSubscription(subscription: PushSubscription, token: string): Promise<PushSubscriptionItem> {
  return api.subscribePush(subscriptionPayload(subscription), token);
}

export async function activatePush(token: string): Promise<PushSubscriptionItem> {
  const support = pushSupportState();
  if (support !== "supported") throw new Error(support === "insecure" ? "Las notificaciones requieren HTTPS o localhost." : "Este navegador no admite notificaciones Push.");
  const publicKey = configuredVapidPublicKey();
  if (!publicKey) throw new Error("Las notificaciones Push no están configuradas.");
  const config = await api.pushConfig();
  if (!config.enabled || !config.public_key) throw new Error("Las notificaciones Push no están habilitadas en el servidor.");
  if (config.public_key !== publicKey) throw new Error("La configuración Push del frontend y del servidor no coincide.");
  const permission = Notification.permission === "granted" ? "granted" : await Notification.requestPermission();
  if (permission !== "granted") throw new DOMException("Permiso denegado", "NotAllowedError");
  const registration = await registrationForActivation();
  const existing = await registration.pushManager.getSubscription();
  const subscription = existing ?? await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(publicKey) });
  try {
    return await saveSubscription(subscription, token);
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 409) throw error;
    await subscription.unsubscribe();
    const replacement = await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(publicKey) });
    return saveSubscription(replacement, token);
  }
}

export async function restorePushSubscription(token: string): Promise<PushSubscriptionItem | null> {
  if (pushSupportState() !== "supported" || Notification.permission !== "granted" || !configuredVapidPublicKey()) return null;
  const registration = await navigator.serviceWorker.getRegistration("/");
  const subscription = await registration?.pushManager.getSubscription();
  if (!subscription) return null;
  try {
    return await saveSubscription(subscription, token);
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 409) throw error;
    await subscription.unsubscribe();
    return null;
  }
}

export async function deactivatePush(token: string): Promise<void> {
  if (pushSupportState() !== "supported") return;
  const registration = await navigator.serviceWorker.getRegistration("/");
  const subscription = await registration?.pushManager.getSubscription();
  if (!subscription) return;
  try {
    await api.unsubscribeCurrentPush(subscription.endpoint, token);
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 404) throw error;
  }
  await subscription.unsubscribe();
}
