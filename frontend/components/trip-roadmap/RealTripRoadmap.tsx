"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { Roadmap } from "@/lib/types";
import { TripMapPreview } from "./TripMapPreview";
import { TripNextStopCard } from "./TripNextStopCard";
import { TripPassengerProgress } from "./TripPassengerProgress";
import { TripQuickActions } from "./TripQuickActions";
import { TripStatusHero } from "./TripStatusHero";
import { TripStopList } from "./TripStopList";
import { TripTimeline } from "./TripTimeline";
import type { RoadmapStop, ScenarioDefinition, TimelineStep } from "./types";

function statusTitle(data: Roadmap): string {
  if (data.reserva.estado === "cancelada" || data.viaje.estado === "cancelado") return "Esta reserva fue cancelada";
  if (data.viaje.estado === "finalizado") return "El viaje finalizó";
  return data.reserva.rol_actual === "conductor" ? `Próxima recogida: ${data.pasajero_actual.nombre}` : `Tu reserva con ${data.conductor.nombre}`;
}

export function RealTripRoadmap({ reservationId, token }: { reservationId: number; token: string }) {
  const [data, setData] = useState<Roadmap | null>(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(0);
  const load = useCallback(async () => {
    try { setData(await api.roadmap(reservationId, token)); setError(""); }
    catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) setError("Tu sesión venció. Inicia sesión nuevamente.");
      else if (caught instanceof ApiError && caught.status === 404) setError("No encontramos esta reserva o no tienes acceso.");
      else setError(caught instanceof ApiError ? caught.message : "No se pudo cargar la hoja de ruta.");
    }
  }, [reservationId, token]);
  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer); }, [load]);

  const stops = useMemo<RoadmapStop[]>(() => (data?.paradas ?? []).map((stop) => ({
    time: stop.hora_estimada ? new Date(stop.hora_estimada).toLocaleTimeString("es-PY", {hour:"2-digit", minute:"2-digit"}) : "Sin hora estimada",
    title: stop.nombre_publico,
    passenger: stop.tipo === "recogida" ? data?.pasajero_actual.nombre ?? "Pasajero" : stop.tipo,
    detail: stop.zona_general ?? "Zona todavía no definida",
    occupancy: `${data?.ocupacion.ocupados ?? 0} de ${data?.ocupacion.totales ?? 0} ocupados`,
    status: stop.estado === "completada" ? "completed" : stop.estado === "actual" ? "current" : stop.estado === "cancelada" ? "cancelled" : "pending",
  })), [data]);
  const timeline = useMemo<TimelineStep[]>(() => (data?.hoja_ruta ?? []).map((step, index) => ({
    title:step.titulo, detail:step.descripcion,
    time:step.timestamp ? new Date(step.timestamp).toLocaleString("es-PY") : undefined,
    status:step.estado === "completado" ? "completed" : step.estado === "actual" ? "current" : step.estado === "cancelado" ? "cancelled" : "pending",
    stopIndex:Math.min(index, Math.max(stops.length - 1, 0)),
  })), [data, stops.length]);

  if (error) return <div className="status-card error-message" role="alert"><p>{error}</p><button type="button" onClick={() => void load()}>Reintentar</button></div>;
  if (!data) return <div className="roadmap-card" aria-busy="true" aria-label="Cargando hoja de ruta"><div className="skeleton-line"/><div className="skeleton-line"/><div className="skeleton-line"/></div>;
  const currentStopIndex = stops.findIndex((stop) => stop.status === "current");
  const currentStop = currentStopIndex >= 0 ? currentStopIndex : 0;
  const scenario: ScenarioDefinition = {
    id:data.reserva.rol_actual === "conductor" ? "pasajeros_pendientes" : "reserva_confirmada", role:data.reserva.rol_actual,
    label:data.viaje.estado, tripState:data.viaje.estado, passengerState:data.reserva.estado,
    heroTitle:statusTitle(data), heroNext:data.punto_encuentro.zona_general ?? "Punto de encuentro todavía no definido",
    primaryAction:"Abrir chat", distance:"Recorrido esquemático", minutes:"Sin ETA disponible",
    currentStep:Math.max(timeline.findIndex((step) => step.status === "current"), 0), currentStop,
    onboard:0, pending:data.ocupacion.pendientes,
  };
  return <div className="roadmap-shell roadmap-real">
    <header className="roadmap-trip-header"><div><p className="roadmap-kicker">Reserva #{data.reserva.id} · como {data.reserva.rol_actual}</p><h1>{data.viaje.origen} → {data.viaje.destino}</h1><p>{new Date(data.viaje.fecha_salida).toLocaleString("es-PY")}</p></div><span className="roadmap-role-badge">{data.viaje.estado.replaceAll("_", " ")}</span></header>
    <div className="roadmap-layout"><main className="roadmap-main-column">
      <TripStatusHero scenario={scenario} location="sin_ubicacion" vehicle={data.vehiculo ? `${data.vehiculo.marca} ${data.vehiculo.modelo} · ${data.vehiculo.color}` : "Viaje sin vehículo asignado"}/>
      <section className="roadmap-mini-card"><div><p className="roadmap-kicker">{data.reserva.rol_actual === "pasajero" ? "Tu punto de encuentro" : "Punto de recogida"}</p><h3>{data.punto_encuentro.nombre_publico ?? "Todavía no definido"}</h3><p>{data.punto_encuentro.zona_general ?? "Podrán coordinarlo desde esta reserva."} · {data.punto_encuentro.estado.replaceAll("_", " ")}</p></div></section>
      {stops.length ? <><TripMapPreview stops={stops} location="sin_ubicacion" selectedStop={Math.min(selected, stops.length - 1)} onSelect={setSelected}/><TripNextStopCard stop={stops[currentStop]} index={currentStop} total={stops.length} occupied={data.ocupacion.ocupados}/></> : <div className="roadmap-card">El recorrido todavía no está disponible.</div>}
      <TripQuickActions showShare={false}/>
    </main><aside className="roadmap-side-column"><TripTimeline steps={timeline} selectedStop={selected} onSelect={setSelected}/>{stops.length > 0 && <TripStopList stops={stops} selected={selected} onSelect={setSelected}/>}<TripPassengerProgress occupied={data.ocupacion.ocupados} pending={data.ocupacion.pendientes} total={data.ocupacion.totales}/><section className="roadmap-mini-card"><div><p className="roadmap-kicker">Conductor</p><h3>{data.conductor.nombre}</h3><p>{data.vehiculo ? `${data.vehiculo.marca} ${data.vehiculo.modelo} · ${data.vehiculo.color} · ${data.vehiculo.matricula}` : "Vehículo todavía no asignado"}</p></div></section></aside></div>
  </div>;
}
