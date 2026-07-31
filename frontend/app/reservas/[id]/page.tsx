"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { api, ApiError } from "@/lib/api";
import type { TripRequest } from "@/lib/types";

export default function ReservationDetailPage() {
  const { token } = useAuth();
  const params = useParams<{ id: string }>();
  const [request, setRequest] = useState<TripRequest | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    const timer = window.setTimeout(() => {
      api.request(Number(params.id), token)
        .then(setRequest)
        .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Error inesperado."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [params.id, token]);

  return (
    <ProtectedRoute>
      <section className="container py-12">
        {error && <p className="error-message" role="alert">{error}</p>}
        {!request ? <div className="status-card">Cargando reserva…</div> : <>
          <div className="form-card">
            <p className="eyebrow">Viaje #{request.viaje_id}</p>
            <div className="mt-2 flex flex-wrap items-center justify-between gap-4">
              <h1 className="text-3xl font-black">Reserva #{request.id}</h1>
              <span className={request.estado === "aceptada" || request.estado === "finalizada" ? "badge-active" : request.estado === "pendiente" ? "badge-pending" : "badge-cancelled"}>{request.estado}</span>
            </div>
            <dl className="mt-8 grid gap-5 md:grid-cols-2">
              <div><dt className="eyebrow">Mensaje inicial</dt><dd className="mt-1">{request.mensaje_inicial || "Sin mensaje"}</dd></div>
              <div><dt className="eyebrow">Punto propuesto</dt><dd className="mt-1">{request.punto_encuentro_propuesto || "Por confirmar"}</dd></div>
            </dl>
          </div>
          <div className="mt-6 grid gap-6 md:grid-cols-2">
            <ChatPanel reservationId={request.id} />
            <section className="status-card"><p className="eyebrow">Próxima fase</p><h2 className="mt-2 text-xl font-black">Ubicación en tiempo real</h2><p className="mt-3 text-slate-600">Este espacio alojará el mapa, permisos de ubicación y estado de seguimiento durante el viaje.</p></section>
          </div>
        </>}
      </section>
    </ProtectedRoute>
  );
}
