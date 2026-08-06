"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { RelatedReservation, Roadmap, Trip, Vehicle } from "@/lib/types";
import { TripMapPreview } from "./TripMapPreview";
import { TripTimeline } from "./TripTimeline";
import type { RoadmapStop, TimelineStep } from "./types";

const visibleSteps = ["Reserva confirmada", "Punto de encuentro", "Conductor en camino", "Viaje en curso", "Viaje finalizado"];

function visibleStatus(data: Roadmap): string {
  if (data.reserva.estado === "cancelada" || data.viaje.estado === "cancelado") return "Viaje cancelado";
  if (data.viaje.estado === "finalizado") return "Viaje finalizado";
  if (["en_curso", "pausado"].includes(data.viaje.estado)) return "Viaje en curso";
  if (["conductor_en_camino", "conductor_en_punto", "abordaje"].includes(data.viaje.estado)) return "Conductor en camino";
  if (data.punto_encuentro.estado === "confirmado") return "Punto de encuentro acordado";
  return "Reserva confirmada";
}

function stageIndex(data: Roadmap): number {
  if (data.viaje.estado === "finalizado") return 4;
  if (["en_curso", "pausado"].includes(data.viaje.estado)) return 3;
  if (["conductor_en_camino", "conductor_en_punto", "abordaje"].includes(data.viaje.estado)) return 2;
  return data.punto_encuentro.estado === "confirmado" ? 1 : 0;
}

function statusDescription(data: Roadmap, status: string): string {
  if (status === "Viaje cancelado") return "La reserva se conserva en tu historial y el chat sigue disponible para consulta.";
  if (status === "Viaje finalizado") return "El trayecto compartido terminó. Gracias por viajar juntos.";
  if (status === "Viaje en curso") return data.viaje.estado === "pausado" ? "El viaje está en pausa temporalmente." : "El viaje ya comenzó y avanza hacia el destino.";
  if (status === "Conductor en camino") return data.viaje.estado === "conductor_en_punto" ? "El conductor llegó al punto acordado." : "El conductor se dirige al punto de encuentro.";
  if (status === "Punto de encuentro acordado") return "El lugar para encontrarse quedó confirmado por ambos.";
  return "Tu lugar está confirmado. Revisá el punto de encuentro antes de salir.";
}

type ReservationContext = { reservationState: string; tripState: string };
type BasicReservation = { reservation: RelatedReservation; trip: Trip | null; vehicle: Vehicle | null };

function basicReservationStatus(state: RelatedReservation["estado"]): { title: string; description: string; tone: string } {
  if (state === "rechazada") return { title: "Solicitud rechazada", description: "El conductor no pudo confirmar tu solicitud para este viaje.", tone: "is-danger" };
  if (state === "cancelada") return { title: "Solicitud cancelada", description: "Esta solicitud fue cancelada y permanece disponible en tu historial.", tone: "is-muted" };
  return { title: "Esperando confirmación", description: "El conductor todavía debe confirmar tu solicitud.", tone: "is-current" };
}

