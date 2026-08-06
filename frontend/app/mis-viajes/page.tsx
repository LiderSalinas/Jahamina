"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { TripCard } from "@/components/TripCard";
import { AsyncState, PageHeader } from "@/components/ui/AppUI";
import { PageContainer } from "@/components/ui/PageContainer";
import { api, ApiError } from "@/lib/api";
import type { Trip, TripRequest } from "@/lib/types";

export default function MyTripsPage() {
  const { token, logout } = useAuth();
  const [created, setCreated] = useState<Trip[]>([]);
  const [joined, setJoined] = useState<Trip[]>([]);
  const [requests, setRequests] = useState<TripRequest[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const [ownTrips, joinedTrips] = await Promise.all([api.myTrips(token), api.joinedTrips(token)]);
      setCreated(ownTrips); setJoined(joinedTrips);
      setRequests((await Promise.all(ownTrips.map((trip) => api.tripRequests(trip.id, token)))).flat());
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) logout();
      else setError(caught instanceof ApiError ? caught.message : "No pudimos cargar tus viajes.");
    } finally { setLoading(false); }
  }, [logout, token]);

  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer); }, [load]);

  async function cancel(id: number) {
    if (!token || !window.confirm("¿Confirmás la cancelación de este viaje?")) return;
    setBusyId(id);
    try { const updated = await api.cancelTrip(id, token); setCreated((items) => items.map((item) => item.id === id ? updated : item)); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "No pudimos cancelar el viaje."); }
    finally { setBusyId(null); }
  }

  async function respond(requestId: number, accept: boolean) {
    if (!token || !window.confirm(`¿Confirmás que querés ${accept ? "aceptar" : "rechazar"} esta solicitud?`)) return;
    setBusyId(requestId); setError("");
    try {
      const updated = accept ? await api.acceptRequest(requestId, token) : await api.rejectRequest(requestId, token);
      setRequests((items) => items.map((item) => item.id === requestId ? updated : item)); await load();
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : "No pudimos responder la solicitud."); }
    finally { setBusyId(null); }
  }

  const groups = useMemo(() => {
    const all = [...created, ...joined.filter((item) => !created.some((own) => own.id === item.id))];
    return [
      { title: "Próximos", items: all.filter((item) => !item.cancelado && ["publicado", "completo"].includes(item.estado) && new Date(item.fecha) > new Date()) },
      { title: "Activos", items: all.filter((item) => !item.cancelado && item.estado === "en_curso") },
      { title: "Finalizados", items: all.filter((item) => item.estado === "finalizado") },
      { title: "Cancelados", items: all.filter((item) => item.cancelado || item.estado === "cancelado") },
    ];
  }, [created, joined]);

  return <ProtectedRoute><PageContainer className="page-stack">
    <PageHeader eyebrow="Tu actividad" title="Mis viajes" description="Organizá tus próximos trayectos y consultá tu historial."/>
    {error && <p className="error-message" role="alert">{error}</p>}
    {loading ? <AsyncState kind="loading" title="Cargando tus viajes…"/> : <>
      {requests.some(item => item.estado === "pendiente") && <section><div className="section-heading"><h2 className="section-title">Solicitudes recibidas</h2><span className="badge-pending">Pendientes</span></div><div className="request-list">{requests.filter(item => item.estado === "pendiente").map(request => <article className="request-row" key={request.id}><div><p className="eyebrow">Viaje #{request.viaje_id}</p><h3>Nueva solicitud</h3><p>{request.mensaje_inicial || "Sin mensaje inicial"}</p></div><div className="request-actions"><button className="button-primary" disabled={busyId === request.id} onClick={() => respond(request.id, true)} type="button">Aceptar</button><button className="button-secondary" disabled={busyId === request.id} onClick={() => respond(request.id, false)} type="button">Rechazar</button></div></article>)}</div></section>}
      <div className="trip-groups">{groups.map(group => <section key={group.title}><div className="section-heading"><h2 className="section-title">{group.title}</h2><span>{group.items.length}</span></div>{group.items.length ? <div className="my-trips-grid">{group.items.map(trip => <TripCard actionLabel={created.some(item => item.id === trip.id) && !trip.cancelado && trip.estado !== "finalizado" ? "Cancelar viaje" : undefined} busy={busyId === trip.id} key={trip.id} onAction={created.some(item => item.id === trip.id) ? () => cancel(trip.id) : undefined} trip={trip}/>)}</div> : <p className="compact-empty">No hay viajes en esta sección.</p>}</section>)}</div>
    </>}
  </PageContainer></ProtectedRoute>;
}
