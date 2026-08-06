"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PushSubscriptionItem } from "@/lib/types";

type PermissionState = "available" | "loading" | "enabled" | "denied" | "unsupported" | "insecure" | "error";

function applicationServerKey(value: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - value.length % 4) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(base64), (character) => character.charCodeAt(0));
}

export function NotificationPermissionCard({ token }: { token: string }) {
  const [state, setState] = useState<PermissionState>("available");
  const [subscription, setSubscription] = useState<PushSubscriptionItem|null>(null);
  useEffect(()=>{const timer=window.setTimeout(()=>api.pushSubscriptions(token).then(items=>{if(items[0]){setSubscription(items[0]);setState("enabled");}}).catch(()=>undefined),0);return()=>window.clearTimeout(timer);},[token]);

  async function activate() {
    if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) { setState("unsupported"); return; }
    if (!window.isSecureContext) { setState("insecure"); return; }
    setState("loading");
    try {
      const config = await api.pushConfig();
      if (!config.enabled || !config.public_key) { setState("unsupported"); return; }
      const permission = await Notification.requestPermission();
      if (permission !== "granted") { setState("denied"); return; }
      const registration = await navigator.serviceWorker.register("/sw.js");
      const subscription = await registration.pushManager.subscribe({ userVisibleOnly:true, applicationServerKey:applicationServerKey(config.public_key) });
      const serialized = subscription.toJSON();
      if (!serialized.endpoint || !serialized.keys?.p256dh || !serialized.keys.auth) throw new Error("Suscripción incompleta");
      const saved=await api.subscribePush({endpoint:serialized.endpoint,keys:{p256dh:serialized.keys.p256dh,auth:serialized.keys.auth},dispositivo_nombre:/Mobi/i.test(navigator.userAgent)?"Teléfono":"Computadora"},token);
      setSubscription(saved);
      setState("enabled");
    } catch { setState("error"); }
  }

  async function update(category:"mensajes"|"reservas"|"viaje",enabled:boolean){if(!subscription)return;const updated=await api.updatePushPreferences(subscription.id,{mensajes:subscription.mensajes,reservas:subscription.reservas,viaje:subscription.viaje,[category]:enabled},token);setSubscription(updated);}
  if (state === "enabled"&&subscription) return <div className="notification-permission is-success"><b>Notificaciones activadas</b><div className="push-preferences"><label><input type="checkbox" checked={subscription.mensajes} onChange={event=>void update("mensajes",event.target.checked)}/> Mensajes</label><label><input type="checkbox" checked={subscription.reservas} onChange={event=>void update("reservas",event.target.checked)}/> Reservas</label><label><input type="checkbox" checked={subscription.viaje} onChange={event=>void update("viaje",event.target.checked)}/> Viaje</label></div></div>;
  const messages:Partial<Record<PermissionState,string>>={denied:"El permiso fue rechazado. Podés habilitarlo desde el navegador.",unsupported:"Las notificaciones Push no están disponibles aquí.",insecure:"Las notificaciones requieren HTTPS o localhost.",error:"No pudimos activar las notificaciones."};
  return <div className="notification-permission"><b>Recibe avisos sobre mensajes y cambios de tu viaje.</b>{messages[state]&&<p role="status">{messages[state]}</p>}<button type="button" disabled={state==="loading"||state==="denied"} onClick={activate}>{state==="loading"?"Activando…":"Activar notificaciones"}</button></div>;
}
