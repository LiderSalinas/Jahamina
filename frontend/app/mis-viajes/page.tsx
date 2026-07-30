"use client";

import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { TripCard } from "@/components/TripCard";
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
      const [ownTrips, joinedTrips] = await Promise.all([
        api.myTrips(token),
        api.joinedTrips(token),
      ]);
      setCreated(ownTrips);
      setJoined(joinedTrips);
      const requestGroups = await Promise.all(
        ownTrips.map((trip) => api.tripRequests(trip.id, token)),
      );
      setRequests(requestGroups.flat());
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) logout();
      else setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    } finally {
      setLoading(false);
    }
  }, [logout, token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function cancel(id: number) {
    if (!token || !window.confirm("¿Confirmás la cancelación de este viaje?")) return;
    setBusyId(id);
    try {
      const updated = await api.cancelTrip(id, token);
      setCreated((trips) => trips.map((trip) => trip.id === id ? updated : trip));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    } finally {
      setBusyId(null);
    }
  }

  async function respond(requestId: number, accept: boolean) {
    if (!token) return;
    const label = accept ? "aceptar" : "rechazar";
    if (!window.confirm(`¿Confirmás que querés ${label} esta solicitud?`)) return;
    setBusyId(requestId);
    setError("");
    try {
      const updated = accept
        ? await api.acceptRequest(requestId, token)
        : await api.rejectRequest(requestId, token);
      setRequests((items) => items.map((item) => item.id === requestId ? updated : item));
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    } finally {
      setBusyId(null);
    }
  }

  function section(title: string, trips: Trip[], own = false) {
    return (
      <section className="mt-10">
        <h2 className="text-2xl font-black">{title}</h2>
        {trips.length === 0 ? <p className="status-card mt-4 text-slate-600">No hay viajes en esta sección.</p> :
          <div className="mt-5 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {trips.map((trip) => <TripCard actionLabel={own ? "Cancelar viaje" : undefined} busy={busyId === trip.id} key={trip.id} onAction={own ? () => cancel(trip.id) : undefined} trip={trip} />)}
          </div>}
      </section>
    );
  }

  return (
    <ProtectedRoute>
      <div className="container py-12">
        <p className="eyebrow">Tu actividad</p><h1 className="mt-2 text-4xl font-black">Mis viajes</h1>
        {error && <p className="error-message mt-6" role="alert">{error}</p>}
        {loading ? <div className="status-card mt-8">Cargando historial…</div> : <>
          <section className="mt-10">
            <h2 className="text-2xl font-black">Solicitudes recibidas</h2>
            {requests.length === 0 ? <p className="status-card mt-4 text-slate-600">Todavía no recibiste solicitudes.</p> :
              <div className="mt-5 grid gap-4">{requests.map((request) => <article className="trip-card" key={request.id}><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="eyebrow">Viaje #{request.viaje_id}</p><h3 className="mt-1 font-black">Solicitud #{request.id}</h3><p className="mt-2 text-sm text-slate-600">{request.mensaje_inicial || "Sin mensaje inicial"}</p></div><span className={request.estado === "aceptada" ? "badge-active" : request.estado === "rechazada" || request.estado === "cancelada" ? "badge-cancelled" : "badge-pending"}>{request.estado}</span></div>{request.estado === "pendiente" && <div className="mt-4 flex gap-3"><button className="button-primary" disabled={busyId === request.id} onClick={() => respond(request.id, true)} type="button">Aceptar</button><button className="button-secondary" disabled={busyId === request.id} onClick={() => respond(request.id, false)} type="button">Rechazar</button></div>}</article>)}</div>}
          </section>
          {section("Viajes creados", created, true)}
          {section("Viajes compartidos", joined)}
        </>}
      </div>
    </ProtectedRoute>
  );
}
