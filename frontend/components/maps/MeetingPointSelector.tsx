"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { isWithinParaguay } from "@/lib/paraguayGeo";
import type { MeetingPoint } from "@/lib/types";
import { MapView } from "./MapView";

export function MeetingPointSelector({ reservationId, reservationState = "pendiente", tripState = "programado" }: { reservationId: number; reservationState?: string; tripState?: string }) {
  const { token } = useAuth();
  const [point, setPoint] = useState<MeetingPoint | null>(null);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { if (token) api.meetingPoint(reservationId, token).then(setPoint).catch(() => undefined); }, [reservationId, token]);
  if (!token) return null;

  const finished = reservationState === "finalizada" || tripState === "finalizado";
  const started = ["conductor_en_camino", "conductor_en_punto", "abordaje", "en_curso", "pausado", "finalizado"].includes(tripState);
  const closed = started || reservationState === "cancelada" || tripState === "cancelado";
  const canPropose = reservationState === "aceptada" && !closed;
  const hasPoint = Boolean(point?.texto && point.latitude != null && point.longitude != null);
  const stateLabel = (finished || started) && !hasPoint ? "Sin información registrada" : point?.estado === "confirmado" ? "Confirmado" : point?.estado === "propuesto" ? "Por confirmar" : point?.estado === "rechazado" ? "No acordado" : "Todavía no definido";

  const proposeDeviceLocation = () => navigator.geolocation.getCurrentPosition((position) => {
    const selected = { latitude: position.coords.latitude, longitude: position.coords.longitude };
    if (!isWithinParaguay(selected)) { setError("Por ahora Jahamina solo permite ubicaciones dentro de Paraguay."); return; }
    setError("");
    void api.reverseGeocode(selected, token)
      .then((result) => api.proposeMeetingPoint(reservationId, { texto: result.label, latitude: result.latitude, longitude: result.longitude }, token))
      .then(setPoint)
      .catch(() => setError("No se pudo validar la ubicación dentro de Paraguay."));
  }, () => setError("No se pudo obtener la ubicación del dispositivo."));

  return <section className={`mobility-panel ${hasPoint ? "has-meeting-point" : "meeting-empty"}`}>
    <div className="meeting-heading"><span className="meeting-icon" aria-hidden>⌖</span><div><p className="eyebrow">Punto de encuentro</p><h2>{hasPoint ? point?.texto : started ? "Sin información registrada" : "Punto de encuentro todavía no definido"}</h2></div><span className={point?.estado === "confirmado" ? "badge-active" : started ? "status-badge" : "badge-pending"}>{stateLabel}</span></div>
    {hasPoint && <MapView className="meeting-map" markers={[{ id: "meeting", latitude: point!.latitude!, longitude: point!.longitude!, color: "#f59e0b", label: point!.texto! }]}/>}
    {canPropose && !hasPoint && <><div className="form-field"><label htmlFor="meeting-text">Referencia del lugar</label><input id="meeting-text" value={text} onChange={(event) => setText(event.target.value)} placeholder="Ej. entrada principal"/></div><button className="button-secondary" type="button" disabled={!text.trim()} onClick={proposeDeviceLocation}>Proponer mi ubicación</button></>}
    {error && <p className="error-message" role="alert">{error}</p>}
    {!closed && point?.estado === "propuesto" && <div className="meeting-actions"><button className="button-primary" type="button" onClick={() => api.confirmMeetingPoint(reservationId, token).then(setPoint)}>Confirmar</button><button className="button-danger" type="button" onClick={() => api.rejectMeetingPoint(reservationId, token).then(setPoint)}>Rechazar</button></div>}
    {hasPoint && <a className="button-secondary meeting-directions" href={`https://www.openstreetmap.org/directions?to=${point!.latitude},${point!.longitude}`} target="_blank" rel="noreferrer">Abrir indicaciones</a>}
  </section>;
}
