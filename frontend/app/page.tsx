import Link from "next/link";

function PinIcon({ destination = false }: { destination?: boolean }) {
  return <span className={destination ? "landing-pin is-destination" : "landing-pin"} aria-hidden="true" />;
}

function RouteMapArtwork() {
  return (
    <div className="landing-map" aria-label="Ruta ilustrativa de Asunción a Ciudad del Este">
      <svg viewBox="0 0 760 560" role="img" aria-hidden="true">
        <defs>
          <pattern id="map-grid" width="44" height="44" patternUnits="userSpaceOnUse">
            <path d="M44 0H0V44" fill="none" stroke="currentColor" strokeOpacity=".1" />
          </pattern>
          <filter id="route-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="5" stdDeviation="6" floodOpacity=".16" />
          </filter>
        </defs>
        <rect width="760" height="560" fill="url(#map-grid)" />
        <path className="map-country" d="M248 34 391 58l59 42 110 12 52 83-28 79 36 88-62 75-13 81-110 8-75-46-93 18-72-67 18-94-51-74 56-70-13-83Z" />
        <path className="map-river" d="M405 71c-21 64 20 86-9 143-25 50-9 92 18 124 30 36 8 100 38 166" />
        <path className="map-route-halo" d="M283 326c57-33 88-28 128-6 43 23 88 12 132-20 25-19 49-26 77-31" />
        <path className="map-route" d="M283 326c57-33 88-28 128-6 43 23 88 12 132-20 25-19 49-26 77-31" filter="url(#route-shadow)" />
        <circle className="map-origin" cx="283" cy="326" r="12" />
        <circle className="map-destination" cx="620" cy="269" r="12" />
        <circle className="map-waypoint" cx="465" cy="320" r="6" />
      </svg>
      <div className="map-label map-label-origin"><b>Asunción</b><small>Salida · 14:30</small></div>
      <div className="map-label map-label-destination"><b>Ciudad del Este</b><small>Llegada estimada · 19:00</small></div>
      <div className="map-route-chip"><span>PY-02</span><b>327 km</b><small>≈ 4 h 30 min</small></div>
      <div className="map-live-note"><i /> Vista del trayecto</div>
    </div>
  );
}

const trips = [
  { time: "14:30", route: "Asunción → Ciudad del Este", seats: "3 lugares" },
  { time: "16:00", route: "Asunción → Encarnación", seats: "2 lugares" },
  { time: "18:00", route: "Luque → San Bernardino", seats: "3 lugares" },
];

export default function Home() {
  return (
    <div className="landing-page">
      <section className="landing-hero">
        <div className="landing-hero-copy">
          <p className="landing-kicker"><span /> Personas · rutas · un Paraguay más conectado</p>
          <h1>Compartimos ruta.<br /><strong>Llegamos mejor.</strong></h1>
          <p className="landing-lead">Encontrá personas que viajan hacia tu mismo destino y coordiná cada paso con claridad.</p>
          <div className="landing-hero-actions">
            <Link className="button-primary" href="/registro">Empezar ahora <span aria-hidden="true">→</span></Link>
            <Link className="landing-text-link" href="#como-funciona">Conocer cómo funciona</Link>
          </div>
          <div className="landing-trust-row" id="seguridad">
            <span><b>01</b> Perfiles identificados</span>
            <span><b>02</b> Reservas claras</span>
            <span><b>03</b> Chat privado</span>
          </div>
        </div>
        <RouteMapArtwork />
        <div className="landing-search-card">
          <div className="landing-search-heading">
            <span>Buscar trayecto</span>
            <Link href="/login?next=/viajes/nuevo">Publicar trayecto</Link>
          </div>
          <div className="landing-search-fields">
            <div><PinIcon /><span><small>Origen</small><b>Asunción</b></span></div>
            <span className="landing-swap" aria-hidden="true">⇄</span>
            <div><PinIcon destination /><span><small>Destino</small><b>Ciudad del Este</b></span></div>
            <div className="landing-date"><span aria-hidden="true">□</span><span><small>Salida</small><b>Hoy, 14:30</b></span></div>
            <Link className="landing-search-button" href="/login?next=/viajes">Buscar trayecto <span aria-hidden="true">→</span></Link>
          </div>
        </div>
      </section>

      <section className="landing-trips" id="como-funciona">
        <div className="landing-section-heading">
          <div><p className="landing-kicker">Ejemplos de trayectos</p><h2>Rutas frecuentes para empezar a moverte.</h2></div>
          <Link href="/login?next=/viajes">Ver todos los trayectos <span aria-hidden="true">→</span></Link>
        </div>
        <div className="landing-trip-list">
          {trips.map((trip, index) => (
            <Link href="/login?next=/viajes" className="landing-trip-row" key={trip.time}>
              <span className="landing-trip-index">0{index + 1}</span>
              <time>{trip.time}<small>Hoy</small></time>
              <strong>{trip.route}</strong>
              <span>{trip.seats}</span>
              <i aria-hidden="true">→</i>
            </Link>
          ))}
        </div>
      </section>

      <section className="landing-principles">
        <div><p className="landing-kicker">Hecho para movernos juntos</p><h2>Más personas.<br />Más destinos.<br /><strong>Un Paraguay conectado.</strong></h2></div>
        <p>Jahamina organiza el encuentro entre personas que comparten camino. Vos elegís el trayecto, conocés los detalles y mantenés el control de tu viaje.</p>
        <Link className="button-primary" href="/registro">Crear mi cuenta <span aria-hidden="true">→</span></Link>
      </section>
    </div>
  );
}