function BasicReservationDetail({ data, token, onCancelled }: { data: BasicReservation; token: string; onCancelled: (reservation: RelatedReservation) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { reservation, trip, vehicle } = data;
  const status = basicReservationStatus(reservation.estado);
  const departure = new Date(reservation.fecha);
  const canCancel = reservation.rol === "pasajero" && reservation.estado === "pendiente";
  const cancel = async () => {
    if (busy || !canCancel || !window.confirm("¿Querés cancelar esta solicitud?")) return;
    setBusy(true); setError("");
    try {
      await api.cancelRequest(reservation.reserva_id, token);
      onCancelled({ ...reservation, estado: "cancelada" });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "No pudimos cancelar la solicitud.");
    } finally { setBusy(false); }
  };
  return <article className="pending-reservation-detail">
    <header className="pending-reservation-heading"><div><p className="ui-eyebrow">Reserva #{reservation.reserva_id}</p><h1>{reservation.origen} <span aria-hidden>→</span> {reservation.destino}</h1><p>{departure.toLocaleString("es-PY", { dateStyle: "long", timeStyle: "short" })}</p></div><span className={`status-badge ${status.tone}`}>{reservation.estado}</span></header>
    <section className="pending-reservation-status" aria-labelledby="pending-status-title"><div><p className="ui-eyebrow">Estado actual</p><h2 id="pending-status-title">{status.title}</h2><p>{status.description}</p></div><div className="participant-summary"><span className="participant-avatar" aria-hidden>{reservation.participante.split(" ").slice(0, 2).map((part) => part[0]).join("").toUpperCase()}</span><div><small>{reservation.rol === "pasajero" ? "Conductor" : "Pasajero"}</small><b>{reservation.participante}</b></div></div></section>
    <section className="pending-reservation-summary" aria-labelledby="pending-summary-title"><div className="section-intro"><div><p className="ui-eyebrow">Detalle</p><h2 id="pending-summary-title">Información de la solicitud</h2></div></div><dl><div><dt>Origen</dt><dd>{reservation.origen}</dd></div><div><dt>Destino</dt><dd>{reservation.destino}</dd></div><div><dt>Fecha</dt><dd>{departure.toLocaleDateString("es-PY", { dateStyle: "medium" })}</dd></div><div><dt>Hora</dt><dd>{departure.toLocaleTimeString("es-PY", { hour: "2-digit", minute: "2-digit" })}</dd></div><div><dt>Estado</dt><dd>{status.title}</dd></div>{trip && <div><dt>Ocupación</dt><dd>{Math.max(trip.cupos_totales - trip.cupos_disponibles, 0)} de {trip.cupos_totales}</dd></div>}{vehicle && <div><dt>Vehículo</dt><dd>{vehicle.marca} {vehicle.modelo} · {vehicle.color}</dd></div>}</dl></section>
    {error && <p className="error-message" role="alert">{error}</p>}
    <footer className="pending-reservation-actions"><Link className="button-secondary" href="/reservas">Volver a reservas</Link>{canCancel && <button className="button-danger" type="button" disabled={busy} onClick={() => void cancel()}>{busy ? "Cancelando…" : "Cancelar solicitud"}</button>}</footer>
  </article>;
}

