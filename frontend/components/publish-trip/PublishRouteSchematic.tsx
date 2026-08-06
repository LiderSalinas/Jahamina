export interface PublishRouteStop {
  id: string | number;
  label: string;
}

export type PublishRouteStatus = "empty" | "partial" | "loading" | "ready" | "schematic";

interface PublishRouteSchematicProps {
  origin?: string;
  destination?: string;
  stops?: PublishRouteStop[];
  status?: PublishRouteStatus;
  compact?: boolean;
  interactive?: boolean;
  className?: string;
}

const PATH = "M70 156C180 156 182 46 330 62S496 180 620 128 724 43 830 55";
const STOP_POSITIONS = [
  { x: 250, y: 64 },
  { x: 380, y: 91 },
  { x: 505, y: 153 },
  { x: 640, y: 115 },
  { x: 735, y: 63 },
];

function deriveStatus(origin?: string, destination?: string): PublishRouteStatus {
  if (origin && destination) return "schematic";
  if (origin) return "partial";
  return "empty";
}

export function PublishRouteSchematic({ origin, destination, stops = [], status, compact = false, interactive = false, className = "" }: PublishRouteSchematicProps) {
  const currentStatus = status ?? deriveStatus(origin, destination);
  const complete = Boolean(origin && destination);
  const accessibleTitle = complete ? `Recorrido desde ${origin} hasta ${destination}` : origin ? `Origen seleccionado: ${origin}; destino pendiente` : "Recorrido pendiente de origen y destino";
  const accessibleDescription = complete
    ? `Representación esquemática con ${stops.length} ${stops.length === 1 ? "parada real" : "paradas reales"}. No representa calles.`
    : origin
      ? "El origen está seleccionado y todavía falta elegir el destino."
      : "Elegí origen y destino para preparar el recorrido.";
  const helper = currentStatus === "loading"
    ? "Preparando la vista del recorrido…"
    : currentStatus === "partial"
      ? "Ahora elegí el destino."
      : currentStatus === "empty"
        ? "Elegí origen y destino para preparar tu recorrido."
        : currentStatus === "schematic"
          ? "Vista esquemática disponible"
          : "Recorrido preparado";

  return <section className={`publish-schematic is-${currentStatus} ${compact ? "is-compact" : ""} ${interactive ? "is-interactive" : ""} ${className}`.trim()} aria-labelledby="publish-schematic-title">
    <header><div><p className="ui-eyebrow">Vista previa del trayecto</p><h2 id="publish-schematic-title">Tu recorrido</h2><p>Representación esquemática · No representa calles</p></div>{complete && <span>{currentStatus === "loading" ? "Preparando…" : currentStatus === "ready" ? "Recorrido preparado" : "Vista disponible"}</span>}</header>
    <div className="publish-schematic-canvas">
      <svg viewBox="0 0 900 210" role="img" aria-labelledby="publish-route-svg-title publish-route-svg-description" preserveAspectRatio="xMidYMid meet">
        <title id="publish-route-svg-title">{accessibleTitle}</title><desc id="publish-route-svg-description">{accessibleDescription}</desc>
        <defs><pattern id="publish-route-grid" width="42" height="42" patternUnits="userSpaceOnUse"><path d="M42 0H0V42"/></pattern></defs>
        <rect className="schematic-grid" width="900" height="210"/>
        <path className="schematic-shadow" d={PATH}/><path className="schematic-line" d={PATH}/>
        {origin && <g className="schematic-origin schematic-marker" transform="translate(70 156)"><circle className="point-halo" r="25"/><circle r="14"/><path d="m-5 0 3.5 3.5L6-5"/></g>}
        {!destination && origin && <g className="schematic-pending" aria-hidden="true" transform="translate(830 55)"><circle r="14"/><circle r="4"/></g>}
        {stops.slice(0, STOP_POSITIONS.length).map((stop, index) => { const point = STOP_POSITIONS[index]; return <g className="schematic-stop schematic-marker" transform={`translate(${point.x} ${point.y})`} key={stop.id}><circle className="point-halo" r="20"/><circle r="12"/><text y="4" textAnchor="middle">{index + 1}</text><title>{stop.label}</title></g>; })}
        {destination && <g className="schematic-destination schematic-marker" transform="translate(830 55)"><circle className="point-halo" r="25"/><circle r="14"/><path d="M0-6 6 0 0 6-6 0Z"/></g>}
      </svg>
      <div className="publish-schematic-labels"><span className={!origin ? "is-pending" : ""}><small>Origen</small><b>{origin || "Por elegir"}</b></span><i aria-hidden>→</i><span className={!destination ? "is-pending" : ""}><small>Destino</small><b>{destination || "Por elegir"}</b></span></div>
    </div>
    <footer><p>{helper}</p>{complete && <div className="publish-schematic-summary"><span><small>Origen</small><b>{origin}</b></span>{stops.length > 0 && <span><small>Paradas</small><b>{stops.length}</b></span>}<span><small>Destino</small><b>{destination}</b></span></div>}</footer>
  </section>;
}
