"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { LocationSearch } from "@/components/maps/LocationSearch";
import { MapView } from "@/components/maps/MapView";
import { api, ApiError } from "@/lib/api";
import { isWithinParaguay } from "@/lib/paraguayGeo";
import { decodePolyline } from "@/lib/polyline";
import type { GeoPoint, RouteResult, Vehicle } from "@/lib/types";

type Step = 1 | 2 | 3;
type FieldErrors = Partial<Record<"origin" | "destination" | "date" | "time" | "vehicle" | "seats" | "departure", string>>;

function localDateMinimum() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

const demoVehicle: Vehicle = { id: 1, propietario_id: 1, marca: "Toyota", modelo: "Corolla", color: "Plata", matricula: "ABC 123", capacidad: 4, activo: true, created_at: "", updated_at: "" };

export function PublishTripFlow({ demo = false }: { demo?: boolean }) {
  const { token } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [vehicles, setVehicles] = useState<Vehicle[]>(demo ? [demoVehicle] : []);
  const [origin, setOrigin] = useState(demo ? "San Lorenzo, Central, Paraguay" : "");
  const [destination, setDestination] = useState(demo ? "Asunción, Distrito Capital, Paraguay" : "");
  const [departure, setDeparture] = useState(demo ? "Paseo La Galería, Asunción, Paraguay" : "");
  const [originPoint, setOriginPoint] = useState<GeoPoint | null>(demo ? { latitude: -25.3397, longitude: -57.5088 } : null);
  const [destinationPoint, setDestinationPoint] = useState<GeoPoint | null>(demo ? { latitude: -25.2867, longitude: -57.3333 } : null);
  const [departurePoint, setDeparturePoint] = useState<GeoPoint | null>(demo ? { latitude: -25.2834, longitude: -57.5654 } : null);
  const [route, setRoute] = useState<RouteResult | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [vehicleId, setVehicleId] = useState(demo ? "1" : "");
  const [seats, setSeats] = useState("1");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [vehiclesLoading, setVehiclesLoading] = useState(!demo);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (demo || !token) return;
    const timer = window.setTimeout(() => api.vehicles(token).then((items) => setVehicles(items.filter((item) => item.activo))).catch(() => setError("No pudimos cargar tus vehículos.")).finally(() => setVehiclesLoading(false)), 0);
    return () => window.clearTimeout(timer);
  }, [demo, token]);
  useEffect(() => {
    if (!token || !originPoint || !destinationPoint) return;
    const timer = window.setTimeout(() => { setRouteLoading(true);api.route(originPoint,destinationPoint,token).then(setRoute).catch(()=>setRoute(null)).finally(()=>setRouteLoading(false)); }, 250);
    return () => window.clearTimeout(timer);
  }, [destinationPoint, originPoint, token]);

  const selectedVehicle = useMemo(() => vehicles.find((item) => item.id === Number(vehicleId)) ?? null, [vehicleId, vehicles]);
  const departureDate = useMemo(() => date && time ? new Date(`${date}T${time}`) : null, [date, time]);
  const mapRoute = useMemo<GeoPoint[] | undefined>(() => {
    if (!originPoint || !destinationPoint) return undefined;
    if (route?.geometry) {
      const decoded = decodePolyline(route.geometry).filter(isWithinParaguay);
      if (decoded.length >= 2) return decoded;
    }
    return [originPoint, destinationPoint];
  }, [destinationPoint, originPoint, route]);
  const seatCount = Number(seats);
  const changeSeats = (delta: number) => {
    if (!selectedVehicle) return;
    setSeats(String(Math.min(selectedVehicle.capacidad, Math.max(1, seatCount + delta))));
    setFieldErrors((current) => ({ ...current, seats: undefined }));
  };
  const markers = [
    ...(originPoint ? [{ id: "origin", ...originPoint, color: "#047857", label: "Origen", draggable: true }] : []),
    ...(destinationPoint ? [{ id: "destination", ...destinationPoint, color: "#e87924", label: "Destino", draggable: true }] : []),
    ...(departurePoint && step > 1 ? [{ id: "departure", ...departurePoint, color: "#0f766e", label: "Punto de salida", draggable: true }] : []),
  ];
  const chooseOrigin = (label: string, point: GeoPoint) => { setOrigin(label);setOriginPoint(point);if(!departurePoint){setDeparture(label);setDeparturePoint(point);} };
  const moveMarker = (id: string, point: GeoPoint) => {
    if (!token || !isWithinParaguay(point)) return;
    void api.reverseGeocode(point,token).then((result)=>{if(id==="origin")chooseOrigin(result.label,result);else if(id==="destination"){setDestination(result.label);setDestinationPoint(result);}else{setDeparture(result.label);setDeparturePoint(result);}}).catch(()=>setError("No pudimos validar ese punto en Paraguay."));
  };
  const continueRoute = () => {
    const next: FieldErrors = {};
    if (!originPoint) next.origin = "Seleccioná un origen de la lista.";
    if (!destinationPoint) next.destination = "Seleccioná un destino de la lista.";
    if (originPoint && destinationPoint && originPoint.latitude === destinationPoint.latitude && originPoint.longitude === destinationPoint.longitude) next.destination = "El destino debe ser diferente del origen.";
    setFieldErrors(next);
    if (Object.keys(next).length) return;
    setError("");setStep(2);
  };
  const continueDetails = () => {
    const next: FieldErrors = {};
    if (!date) next.date = "Elegí la fecha de salida.";
    if (!time) next.time = "Elegí la hora de salida.";
    if (departureDate && departureDate <= new Date()) next.date = "La salida debe ser en una fecha futura.";
    if (!selectedVehicle) next.vehicle = "Seleccioná uno de tus vehículos.";
    const seatCount = Number(seats);
    if (!Number.isInteger(seatCount) || seatCount < 1 || (selectedVehicle && seatCount > selectedVehicle.capacidad)) next.seats = "Elegí una cantidad válida según la capacidad del vehículo.";
    if (!departurePoint) next.departure = "Seleccioná un punto de salida de la lista.";
    setFieldErrors(next);
    if (Object.keys(next).length) return;
    setError("");setStep(3);
  };
  async function publish(event: FormEvent) {
    event.preventDefault();
    if (demo) { setSuccess(true); return; }
    if (!token || !originPoint || !destinationPoint || !departurePoint || !selectedVehicle || !departureDate || loading) return;
    setLoading(true);setError("");
    try {
      await api.createTrip({ origen:origin,destino:destination,fecha:departureDate.toISOString(),vehiculo_id:selectedVehicle.id,cupos_totales:Number(seats),descripcion:description,punto_salida:departure,punto_llegada:destination,origen_latitud:originPoint.latitude,origen_longitud:originPoint.longitude,destino_latitud:destinationPoint.latitude,destino_longitud:destinationPoint.longitude,punto_salida_latitud:departurePoint.latitude,punto_salida_longitud:departurePoint.longitude,punto_llegada_latitud:destinationPoint.latitude,punto_llegada_longitud:destinationPoint.longitude,...(route?{distancia_estimada_km:route.distance_km,duracion_estimada_minutos:route.duration_minutes,ruta_codificada:route.geometry??undefined}:{})},token);
      setSuccess(true);router.push("/mis-viajes?created=1");
    } catch(caught) { setError(caught instanceof ApiError?caught.message:"No pudimos publicar el viaje. Tus datos siguen guardados."); }
    finally { setLoading(false); }
  }

  const titles = step === 1
    ? { title: "¿A dónde vamos?", description: "Elegí el origen y el destino de tu viaje." }
    : step === 2
      ? { title: "Prepará tu viaje", description: "Definí cuándo salís, el vehículo y los lugares disponibles." }
      : { title: "Revisá antes de publicar", description: "Confirmá que todos los datos estén correctos." };
  return <main className="publish-flow">
    <header className="publish-heading"><p className="eyebrow">Compartí el camino</p><h1>Publicar viaje</h1><p>Definí tu recorrido, completá los detalles y publicá tu viaje en pocos pasos.</p></header>
    <ol className="publish-steps" aria-label="Progreso de publicación">{["Ruta", "Detalles", "Confirmación"].map((label, index) => <li className={step === index + 1 ? "current" : step > index + 1 ? "done" : ""} key={label} aria-current={step === index + 1 ? "step" : undefined}><span aria-hidden>{step > index + 1 ? "✓" : index + 1}</span><span className="publish-step-label"><small>Paso {index + 1}</small>{label}</span></li>)}</ol>
    {error && <p className="error-message publish-message" role="alert">{error}</p>}{success && <p className="success-message publish-message" role="status">El viaje fue publicado correctamente.</p>}
    <div className={`publish-layout is-step-${step}`}>
      <section className="publish-card"><form onSubmit={publish} noValidate>
        <header className="publish-section-heading"><span>{String(step).padStart(2, "0")}</span><div><p className="ui-eyebrow">Paso {step} de 3</p><h2>{titles.title}</h2><p>{titles.description}</p></div></header>
        {step === 1 && <div className="publish-step">
          <div className="publish-location-pair"><div><LocationSearch id="publish-origin" label="Origen" placeholder="Buscar origen en Paraguay" value={origin} onChange={(value) => { setOrigin(value); setOriginPoint(null); setRoute(null); setFieldErrors((current) => ({ ...current, origin: undefined })); }} onSelect={(item) => { chooseOrigin(item.label, item); setFieldErrors((current) => ({ ...current, origin: undefined })); }}/>{fieldErrors.origin && <p className="field-error" id="publish-origin-error" role="alert">{fieldErrors.origin}</p>}</div><div><LocationSearch id="publish-destination" label="Destino" placeholder="Buscar destino en Paraguay" value={destination} onChange={(value) => { setDestination(value); setDestinationPoint(null); setRoute(null); setFieldErrors((current) => ({ ...current, destination: undefined })); }} onSelect={(item) => { setDestination(item.label); setDestinationPoint(item); setFieldErrors((current) => ({ ...current, destination: undefined })); }}/>{fieldErrors.destination && <p className="field-error" id="publish-destination-error" role="alert">{fieldErrors.destination}</p>}</div></div>
          <p className="publish-country-note"><span aria-hidden>PY</span> Jahamina conecta viajes dentro de Paraguay.</p>
          <div className="publish-actions publish-route-actions"><button className="button-primary" type="button" onClick={continueRoute}>Continuar</button></div>
        </div>}
        {step === 2 && <div className="publish-step publish-details-grid">
          <div className="publish-details-primary"><div className="publish-date-grid"><div className="form-field"><label htmlFor="publish-date">Fecha</label><input id="publish-date" type="date" min={localDateMinimum()} value={date} onChange={(event) => { setDate(event.target.value); setFieldErrors((current) => ({ ...current, date: undefined })); }} aria-describedby={fieldErrors.date ? "publish-date-error" : undefined}/>{fieldErrors.date && <p className="field-error" id="publish-date-error" role="alert">{fieldErrors.date}</p>}</div><div className="form-field"><label htmlFor="publish-time">Hora</label><input id="publish-time" type="time" value={time} onChange={(event) => { setTime(event.target.value); setFieldErrors((current) => ({ ...current, time: undefined })); }} aria-describedby={fieldErrors.time ? "publish-time-error" : undefined}/>{fieldErrors.time && <p className="field-error" id="publish-time-error" role="alert">{fieldErrors.time}</p>}</div></div>
          <fieldset className="seat-picker" disabled={!selectedVehicle}><legend>Lugares disponibles</legend><div><button type="button" onClick={() => changeSeats(-1)} disabled={!selectedVehicle || seatCount <= 1} aria-label="Quitar un lugar">−</button><output aria-live="polite">{seatCount}</output><button type="button" onClick={() => changeSeats(1)} disabled={!selectedVehicle || seatCount >= (selectedVehicle?.capacidad ?? 1)} aria-label="Agregar un lugar">+</button></div><p>{seatCount} {seatCount === 1 ? "lugar disponible" : "lugares disponibles"}{selectedVehicle ? ` · máximo ${selectedVehicle.capacidad}` : ""}</p>{fieldErrors.seats && <p className="field-error" role="alert">{fieldErrors.seats}</p>}</fieldset>
          <div className="form-field"><label htmlFor="publish-description">Descripción <span>Opcional</span></label><textarea id="publish-description" value={description} onChange={(event) => setDescription(event.target.value)} maxLength={1000} placeholder="Información útil para quienes viajen contigo"/><small className="field-help">{description.length}/1000</small></div></div>
          <div className="publish-details-secondary"><section className="publish-details-route"><p className="ui-eyebrow">Recorrido elegido</p><h2>{origin} <span aria-hidden>→</span> {destination}</h2><p>Punto de salida: {departure}</p></section>
          <fieldset className="vehicle-picker"><legend>Vehículo</legend>{vehiclesLoading ? <div className="publish-inline-state" aria-live="polite">Cargando tus vehículos…</div> : vehicles.length === 0 ? <div className="publish-inline-state"><b>Necesitás registrar un vehículo antes de publicar.</b><p>Tu recorrido queda guardado mientras completás este paso.</p><Link className="button-secondary" href="/vehiculos">Registrar vehículo</Link></div> : <div className="vehicle-options">{vehicles.map((vehicle) => <label className={vehicle.id === selectedVehicle?.id ? "is-selected" : ""} key={vehicle.id}><input type="radio" name="publish-vehicle" value={vehicle.id} checked={vehicle.id === selectedVehicle?.id} onChange={() => { setVehicleId(String(vehicle.id)); setSeats("1"); setFieldErrors((current) => ({ ...current, vehicle: undefined, seats: undefined })); }}/><span className="vehicle-option-icon" aria-hidden><i/><i/></span><span><b>{vehicle.marca} {vehicle.modelo}</b><small>{vehicle.color}{vehicle.matricula ? ` · ${vehicle.matricula}` : ""}</small></span><em>{vehicle.id === selectedVehicle?.id ? "Seleccionado" : "Elegir"}</em></label>)}</div>}{fieldErrors.vehicle && <p className="field-error" role="alert">{fieldErrors.vehicle}</p>}</fieldset>
          <div><LocationSearch id="publish-departure" label="Punto de salida" placeholder="Buscar punto de salida en Paraguay" value={departure} onChange={(value) => { setDeparture(value); setDeparturePoint(null); setFieldErrors((current) => ({ ...current, departure: undefined })); }} onSelect={(item) => { setDeparture(item.label); setDeparturePoint(item); setFieldErrors((current) => ({ ...current, departure: undefined })); }}/>{fieldErrors.departure && <p className="field-error" role="alert">{fieldErrors.departure}</p>}</div></div>
          <div className="publish-actions publish-details-actions"><button className="button-secondary" type="button" onClick={() => setStep(1)}>Volver</button><button className="button-primary" type="button" onClick={continueDetails}>Continuar</button></div>
        </div>}
        {step === 3 && <div className="publish-step publish-confirmation"><header><div><p className="ui-eyebrow">Datos del viaje</p><h2>Todo listo para compartir</h2></div><div><button type="button" onClick={() => setStep(1)}>Editar recorrido</button><button type="button" onClick={() => setStep(2)}>Editar detalles</button></div></header><dl><div><dt>Fecha</dt><dd>{departureDate?.toLocaleDateString("es-PY", { dateStyle: "medium" })}</dd></div><div><dt>Hora</dt><dd>{departureDate?.toLocaleTimeString("es-PY", { hour: "2-digit", minute: "2-digit" })}</dd></div><div><dt>Vehículo</dt><dd>{selectedVehicle?.marca} {selectedVehicle?.modelo}<small>{selectedVehicle?.color}{selectedVehicle?.matricula ? ` · ${selectedVehicle.matricula}` : ""}</small></dd></div><div><dt>Lugares</dt><dd>{seatCount} {seatCount === 1 ? "disponible" : "disponibles"}</dd></div><div className="confirmation-departure"><dt>Punto de salida</dt><dd>{departure}</dd></div>{description && <div className="confirmation-description"><dt>Descripción</dt><dd>{description}</dd></div>}</dl><div className="publish-actions"><button className="button-secondary" type="button" onClick={() => setStep(2)}>Volver</button><button className="button-primary" disabled={loading} type="submit">{loading ? "Publicando…" : "Publicar viaje"}</button></div></div>}
      </form></section>
      <aside className="publish-map" aria-label="Vista del recorrido"><div className="publish-map-stage"><MapView markers={markers} route={mapRoute} onMarkerMove={moveMarker} onInvalidPoint={() => setError("Por ahora Jahamina solo permite ubicaciones dentro de Paraguay.")}/></div><section className={`publish-map-summary ${originPoint && destinationPoint ? "is-complete" : ""}`} aria-live="polite"><div className="publish-route-points"><span><i className="is-origin" aria-hidden/><small>Origen</small><b>{originPoint ? origin : "Por seleccionar"}</b></span><em aria-hidden/><span><i className="is-destination" aria-hidden/><small>Destino</small><b>{destinationPoint ? destination : "Por seleccionar"}</b></span></div>{route && <p className="publish-route-metrics"><b>{route.distance_km} km</b><span aria-hidden>·</span><b>{route.duration_minutes} min</b></p>}{routeLoading && <p className="publish-route-state"><span aria-hidden/> Calculando la mejor ruta…</p>}{!routeLoading && originPoint && destinationPoint && !route && <p className="publish-route-state is-muted">La ruta vial no está disponible. Podés continuar con los puntos elegidos.</p>}</section></aside>
    </div>
  </main>;
}
