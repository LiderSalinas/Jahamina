import type { LocationDemoState, RoadmapStop } from "./types";

const points = [[55, 205], [190, 105], [335, 185], [500, 95], [665, 62]];

export function TripMapPreview({ stops, location, selectedStop, onSelect, title = "Origen → destino", origin = "Origen", destination = "Destino", departure }: {
  stops: RoadmapStop[];
  location: LocationDemoState;
  selectedStop: number;
  onSelect: (index: number) => void;
  title?: string;
  origin?: string;
  destination?: string;
  departure?: string;
}) {
  return <section className="roadmap-map-card" aria-labelledby="map-preview-title">
    <header><div><p className="roadmap-kicker">Tu ruta</p><h2 id="map-preview-title">{title}</h2></div><span className={`location-pill is-${location}`}>{location === "activa" ? "● En línea" : location === "desactualizada" ? "◷ Desactualizada" : "○ Sin GPS en vivo"}</span></header>
    <div className="roadmap-map"><svg viewBox="0 0 720 250" role="img" aria-label={`Recorrido esquemático desde ${origin} hasta ${destination}; parada ${selectedStop + 1} destacada`}><defs><pattern id="roadmap-grid" width="38" height="38" patternUnits="userSpaceOnUse"><path d="M38 0H0V38" fill="none" stroke="#dfeae3"/></pattern></defs><rect width="720" height="250" fill="#eef5ef"/><rect width="720" height="250" fill="url(#roadmap-grid)"/><path d="M55 205C130 180 155 78 245 105S360 230 440 170S535 35 665 62" fill="none" stroke="#c4d7cd" strokeWidth="17" strokeLinecap="round"/><path d="M55 205C130 180 155 78 245 105S360 230 440 170S535 35 665 62" fill="none" stroke="#08745b" strokeWidth="7" strokeLinecap="round"/>{points.slice(0, stops.length).map(([x, y], index) => <g className={selectedStop === index ? "map-point selected" : "map-point"} key={`${x}-${y}`} transform={`translate(${x} ${y})`} onClick={() => onSelect(index)} role="button" tabIndex={0} aria-label={`Parada ${index + 1}: ${stops[index]?.title}`} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") onSelect(index); }}><circle className="map-point-halo" r="27"/><circle r="17"/><text textAnchor="middle" dy="5">{index + 1}</text></g>)}</svg><div className="route-endpoints"><span><small>Origen</small><b>{origin}</b></span><span><small>Destino</small><b>{destination}</b></span></div><div className="map-legend"><span><i className="meeting-dot"/>Parada seleccionada</span><span><i className="route-line"/>Vista del recorrido</span></div></div>
    <div className="map-stop-preview"><span><small>Parada seleccionada</small><b>{stops[selectedStop]?.title}</b></span><span>{stops[selectedStop]?.detail}</span>{departure && <span><small>Salida programada</small><b>{departure}</b></span>}</div>
  </section>;
}
