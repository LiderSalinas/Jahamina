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

  return (
    <article className="trip-card">
      <div className="flex items-start justify-between gap-4">
        <span className={trip.cancelado ? "badge-cancelled" : "badge-active"}>
          {trip.cancelado ? "Cancelado" : "Disponible"}
        </span>
        <span className="text-xs font-semibold text-slate-500">#{trip.id}</span>
      </div>
      <div className="mt-5 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <div>
          <p className="eyebrow">Origen</p>
          <p className="font-bold text-slate-900">{trip.origen}</p>
        </div>
        <span aria-hidden className="text-2xl text-amber-500">→</span>
        <div className="text-right">
          <p className="eyebrow">Destino</p>
          <p className="font-bold text-slate-900">{trip.destino}</p>
        </div>
      </div>
      <p className="mt-5 border-t border-slate-100 pt-4 text-sm text-slate-600">
        {date}
      </p>
      <div className="mt-3 flex items-center justify-between text-sm">
        <span className="font-semibold text-slate-600">
          {trip.cupos_disponibles} de {trip.cupos_totales} lugares
        </span>
        <span className="font-bold capitalize text-emerald-700">
          {trip.estado.replace("_", " ")}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-600">
        {trip.punto_salida} → {trip.punto_llegada}
      </p>
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
