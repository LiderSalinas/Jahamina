import type { Trip } from "@/lib/types";

interface TripCardProps {
  trip: Trip;
  actionLabel?: string;
  onAction?: () => void;
  busy?: boolean;
}

export function TripCard({
  trip,
  actionLabel,
  onAction,
  busy = false,
}: TripCardProps) {
  const date = new Intl.DateTimeFormat("es-PY", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(trip.fecha));
  const status = trip.cancelado || trip.estado === "cancelado"
    ? { label: "Cancelado", className: "badge-cancelled" }
    : trip.estado === "finalizado"
      ? { label: "Finalizado", className: "badge-active" }
      : trip.estado === "en_curso"
        ? { label: "En curso", className: "badge-pending" }
        : trip.estado === "completo" || trip.cupos_disponibles === 0
          ? { label: "Completo", className: "badge-pending" }
          : { label: "Disponible", className: "badge-active" };

  return (
    <article className="trip-card trip-card-official">
      <div className="flex items-start justify-between gap-4">
        <span className={status.className}>{status.label}</span>
        <span className="trip-reference">Viaje #{trip.id}</span>
      </div>
      <div className="trip-route">
        <div>
          <p className="eyebrow">Origen</p>
          <p className="trip-place">{trip.origen}</p>
        </div>
        <span aria-hidden className="trip-arrow">→</span>
        <div className="text-right">
          <p className="eyebrow">Destino</p>
          <p className="trip-place">{trip.destino}</p>
        </div>
      </div>
      <p className="trip-date">
        {date}
      </p>
      <div className="trip-meta-row">
        <span>
          {trip.cupos_disponibles} de {trip.cupos_totales} lugares
        </span>
        <span>{trip.cupos_disponibles === 1 ? "1 lugar libre" : `${trip.cupos_disponibles} lugares libres`}</span>
      </div>
      {actionLabel && onAction && !trip.cancelado && (
        <button
          className="button-primary mt-5 w-full"
          disabled={busy}
          onClick={onAction}
          type="button"
        >
          {busy ? "Procesando…" : actionLabel}
        </button>
      )}
    </article>
  );
}
