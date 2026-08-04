import type { LocationDemoState, ScenarioDefinition } from "./types";

export function TripStatusHero({ scenario,location }: { scenario:ScenarioDefinition; location:LocationDemoState }) {
  const update=location==="activa"?"Hace 2 min":location==="desactualizada"?"Hace 18 min · demo":"Sin señal demo";
  return <section className={`roadmap-hero is-${scenario.tripState.replace(" ","_")}`} aria-labelledby="trip-status-title"><div><p className="roadmap-kicker">Estado ahora · {scenario.passengerState}</p><h2 id="trip-status-title">{scenario.heroTitle}</h2><p className="roadmap-next"><span>Qué sucede ahora</span>{scenario.heroNext}</p></div><div className="roadmap-hero-meta"><span><b>{scenario.distance}</b><small>{scenario.minutes} · demo</small></span><span><b>{update}</b><small>ubicación simulada</small></span></div><div className="roadmap-vehicle-inline"><span aria-hidden="true">🚙</span><div><b>Toyota Corolla · Plata</b><small>ABC 123 · {scenario.role==="pasajero"?"conduce Rubén":"tu vehículo"}</small></div></div></section>;
}
