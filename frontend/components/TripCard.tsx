import { VehicleImage } from "@/components/trip-roadmap/VehicleImage";
import type { Trip, Vehicle } from "@/lib/types";
import Link from "next/link";

interface TripCardProps {
  trip: Trip;
  actionLabel?: string;
  onAction?: () => void;
  busy?: boolean;
  role?: "conductor" | "pasajero";
  vehicle?: Vehicle | null;
  actionHref?: string;
}

function compactDate(value: string) {
  const date = new Date(value);
  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(now.getDate() + 1);
  const day = date.toDateString() === now.toDateString()
    ? "Hoy"
    : date.toDateString() === tomorrow.toDateString()
      ? "Mañana"
      : new Intl.DateTimeFormat("es-PY", { day: "numeric", month: "short" }).format(date);
  return `${day} · ${new Intl.DateTimeFormat("es-PY", { hour: "2-digit", minute: "2-digit" }).format(date)}`;
}

export function TripCard({ trip, actionLabel, onAction, busy = false, role, vehicle, actionHref }: TripCardProps) {
  const status = trip.cancelado || trip.estado === "cancelado"
    ? { label: "Cancelado", className: "badge-cancelled" }
    : trip.estado === "finalizado"
      ? { label: "Finalizado", className: "badge-active" }
      : trip.estado === "en_curso"
        ? { label: "En curso", className: "badge-pending" }
        : trip.estado === "completo" || trip.cupos_disponibles === 0
          ? { label: "Completo", className: "badge-pending" }
          : { label: "Disponible", className: "badge-active" };
  const occupied = trip.cupos_totales - trip.cupos_disponibles;

  return (
    <article className={`trip-card trip-card-official ${trip.cancelado || trip.estado === "cancelado" ? "is-cancelled" : ""}`}>
      <div className="trip-card-topline">
        <span className={status.className}>{status.label}</span>
        <span className="trip-role">{role === "conductor" ? "Vas como conductor" : role === "pasajero" ? "Vas como pasajero" : `Viaje #${trip.id}`}</span>
      </div>
      <div className="trip-route">
        <div className="trip-route-stop">
          <p className="trip-route-label"><span className="trip-route-pin is-origin" aria-hidden />Origen</p>
          <p className="trip-place">{trip.origen}</p>
        </div>
        <span aria-hidden className="trip-arrow">→</span>
        <div className="trip-route-stop is-destination">
          <p className="trip-route-label"><span className="trip-route-pin is-destination" aria-hidden />Destino</p>
          <p className="trip-place">{trip.destino}</p>
        </div>
      </div>
      <div className="trip-summary-row">
        <span className="trip-date"><span aria-hidden>◷</span>{compactDate(trip.fecha)}</span>
        <span className="trip-occupancy"><span aria-hidden>♙</span>{occupied} de {trip.cupos_totales} lugares</span>
      </div>
      <div className="trip-meta-row">
        <span>{trip.cupos_disponibles === 1 ? "1 lugar disponible" : `${trip.cupos_disponibles} lugares disponibles`}</span>
        <span>{trip.punto_salida}</span>
      </div>
      {vehicle && <div className="trip-vehicle"><VehicleImage brand={vehicle.marca} model={vehicle.modelo} color={vehicle.color} registration={vehicle.matricula} imageUrl={vehicle.imagen_url} /><div className="trip-vehicle-copy"><small>Vehículo asignado</small><b>{vehicle.marca} {vehicle.modelo}</b><span>{vehicle.color} · {vehicle.matricula}</span></div></div>}
      {actionHref && actionLabel && <Link className="button-secondary mt-5 w-full text-center" href={actionHref}>{actionLabel}</Link>}
      {actionLabel && onAction && !trip.cancelado && <button className="button-primary mt-5 w-full" disabled={busy} onClick={onAction} type="button">{busy ? "Procesando…" : actionLabel}</button>}
    </article>
  );
}
