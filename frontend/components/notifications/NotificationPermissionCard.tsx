"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { activatePush, configuredVapidPublicKey, deactivatePush, pushSupportState, restorePushSubscription } from "@/lib/push-notifications";
import type { PushSubscriptionItem } from "@/lib/types";

type PermissionState = "available" | "loading" | "enabled" | "denied" | "unsupported" | "insecure" | "unconfigured" | "error";

export function NotificationPermissionCard({ token }: { token: string }) {
  const [state, setState] = useState<PermissionState>(() => configuredVapidPublicKey() ? "available" : "unconfigured");
  const [subscription, setSubscription] = useState<PushSubscriptionItem | null>(null);

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      const support = pushSupportState();
      if (support !== "supported") {
        if (active) setState(support === "insecure" ? "insecure" : "unsupported");
        return;
      }
      if (Notification.permission === "denied") {
        if (active) setState("denied");
        return;
      }
      restorePushSubscription(token).then((item) => {
        if (active && item) { setSubscription(item); setState("enabled"); }
      }).catch(() => { if (active) setState("error"); });
    }, 0);
    return () => { active = false; window.clearTimeout(timer); };
  }, [token]);

  async function activate() {
    setState("loading");
    try {
      const saved = await activatePush(token);
      setSubscription(saved);
      setState("enabled");
    } catch (error) {
      if (error instanceof DOMException && error.name === "NotAllowedError") setState("denied");
      else if (error instanceof Error && error.message.includes("configurad")) setState("unconfigured");
      else if (error instanceof Error && error.message.includes("HTTPS")) setState("insecure");
      else setState("error");
    }
  }

  async function deactivate() {
    setState("loading");
    try {
      await deactivatePush(token);
      setSubscription(null);
      setState("available");
    } catch { setState("error"); }
  }

  async function update(category: "mensajes" | "reservas" | "viaje", enabled: boolean) {
    if (!subscription) return;
    try {
      const updated = await api.updatePushPreferences(subscription.id, { mensajes: subscription.mensajes, reservas: subscription.reservas, viaje: subscription.viaje, [category]: enabled }, token);
      setSubscription(updated);
    } catch { setState("error"); }
  }

  if (state === "enabled" && subscription) return <div className="notification-permission is-success"><b>Notificaciones activadas</b><div className="push-preferences"><label><input type="checkbox" checked={subscription.mensajes} onChange={(event) => void update("mensajes", event.target.checked)}/> Mensajes</label><label><input type="checkbox" checked={subscription.reservas} onChange={(event) => void update("reservas", event.target.checked)}/> Reservas</label><label><input type="checkbox" checked={subscription.viaje} onChange={(event) => void update("viaje", event.target.checked)}/> Viaje</label></div><button type="button" className="button-secondary" onClick={() => void deactivate()}>Desactivar en este dispositivo</button></div>;
  const messages: Partial<Record<PermissionState, string>> = { denied: "El permiso fue rechazado. Podés habilitarlo desde la configuración del navegador.", unsupported: "Este navegador no admite notificaciones Push.", insecure: "Las notificaciones requieren HTTPS o localhost.", unconfigured: "Las notificaciones Push todavía no están configuradas.", error: "No pudimos actualizar las notificaciones. Intentá nuevamente." };
  return <div className="notification-permission"><b>Recibí avisos sobre mensajes y cambios de tu viaje.</b>{messages[state] && <p role="status">{messages[state]}</p>}<button type="button" disabled={state === "loading" || state === "denied" || state === "unsupported" || state === "insecure" || state === "unconfigured"} onClick={() => void activate()}>{state === "loading" ? "Activando…" : "Activar notificaciones"}</button></div>;
}
