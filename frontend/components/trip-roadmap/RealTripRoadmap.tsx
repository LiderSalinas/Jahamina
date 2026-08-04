"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Roadmap } from "@/lib/types";
import { TripMapPreview } from "./TripMapPreview";
import { TripPrimaryAction } from "./TripPrimaryAction";
import { TripTimeline } from "./TripTimeline";
import type { RoadmapStop, ScenarioDefinition, TimelineStep } from "./types";

function visibleStatus(data: Roadmap): string {
  if (data.reserva.estado === "cancelada" || data.viaje.estado === "cancelado") return "Viaje cancelado";
  if (data.viaje.estado === "finalizado") return "Viaje finalizado";
  if (["en_curso", "pausado"].includes(data.viaje.estado)) return "Viaje en curso";
  if (["conductor_en_camino", "conductor_en_punto", "abordaje"].includes(data.viaje.estado)) return "Conductor en camino";
  if (data.punto_encuentro.estado === "confirmado") return "Punto de encuentro acordado";
  return "Reserva confirmada";
}

export function RealTripRoadmap({ reservationId, token }: { reservationId: number; token: string }) {
  const [data, setData] = useState<Roadmap | null>(null);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(0);
  const socketRef = useRef<WebSocket | null>(null);

  const load = useCallback(async () => {
    try { setData(await api.roadmap(reservationId, token)); setLoadError(""); }
    catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) setLoadError("Tu sesión venció. Inicia sesión nuevamente.");
      else if (caught instanceof ApiError && caught.status === 404) setLoadError("No encontramos esta reserva o no tienes acceso.");
      else setLoadError(caught instanceof ApiError ? caught.message : "No se pudo cargar la hoja de ruta.");
    }
  }, [reservationId, token]);

  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer); }, [load]);
  useEffect(() => {
    let stopped = false; let retry: number | undefined;
    const connect = async () => {
      try {
        const url = await api.roadmapWebSocketUrl(reservationId, token);
        if (stopped || socketRef.current) return;
        const socket = new WebSocket(url); socketRef.current = socket;
        socket.onmessage = (message) => { const event = JSON.parse(message.data) as { type: string }; if (!['connected', 'pong'].includes(event.type)) void load(); };
        socket.onclose = () => { socketRef.current = null; if (!stopped) retry = window.setTimeout(connect, 2000); };
      } catch { if (!stopped) retry = window.setTimeout(connect, 3000); }
    };
    void connect();
    return () => { stopped = true; if (retry) window.clearTimeout(retry); socketRef.current?.close(); socketRef.current = null; };
  }, [load, reservationId, token]);

  const stops = useMemo<RoadmapStop[]>(() => (data?.paradas ?? []).map((stop) => ({
    time: stop.hora_estimada ? new Date(stop.hora_estimada).toLocaleTimeString("es-PY", { hour: "2-digit", minute: "2-digit" }) : "",
    title: stop.nombre_publico,
    passenger: stop.tipo,
    detail: stop.zona_general ?? "Zona todavía no definida",
    occupancy: "",
    status: stop.estado === "completada" ? "completed" : stop.estado === "actual" ? "current" : stop.estado === "cancelada" ? "cancelled" : "pending",
  })), [data]);
  const timeline = useMemo<TimelineStep[]>(() => (data?.hoja_ruta ?? []).slice(0, 5).map((step, index) => ({
    title: step.titulo,
    detail: step.descripcion,
    time: step.timestamp ? new Date(step.timestamp).toLocaleString("es-PY") : undefined,
    status: step.estado === "completado" ? "completed" : step.estado === "actual" ? "current" : step.estado === "cancelado" ? "cancelled" : "pending",
    stopIndex: Math.min(index, Math.max(stops.length - 1, 0)),
  })), [data, stops.length]);

  if (loadError && !data) return <div className="status-card error-message" role="alert"><p>{loadError}</p><button type="button" onClick={() => void load()}>Reintentar</button></div>;
  if (!data) return <div className="roadmap-card" aria-busy="true" aria-label="Cargando hoja de ruta"><div className="skeleton-line"/><div className="skeleton-line"/><div className="skeleton-line"/></div>;

  const action = data.proxima_accion;
  const stage = visibleStatus(data);
  const scenario: ScenarioDefinition = {
    id: data.reserva.rol_actual === "conductor" ? "pasajeros_pendientes" : "reserva_confirmada",
    role: data.reserva.rol_actual,
    label: stage,
    tripState: stage.toLowerCase().replaceAll(" ", "_"),
    passengerState: stage,
    heroTitle: stage,
    heroNext: action.enabled ? action.label : "No hay acciones pendientes",
    primaryAction: action.label,
    distance: "",
    minutes: "",
    currentStep: Math.max(timeline.findIndex((step) => step.status === "current"), 0),
    currentStop: Math.max(stops.findIndex((stop) => stop.status === "current"), 0),
    onboard: 0,
    pending: 0,
  };
  const runAction = async () => {
    if (busy || !action.enabled) return;
    if (action.id === "chat") { document.querySelector("#chat-reserva")?.scrollIntoView({ behavior: "smooth" }); return; }
    if (action.confirmation_required && !window.confirm(`¿Confirmas: ${action.label}?`)) return;
    setBusy(true); setActionError(""); setNotice("");
    try { setData(await api.roadmapAction(data, token)); setNotice("Listo. La hoja de ruta fue actualizada."); }
    catch (caught) { setActionError(caught instanceof ApiError ? caught.message : "No se pudo completar la acción."); }
    finally { setBusy(false); }
  };
  const vehicle = data.vehiculo ? `${data.vehiculo.marca} ${data.vehiculo.modelo} · ${data.vehiculo.color}` : "Vehículo todavía no asignado";

  return <div className="roadmap-shell roadmap-real roadmap-simple">
    <header className="roadmap-trip-header"><div><p className="roadmap-kicker">Reserva #{data.reserva.id}</p><h1>{data.viaje.origen} → {data.viaje.destino}</h1><p>{new Date(data.viaje.fecha_salida).toLocaleString("es-PY")} · {vehicle}</p></div><span className="roadmap-role-badge">{stage}</span></header>
    {actionError && <p className="error-message" role="alert">{actionError}</p>}{notice && <p className="success-message" role="status">{notice}</p>}
    <div className="roadmap-layout"><main className="roadmap-main-column">
      <section className="roadmap-hero" aria-labelledby="simple-trip-status"><div><p className="roadmap-kicker">Estado actual</p><h2 id="simple-trip-status">{stage}</h2><p className="roadmap-next"><span>Qué sucede ahora</span>{action.enabled ? action.label : "No hay acciones pendientes"}</p></div></section>
      {action.enabled && <TripPrimaryAction scenario={scenario} onAction={() => void runAction()} disabled={busy}/>}
      <section className="roadmap-mini-card" id="meeting-point"><div><p className="roadmap-kicker">Punto de encuentro</p><h3>{data.punto_encuentro.nombre_publico ?? "Todavía no acordado"}</h3><p>{data.punto_encuentro.zona_general ?? "Pueden coordinarlo desde el chat."}</p></div><a className="button-secondary" href="#chat-reserva">Abrir chat</a></section>
      {stops.length > 0 ? <TripMapPreview stops={stops} location="sin_ubicacion" selectedStop={Math.min(selected, stops.length - 1)} onSelect={setSelected} title={`${data.viaje.origen} → ${data.viaje.destino}`}/> : <div className="roadmap-card">El recorrido todavía no está disponible.</div>}
      <nav className="roadmap-quick-actions" aria-label="Acciones de la reserva"><a href="#chat-reserva"><span aria-hidden="true">💬</span>Abrir chat</a><a href="#meeting-point"><span aria-hidden="true">↗</span>Abrir indicaciones</a></nav>
    </main><aside className="roadmap-side-column"><TripTimeline steps={timeline} selectedStop={selected} onSelect={setSelected}/></aside></div>
  </div>;
}
