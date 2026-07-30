"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import type { TripRequest } from "@/lib/types";

export default function ReservationsPage() {
  const { token } = useAuth();
  const [requests, setRequests] = useState<TripRequest[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    try { setRequests(await api.myRequests(token)); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Error inesperado."); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function cancel(id: number) {
    if (!token || !window.confirm("¿Cancelar esta solicitud o reserva?")) return;
    try { await api.cancelRequest(id, token); await load(); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Error inesperado."); }
  }

  return (
    <ProtectedRoute>
      <section className="container py-12">
        <p className="eyebrow">Pasajero</p><h1 className="mt-2 text-4xl font-black">Mis reservas</h1>
        {error && <p className="error-message mt-6" role="alert">{error}</p>}
        {loading ? <div className="status-card mt-8">Cargando reservas…</div> : requests.length === 0 ? <div className="status-card mt-8"><h2 className="text-xl font-black">Todavía no solicitaste lugares</h2><p className="mt-2 text-slate-600">Explorá viajes publicados y solicitá un lugar.</p></div> :
          <div className="mt-8 grid gap-5 md:grid-cols-2">{requests.map((request) => <article className="trip-card" key={request.id}><div className="flex items-start justify-between gap-3"><div><p className="eyebrow">Viaje #{request.viaje_id}</p><h2 className="mt-1 text-xl font-black">Reserva #{request.id}</h2></div><span className={request.estado === "aceptada" || request.estado === "finalizada" ? "badge-active" : request.estado === "pendiente" ? "badge-pending" : "badge-cancelled"}>{request.estado}</span></div><p className="mt-4 text-sm text-slate-600">{request.punto_encuentro_propuesto || "Punto de encuentro por confirmar"}</p><div className="mt-5 flex flex-wrap gap-3"><Link className="button-secondary" href={`/reservas/${request.id}`}>Ver detalle</Link>{["pendiente", "aceptada"].includes(request.estado) && <button className="button-danger" onClick={() => cancel(request.id)} type="button">Cancelar</button>}</div></article>)}</div>}
      </section>
    </ProtectedRoute>
  );
}
