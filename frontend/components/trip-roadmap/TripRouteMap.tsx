import { MapView, type MapMarker } from "@/components/maps/MapView";
import { decodePolyline } from "@/lib/polyline";
import { isWithinParaguay } from "@/lib/paraguayGeo";
import type { RoadmapStopReal } from "@/lib/types";
import { TripMapPreview } from "./TripMapPreview";
import type { RoadmapStop } from "./types";

type TripRouteMapProps = {
  stops: RoadmapStop[];
  realStops: RoadmapStopReal[];
  encodedRoute: string | null;
  selectedStop: number;
  onSelect: (index: number) => void;
  origin: string;
  destination: string;
  departure: string;
};

function hasValidCoordinates(stop: RoadmapStopReal) {
  return stop.latitud != null
    && stop.longitud != null
    && Number.isFinite(stop.latitud)
    && Number.isFinite(stop.longitud)
    && isWithinParaguay({ latitude: stop.latitud, longitude: stop.longitud });
}

export function TripRouteMap({ stops, realStops, encodedRoute, selectedStop, onSelect, origin, destination, departure }: TripRouteMapProps) {
  const geographicStops = realStops.filter(hasValidCoordinates);
  const hasOrigin = geographicStops.some((stop) => stop.tipo === "origen");
  const hasDestination = geographicStops.some((stop) => stop.tipo === "destino");

  if (!hasOrigin || !hasDestination) {
    return <TripMapPreview stops={stops} location="sin_ubicacion" selectedStop={selectedStop} onSelect={onSelect} title={`${origin} → ${destination}`} origin={origin} destination={destination} departure={departure}/>;
  }

  const markers: MapMarker[] = geographicStops.map((stop, index) => ({
    id: stop.tipo === "origen" ? "origin" : stop.tipo === "destino" ? "destination" : `stop-${stop.id ?? stop.orden}-${index}`,
    latitude: stop.latitud!,
    longitude: stop.longitud!,
    color: stop.tipo === "destino" ? "#e98520" : stop.tipo === "origen" ? "#075b49" : "#5f8f7f",
    label: stop.nombre_publico,
  }));
  const decodedRoute = encodedRoute ? decodePolyline(encodedRoute).filter(isWithinParaguay) : [];
  const selected = realStops[selectedStop];

  return <section className="roadmap-map-card trip-real-map" aria-labelledby="real-route-title">
    <header><div><p className="roadmap-kicker">Tu ruta</p><h2 id="real-route-title">{origin} → {destination}</h2></div></header>
    <div className="publish-map-stage"><MapView markers={markers} route={decodedRoute.length >= 2 ? decodedRoute : undefined}/></div>
    <div className="publish-map-summary">
      <div className="publish-route-points"><span><i className="is-origin" aria-hidden/><small>Origen</small><b>{origin}</b></span><em aria-hidden/><span><i className="is-destination" aria-hidden/><small>Destino</small><b>{destination}</b></span></div>
      <dl><div><dt>Salida programada</dt><dd>{departure}</dd></div>{selected && <div><dt>Parada seleccionada</dt><dd>{selected.nombre_publico}</dd></div>}</dl>
    </div>
  </section>;
}
