"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import type { MeetingPoint } from "@/lib/types";
import { MapView } from "./MapView";

export function MeetingPointSelector({ reservationId }: { reservationId: number }) {
  const { token } = useAuth(); const [point, setPoint] = useState<MeetingPoint | null>(null); const [text, setText] = useState("");
  useEffect(() => { if (token) api.meetingPoint(reservationId, token).then(setPoint).catch(() => undefined); }, [reservationId, token]);
  if (!token) return null;
  const latitude = point?.latitude ?? Number(process.env.NEXT_PUBLIC_DEFAULT_LATITUDE ?? -25.2867); const longitude = point?.longitude ?? Number(process.env.NEXT_PUBLIC_DEFAULT_LONGITUDE ?? -57.3333);
  return <section className="mobility-panel"><div><p className="eyebrow">Punto de encuentro</p><h2 className="text-xl font-black">{point?.texto || "Aún no definido"}</h2><span className="badge-pending">{point?.estado || "sin_definir"}</span></div><MapView className="meeting-map" markers={point?.latitude ? [{ id: "meeting", latitude, longitude, color: "#f59e0b", label: point.texto ?? "Punto de encuentro" }] : []} /><div className="form-field"><label htmlFor="meeting-text">Proponer lugar</label><input id="meeting-text" value={text} onChange={(e) => setText(e.target.value)} placeholder="Ej. entrada principal" /></div><div className="flex flex-wrap gap-2"><button className="button-secondary" type="button" disabled={!text.trim()} onClick={() => navigator.geolocation.getCurrentPosition((position) => api.proposeMeetingPoint(reservationId, { texto: text, latitude: position.coords.latitude, longitude: position.coords.longitude }, token).then(setPoint))}>Proponer mi ubicación</button>{point?.estado === "propuesto" && <><button className="button-primary" type="button" onClick={() => api.confirmMeetingPoint(reservationId, token).then(setPoint)}>Confirmar</button><button className="button-danger" type="button" onClick={() => api.rejectMeetingPoint(reservationId, token).then(setPoint)}>Rechazar</button></>}</div>{point?.latitude && <a className="button-secondary" href={`https://www.openstreetmap.org/directions?to=${point.latitude},${point.longitude}`} target="_blank" rel="noreferrer">Abrir indicaciones</a>}</section>;
}
