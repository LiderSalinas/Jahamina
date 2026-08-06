"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { UnreadBadge } from "@/components/chat/UnreadBadge";
import { api, ApiError } from "@/lib/api";
import type { RelatedReservation } from "@/lib/types";
import { PageContainer } from "@/components/ui/PageContainer";
import { AsyncState, PageHeader } from "@/components/ui/AppUI";

function ReservationCard({ reservation }: { reservation: RelatedReservation }) {
  return <article className="trip-card reservation-list-card">
    <div className="flex items-start justify-between gap-3">
      <div><p className="eyebrow">{reservation.rol === "conductor" ? "Como conductor" : "Como pasajero"} · Viaje #{reservation.viaje_id}</p><h3>{reservation.origen} <span aria-hidden>→</span> {reservation.destino}</h3></div>
      <span className={reservation.estado === "aceptada" || reservation.estado === "finalizada" ? "badge-active" : reservation.estado === "pendiente" ? "badge-pending" : "badge-cancelled"}>{reservation.estado}</span>
    </div>
    <dl className="mt-4 grid gap-2 text-sm text-slate-600">
      <div><dt className="inline font-bold">Participante: </dt><dd className="inline">{reservation.participante}</dd></div>
      <div><dt className="inline font-bold">Fecha: </dt><dd className="inline">{new Date(reservation.fecha).toLocaleString("es-PY", { dateStyle: "medium", timeStyle: "short" })}</dd></div>
    </dl>
    <p className="mt-4 line-clamp-2 text-sm text-slate-600">{reservation.ultimo_mensaje || "Sin mensajes todavía"}</p>
    <div className="mt-5 flex items-center gap-3"><Link className="button-secondary" href={`/reservas/${reservation.reserva_id}`}>Ver detalle</Link><UnreadBadge count={reservation.no_leidos} /></div>
  </article>;
}

export default function ReservationsPage() {
  const { token } = useAuth();
  const [reservations, setReservations] = useState<RelatedReservation[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    try { setReservations(await api.relatedReservations(token)); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Error inesperado."); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    const polling = window.setInterval(() => void load(), 10000);
    window.addEventListener("jahamina:unread-changed", load);
    return () => { window.clearTimeout(timer); window.clearInterval(polling); window.removeEventListener("jahamina:unread-changed", load); };
  }, [load]);

  const passenger = reservations.filter((item) => item.rol === "pasajero");
  const driver = reservations.filter((item) => item.rol === "conductor");
  return <ProtectedRoute><PageContainer className="page-stack">
    <PageHeader eyebrow="Actividad compartida" title="Reservas" description="Seguí tus solicitudes y los lugares de tus viajes."/>
    {error && <p className="error-message mt-6" role="alert">{error}</p>}
    {loading ? <AsyncState kind="loading" title="Cargando reservas…"/> : <div className="section-stack">
      <section><h2 className="section-title">Como pasajero</h2>{passenger.length ? <div className="card-grid card-grid-two">{passenger.map((item) => <ReservationCard key={`passenger-${item.reserva_id}`} reservation={item} />)}</div> : <AsyncState title="Todavía no solicitaste lugares" description="Cuando solicites un viaje, aparecerá aquí."/>}</section>
      <section><h2 className="section-title">Como conductor</h2>{driver.length ? <div className="card-grid card-grid-two">{driver.map((item) => <ReservationCard key={`driver-${item.reserva_id}`} reservation={item} />)}</div> : <AsyncState title="Todavía no recibiste solicitudes" description="Las reservas de tus viajes aparecerán aquí."/>}</section>
    </div>}
  </PageContainer></ProtectedRoute>;
}
