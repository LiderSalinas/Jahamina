"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { Roadmap } from "@/lib/types";
import { TripMapPreview } from "./TripMapPreview";
import { TripNextStopCard } from "./TripNextStopCard";
import { TripPassengerProgress } from "./TripPassengerProgress";
import { TripPrimaryAction } from "./TripPrimaryAction";
import { TripQuickActions } from "./TripQuickActions";
import { TripStatusHero } from "./TripStatusHero";
import { TripStopList } from "./TripStopList";
import { TripTimeline } from "./TripTimeline";
import type { RoadmapStop, ScenarioDefinition, TimelineStep } from "./types";

export function RealTripRoadmap({ reservationId, token }: { reservationId: number; token: string }) {
  const [data, setData] = useState<Roadmap | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(0);
  const socketRef = useRef<WebSocket | null>(null);

  const load = useCallback(async () => {
    try { setData(await api.roadmap(reservationId, token)); setError(""); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "No se pudo cargar la hoja de ruta."); }
  }, [reservationId, token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  useEffect(() => {
    let stopped = false; let retry: number | undefined;
    const connect = async () => {
      try {
        const url = await api.roadmapWebSocketUrl(reservationId, token);
        if (stopped || socketRef.current) return;
        const socket = new WebSocket(url); socketRef.current = socket;
        socket.onmessage = (event) => { const payload = JSON.parse(event.data) as {type:string}; if (payload.type !== "connected" && payload.type !== "pong") void load(); };
        socket.onclose = () => { socketRef.current = null; if (!stopped) retry = window.setTimeout(connect, 2000); };
      } catch { if (!stopped) retry = window.setTimeout(connect, 3000); }
    };
    void connect();
    return () => { stopped = true; if (retry) window.clearTimeout(retry); socketRef.current?.close(); socketRef.current = null; };
  }, [load, reservationId, token]);

  const stops = useMemo<RoadmapStop[]>(() => (data?.paradas ?? []).map((stop) => ({
    time: stop.hora_estimada ? new Date(stop.hora_estimada).toLocaleTimeString("es-PY", {hour:"2-digit", minute:"2-digit"}) : "Por coordinar",
    title: stop.nombre_publico, passenger: stop.tipo === "recogida" ? data?.pasajero.nombre ?? "Pasajero" : stop.tipo,
    detail: stop.zona_general ?? "Zona general", occupancy: `${data?.viaje.cupos_ocupados ?? 0} ocupados`,
    status: stop.estado === "completada" ? "completed" : stop.estado === "actual" ? "current" : stop.estado === "cancelada" ? "cancelled" : "pending",
  })), [data]);
  const timeline = useMemo<TimelineStep[]>(() => data?.eventos.length ? data.eventos.map((event, index) => ({title:event.descripcion_publica, detail:event.tipo.replaceAll("_", " "), time:new Date(event.created_at).toLocaleString("es-PY"), status:index === data.eventos.length-1 ? "current" : "completed", stopIndex:Math.min(index, Math.max(stops.length-1, 0))})) : [{title:"Reserva confirmada", detail:"La coordinación está activa", status:"current", stopIndex:0}], [data, stops.length]);
  if (error) return <div className="status-card error-message" role="alert">{error}<button type="button" onClick={() => void load()}>Reintentar</button></div>;
  if (!data) return <div className="status-card" aria-busy="true">Cargando hoja de ruta…</div>;

  const currentStop = Math.max(0, stops.findIndex((stop) => stop.status === "current"));
  const action = data.proxima_accion;
  const scenario: ScenarioDefinition = {
    id: data.reserva.rol_actual === "conductor" ? "preparando_salida" : "reserva_confirmada", role:data.reserva.rol_actual,
    label:data.viaje.estado, tripState:data.viaje.estado, passengerState:data.estado_pasajero.estado,
    heroTitle:data.viaje.estado.replaceAll("_", " "), heroNext:stops[currentStop]?.title ?? data.viaje.destino,
    primaryAction:action.label, distance:"Recorrido coordinado", minutes:"sin GPS en vivo", currentStep:Math.max(timeline.length-1,0), currentStop,
    onboard:data.estado_pasajero.estado === "abordo" ? data.viaje.cupos_ocupados : 0, pending:Math.max(data.viaje.cupos_ocupados-(data.estado_pasajero.estado === "abordo" ? 1 : 0),0),
  };
  const runAction = async () => {
    if (!action.enabled || action.action === "none" || action.action === "chat") return;
    if (action.confirmation_required && !window.confirm(`¿Confirmas: ${action.label}?`)) return;
    setBusy(true); setError("");
    try { setData(await api.roadmapAction(data, token)); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "No se pudo completar la acción."); }
    finally { setBusy(false); }
  };
  return <div className="roadmap-shell roadmap-real">
    <header className="roadmap-trip-header"><div><p className="roadmap-kicker">Reserva #{data.reserva.id} · {data.reserva.rol_actual}</p><h1>{data.viaje.origen} → {data.viaje.destino}</h1><p>{new Date(data.viaje.fecha_salida).toLocaleString("es-PY")}</p></div><span className="roadmap-role-badge">{data.viaje.estado.replaceAll("_", " ")}</span></header>
    {error && <p className="error-message" role="alert">{error}</p>}
    <div className="roadmap-layout"><main className="roadmap-main-column">
      <TripStatusHero scenario={scenario} location="sin_ubicacion" vehicle={data.vehiculo ? `${data.vehiculo.marca} ${data.vehiculo.modelo} · ${data.vehiculo.color}` : "Vehículo por confirmar"}/>
      <TripPrimaryAction scenario={scenario} onAction={() => void runAction()} disabled={busy || !action.enabled}/>
      {stops.length > 0 && <><TripMapPreview stops={stops} location="sin_ubicacion" selectedStop={Math.min(selected, stops.length-1)} onSelect={setSelected}/><TripNextStopCard stop={stops[currentStop]} index={currentStop} scenario={scenario}/></>}
      <TripQuickActions />
    </main><aside className="roadmap-side-column"><TripTimeline steps={timeline} selectedStop={selected} onSelect={setSelected}/>{stops.length > 0 && <TripStopList stops={stops} selected={selected} onSelect={setSelected}/>}<TripPassengerProgress scenario={scenario}/></aside></div>
  </div>;
}