export function RealTripRoadmap({ reservationId, token, meetingPoint, chat }: { reservationId: number; token: string; meetingPoint: (context: ReservationContext) => ReactNode; chat: (context: ReservationContext) => ReactNode }) {
  const [data, setData] = useState<Roadmap | null>(null);
  const [basicData, setBasicData] = useState<BasicReservation | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loadErrorStatus, setLoadErrorStatus] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(0);
  const socketRef = useRef<WebSocket | null>(null);

  const load = useCallback(async () => {
    try { setData(await api.roadmap(reservationId, token)); setBasicData(null); setLoadError(""); setLoadErrorStatus(null); }
    catch (caught) {
      if (caught instanceof ApiError && caught.status === 409) {
        try {
          const reservations = await api.relatedReservations(token);
          const reservation = reservations.find((item) => item.reserva_id === reservationId);
          if (!reservation) { setLoadError("No encontramos esta reserva o no tenés acceso."); setLoadErrorStatus(404); return; }
          const tripsResult = await Promise.allSettled([api.availableTrips(token), api.myTrips(token)]);
          const trips = tripsResult.flatMap((result) => result.status === "fulfilled" ? result.value : []);
          const trip = trips.find((item) => item.id === reservation.viaje_id) ?? null;
          let vehicle: Vehicle | null = null;
          if (trip?.vehiculo_id) {
            const vehicles = await api.vehicles(token).catch(() => []);
            vehicle = vehicles.find((item) => item.id === trip.vehiculo_id) ?? null;
          }
          setBasicData({ reservation, trip, vehicle }); setLoadError(""); setLoadErrorStatus(null);
        } catch (fallbackError) {
          setLoadError(fallbackError instanceof ApiError ? fallbackError.message : "No pudimos cargar la reserva.");
          setLoadErrorStatus(fallbackError instanceof ApiError ? fallbackError.status : 0);
        }
      } else if (caught instanceof ApiError && caught.status === 401) { setLoadError("Tu sesión venció. Iniciá sesión nuevamente."); setLoadErrorStatus(401); }
      else if (caught instanceof ApiError && caught.status === 404) { setLoadError("No encontramos esta reserva o no tenés acceso."); setLoadErrorStatus(404); }
      else { setLoadError(caught instanceof ApiError ? caught.message : "No pudimos cargar la reserva."); setLoadErrorStatus(caught instanceof ApiError ? caught.status : 0); }
    }
  }, [reservationId, token]);

  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer); }, [load]);
  useEffect(() => {
    if (basicData) return;
    let stopped = false; let retry: number | undefined;
    const connect = async () => {
      try {
        const url = await api.roadmapWebSocketUrl(reservationId, token);
        if (stopped || socketRef.current) return;
        const socket = new WebSocket(url); socketRef.current = socket;
        socket.onmessage = (message) => { const event = JSON.parse(message.data) as { type: string }; if (!["connected", "pong"].includes(event.type)) void load(); };
        socket.onclose = () => { socketRef.current = null; if (!stopped) retry = window.setTimeout(connect, 2000); };
      } catch { if (!stopped) retry = window.setTimeout(connect, 3000); }
    };
    void connect();
    return () => { stopped = true; if (retry) window.clearTimeout(retry); socketRef.current?.close(); socketRef.current = null; };
  }, [basicData, load, reservationId, token]);

  const stops = useMemo<RoadmapStop[]>(() => (data?.paradas ?? []).map((stop) => ({
    time: stop.hora_estimada ? new Date(stop.hora_estimada).toLocaleTimeString("es-PY", { hour: "2-digit", minute: "2-digit" }) : "",
    title: stop.nombre_publico, passenger: stop.tipo, detail: stop.zona_general ?? "Zona todavía no definida", occupancy: "",
    status: stop.estado === "completada" ? "completed" : stop.estado === "actual" ? "current" : stop.estado === "cancelada" ? "cancelled" : "pending",
  })), [data]);

  const timeline = useMemo<TimelineStep[]>(() => visibleSteps.slice(0, 5).map((title, index) => {
    const source = data?.hoja_ruta[index];
    const cancelled = data?.reserva.estado === "cancelada" || data?.viaje.estado === "cancelado";
    const currentStage = data ? stageIndex(data) : 0;
    let detail = source?.descripcion ?? "Pendiente";
    if (index === 1 && data && ["listo", "llego_al_punto"].includes(data.estado_pasajero.estado)) detail = data.estado_pasajero.estado === "listo" ? "Confirmaste que estás listo." : "Ya llegaste al punto acordado.";
    if (index === 2 && data?.viaje.estado === "conductor_en_punto") detail = "El conductor llegó al punto acordado.";
    if (index === 3 && data?.viaje.estado === "pausado") detail = "El viaje está pausado temporalmente.";
    const status = cancelled
      ? source?.estado === "completado" ? "completed" : source?.estado === "cancelado" ? "cancelled" : "pending"
      : index < currentStage ? "completed" : index === currentStage ? "current" : "pending";
    if (status === "completed" && (!source?.timestamp || /pendiente|todav[ií]a|falta/i.test(detail))) detail = "Etapa completada";
    return { title, detail, time: source?.timestamp ? new Date(source.timestamp).toLocaleString("es-PY") : undefined, status, stopIndex: Math.min(index, Math.max(stops.length - 1, 0)) };
  }), [data, stops.length]);

  if (basicData && !data) return <BasicReservationDetail data={basicData} token={token} onCancelled={(reservation) => setBasicData((current) => current ? { ...current, reservation } : current)}/>;
  if (loadError && !data) return <section className="ui-state ui-state-error" role="alert"><b>No pudimos abrir esta reserva</b><p>{loadError}</p>{loadErrorStatus === 0 && <button className="button-secondary" type="button" onClick={() => void load()}>Reintentar</button>}<Link className="text-link" href="/reservas">Volver a reservas</Link></section>;
  if (!data) return <section className="reservation-skeleton" aria-busy="true" aria-label="Cargando reserva"><div/><div/><div/></section>;

  const action = data.proxima_accion;
  const actionLabel = action.id === "chat" ? "Abrir chat" : action.label;
  const stage = visibleStatus(data);
  const participant = data.reserva.rol_actual === "conductor" ? data.pasajero_actual : data.conductor;
  const initials = participant.nombre.split(" ").slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  const departure = new Date(data.viaje.fecha_salida);
  const context = { reservationState: data.reserva.estado, tripState: data.viaje.estado };
  const runAction = async () => {
    if (busy || !action.enabled) return;
    if (action.id === "chat") { window.dispatchEvent(new Event("jahamina:open-chat")); return; }
    if (action.confirmation_required && !window.confirm(`¿Confirmás: ${action.label}?`)) return;
    setBusy(true); setActionError(""); setNotice("");
    try { setData(await api.roadmapAction(data, token)); setNotice("Listo, el viaje fue actualizado."); }
    catch (caught) { setActionError(caught instanceof ApiError ? caught.message : "No pudimos completar la acción."); }
    finally { setBusy(false); }
  };

  return <article className="reservation-dashboard">
    <header className="reservation-heading"><div><p className="ui-eyebrow">Reserva #{data.reserva.id}</p><h1><span>{data.viaje.origen}</span><i aria-hidden>→</i><span>{data.viaje.destino}</span></h1><p>{departure.toLocaleString("es-PY", { dateStyle: "long", timeStyle: "short" })}</p></div><span className={`status-badge ${stage === "Viaje cancelado" ? "is-danger" : stage === "Viaje finalizado" ? "is-success" : "is-current"}`}>{stage}</span></header>
    {actionError && <p className="error-message dashboard-message" role="alert">{actionError}</p>}{notice && <p className="success-message dashboard-message" role="status">{notice}</p>}

    <section className="status-surface" aria-labelledby="reservation-status">
      <div className="status-copy"><p className="ui-eyebrow">Estado actual</p><h2 id="reservation-status">{stage}</h2><p>{statusDescription(data, stage)}</p></div>
      <div className="status-people"><div className="participant-summary"><span className="participant-avatar" aria-hidden>{initials}</span><div><small>{data.reserva.rol_actual === "conductor" ? "Pasajero" : "Conductor"}</small><b>{participant.nombre}</b></div></div>{data.vehiculo && <div className="vehicle-summary"><span className="vehicle-glyph" aria-hidden><i/><i/></span><div><small>Vehículo</small><b>{data.vehiculo.marca} {data.vehiculo.modelo}</b><span>{data.vehiculo.color}{data.vehiculo.matricula ? ` · ${data.vehiculo.matricula}` : ""}</span></div></div>}</div>
      <dl className="trip-facts"><div><dt>Ocupación</dt><dd>{data.ocupacion.ocupados} de {data.ocupacion.totales} lugares</dd></div><div><dt>Participás como</dt><dd>{data.reserva.rol_actual}</dd></div></dl>
      {action.enabled && !["finalizado", "cancelado"].includes(data.viaje.estado) && <div className="context-action"><div><small>Próxima acción</small><b>{actionLabel}</b></div><button className="button-primary" type="button" disabled={busy} onClick={() => void runAction()}>{busy ? "Actualizando…" : actionLabel}</button></div>}
    </section>

    <div className="timeline-area"><TripTimeline steps={timeline} selectedStop={selected} onSelect={setSelected}/></div>
    <section className="route-area" aria-label="Tu ruta">{stops.length > 0 ? <TripMapPreview stops={stops} location="sin_ubicacion" selectedStop={Math.min(selected, stops.length - 1)} onSelect={setSelected} title={`${data.viaje.origen} → ${data.viaje.destino}`} origin={data.viaje.origen} destination={data.viaje.destino}/> : <div className="surface-card route-empty"><p className="ui-eyebrow">Tu ruta</p><h2>{data.viaje.origen} → {data.viaje.destino}</h2><div className="schematic-route" aria-label={`Recorrido desde ${data.viaje.origen} hasta ${data.viaje.destino}`}><span/><div><b>{data.viaje.origen}</b><i/><b>{data.viaje.destino}</b></div><span/></div><p>El recorrido detallado todavía no está disponible.</p></div>}</section>
    <section className="meeting-area" id="meeting-point">{meetingPoint(context)}</section>
    <section className="chat-area" id="chat-reserva"><div className="section-intro"><div><p className="ui-eyebrow">Conversación</p><h2>Chat del viaje</h2></div>{data.permisos.puede_ver_chat && <a href="#chat-reserva" className="text-link">Ver conversación</a>}</div>{chat(context)}</section>
    <section className="trip-info-area" aria-labelledby="trip-info-title"><div className="section-intro"><div><p className="ui-eyebrow">Resumen</p><h2 id="trip-info-title">Información del viaje</h2></div></div><dl><div><dt>Fecha</dt><dd>{departure.toLocaleDateString("es-PY", { dateStyle: "medium" })}</dd></div><div><dt>Hora</dt><dd>{departure.toLocaleTimeString("es-PY", { hour: "2-digit", minute: "2-digit" })}</dd></div><div><dt>Estado</dt><dd>{stage}</dd></div><div><dt>Ocupación</dt><dd>{data.ocupacion.ocupados} de {data.ocupacion.totales}</dd></div><div><dt>Rol</dt><dd>{data.reserva.rol_actual}</dd></div>{data.vehiculo && <div><dt>Vehículo</dt><dd>{data.vehiculo.marca} {data.vehiculo.modelo}</dd></div>}<div><dt>Origen</dt><dd>{data.viaje.origen}</dd></div><div><dt>Destino</dt><dd>{data.viaje.destino}</dd></div></dl></section>
  </article>;
}
