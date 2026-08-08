"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { JahaminaNotification, NotificationList } from "@/lib/types";
import { NotificationPermissionCard } from "./NotificationPermissionCard";
import { safeNotificationTarget } from "@/lib/notification-navigation";

const EMPTY: NotificationList = { items: [], total_no_leidas: 0 };

export function NotificationBell({ token }: { token: string }) {
  const router = useRouter();
  const [data, setData] = useState(EMPTY);
  const [open, setOpen] = useState(false);
  const socket = useRef<WebSocket | null>(null);
  const timer = useRef<number | null>(null);
  const bellRef = useRef<HTMLDivElement | null>(null);
  const refresh = useCallback(() => api.notifications(token).then(setData).catch(() => undefined), [token]);

  useEffect(() => {
    let active = true;
    refresh();
    const connect = async () => {
      try {
        const ws = new WebSocket(await api.notificationWebSocketUrl(token));
        socket.current = ws;
        ws.onmessage = (raw) => {
          const event = JSON.parse(raw.data) as { type: string; data: JahaminaNotification };
          if (event.type === "notification.created") setData((current) => current.items.some((item) => item.id === event.data.id) ? current : { items: [event.data, ...current.items], total_no_leidas: current.total_no_leidas + 1 });
        };
        ws.onclose = () => { if (active) timer.current = window.setTimeout(connect, 3000); };
      } catch { if (active) timer.current = window.setTimeout(connect, 5000); }
    };
    void connect();
    const poll = window.setInterval(refresh, 30000);
    return () => { active = false; socket.current?.close(); if (timer.current) window.clearTimeout(timer.current); window.clearInterval(poll); };
  }, [refresh, token]);

  useEffect(() => {
    if (!open) return;
    const closePanel = (event: PointerEvent) => {
      if (!bellRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeWithEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", closePanel);
    document.addEventListener("keydown", closeWithEscape);
    return () => {
      document.removeEventListener("pointerdown", closePanel);
      document.removeEventListener("keydown", closeWithEscape);
    };
  }, [open]);

  async function choose(item: JahaminaNotification) {
    if (!item.leida) await api.readNotification(item.id, token);
    setOpen(false); await refresh(); router.push(safeNotificationTarget(item));
  }
  async function readAll() { await api.readAllNotifications(token); await refresh(); }

  return <div className="notification-bell" ref={bellRef}>
    <button type="button" className="notification-bell-button" aria-label={`Notificaciones: ${data.total_no_leidas} sin leer`} aria-expanded={open} onClick={() => setOpen((value) => !value)}>
      <svg className="notification-bell-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"/><path d="M10 21h4"/></svg>
      {data.total_no_leidas > 0 && <span>{data.total_no_leidas > 99 ? "99+" : data.total_no_leidas}</span>}
    </button>
    {open && <section className="notification-panel" aria-label="Notificaciones" role="dialog">
      <header><div><b>Notificaciones</b><small>{data.total_no_leidas > 0 ? `${data.total_no_leidas} sin leer` : "Todo al día"}</small></div>{data.total_no_leidas > 0 && <button type="button" onClick={readAll}>Marcar todas como leídas</button>}</header>
      <NotificationPermissionCard token={token}/>
      <div className="notification-items">{data.items.length === 0 ? <p className="notification-empty">Todavía no tenés avisos.</p> : data.items.map((item) => <button type="button" className={item.leida ? "" : "is-unread"} onClick={() => void choose(item)} key={item.id}><span className="notification-kind" aria-hidden>{item.tipo === "mensaje_nuevo" ? "M" : "V"}</span><span><b>{item.titulo}</b><small>{item.cuerpo}</small><time>{new Date(item.creada_en).toLocaleString("es-PY")}</time></span></button>)}</div>
    </section>}
  </div>;
}
