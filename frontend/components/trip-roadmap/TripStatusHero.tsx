import type { LocationDemoState, ScenarioDefinition } from "./types";

export function TripStatusHero({ scenario, location, vehicle }: { scenario: ScenarioDefinition; location: LocationDemoState; vehicle?: string }) {
  const update = location === "activa" ? "Disponible" : location === "desactualizada" ? "Desactualizada" : "No disponible";
  return <section className={`roadmap-hero is-${scenario.tripState.replace(" ", "_")}`} aria-labelledby="trip-status-title"><div><p className="roadmap-kicker">Estado ahora · {scenario.passengerState}</p><h2 id="trip-status-title">{scenario.heroTitle}</h2><p className="roadmap-next"><span>Qué sucede ahora</span>{scenario.heroNext}</p></div><div className="roadmap-hero-meta"><span><b>{scenario.distance}</b><small>{scenario.minutes}</small></span><span><b>{update}</b><small>ubicación de referencia</small></span></div><div className="roadmap-vehicle-inline"><span aria-hidden="true">🚙</span><div><b>{vehicle ?? "Toyota Corolla · Plata"}</b><small>{scenario.role === "pasajero" ? "Vehículo del conductor" : "Tu vehículo"}</small></div></div></section>;
}
