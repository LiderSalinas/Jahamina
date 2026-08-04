"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import type { CurrentLocation, LocationEta, Tracking } from "@/lib/types";
import { MapView } from "./MapView";

type Props = {
  tripId: number;
  reservationId: number;
  isDriver: boolean;
  nextStop: { latitude: number; longitude: number; label: string } | null;
  onContextChange?: (context: LocationEta | null) => void;
};

export function LiveLocationPanel({ tripId, reservationId, isDriver, nextStop, onContextChange }: Props) {
  const { token } = useAuth();
  const [tracking, setTracking] = useState<Tracking | null>(null);
  const [context, setContext] = useState<LocationEta | null>(null);
  const [status, setStatus] = useState("desconectado");
  const [permission, setPermission] = useState("sin solicitar");
  const [watching, setWatching] = useState(false);
  const [error, setError] = useState("");
  const socket = useRef<WebSocket | null>(null);
  const watch = useRef<number | null>(null);
  const lastSent = useRef<{ at: number; latitude: number; longitude: number } | null>(null);
  const sequence = useRef(0);
  const configuring = useRef(false);
  const reconnect = useRef<number | null>(null);
  const mounted = useRef(true);
  const connectRef = useRef<() => Promise<void>>(async () => undefined);

  const updateContext = useCallback(async () => {
    if (!token) return;
    try {
      const value = await api.locationContext(reservationId, token);
      if (mounted.current) { setContext(value); onContextChange?.(value); }
    } catch { /* La ausencia de posición es un estado esperado. */ }
  }, [onContextChange, reservationId, token]);

  const stopWatch = useCallback(() => {
    if (watch.current !== null) navigator.geolocation.clearWatch(watch.current);
    watch.current = null;
    setWatching(false);
  }, []);

  const connect = useCallback(async () => {
    if (!token || !mounted.current || socket.current?.readyState === WebSocket.OPEN || socket.current?.readyState === WebSocket.CONNECTING) return;
    setStatus("reconectando");
    try {
      const connection = await api.locationWebSocketUrl(tripId, token);
      const ws = new WebSocket(connection.url);
      socket.current = ws;
      ws.onmessage = (raw) => {
        const event = JSON.parse(raw.data) as { type: string; data: CurrentLocation };
        if (event.type === "connected") setStatus("conectado");
        if (event.type === "location.updated") void updateContext();
        if (["location.paused", "location.stopped", "tracking.finished"].includes(event.type)) {
          if (event.type === "tracking.finished") stopWatch();
          void updateContext();
        }
      };
      ws.onclose = () => {
        if (socket.current === ws) socket.current = null;
        if (mounted.current) reconnect.current = window.setTimeout(() => { void updateContext(); void connectRef.current(); }, 2500);
      };
      ws.onerror = () => ws.close();
    } catch { if (mounted.current) reconnect.current = window.setTimeout(() => void connectRef.current(), 3000); }
  }, [stopWatch, token, tripId, updateContext]);

  const ensureSharing = useCallback(async () => {
    if (!token || configuring.current) return;
    configuring.current = true;
    try {
      let current = tracking;
      if (!current) current = await api.startTracking(tripId, token);
      if (!current.compartir_ubicacion) current = await api.shareLocation(tripId, true, token);
      setTracking(current);
    } finally { configuring.current = false; }
  }, [token, tracking, tripId]);

  function beginSharing() {
    if (!token || watch.current !== null) return;
    if (!navigator.geolocation) { setError("Este dispositivo no ofrece geolocalización."); setPermission("no disponible"); return; }
    setError("");
    watch.current = navigator.geolocation.watchPosition(async (position) => {
      setPermission("concedido");
      try { await ensureSharing(); } catch { setError("No se pudo activar el seguimiento para este viaje."); stopWatch(); return; }
      const now = Date.now();
      const previous = lastSent.current;
      if (previous && (now - previous.at < 4000 || (previous.latitude === position.coords.latitude && previous.longitude === position.coords.longitude))) return;
      lastSent.current = { at: now, latitude: position.coords.latitude, longitude: position.coords.longitude };
      const payload = { latitude: position.coords.latitude, longitude: position.coords.longitude, accuracy: position.coords.accuracy, speed: position.coords.speed, heading: position.coords.heading, client_timestamp: new Date(position.timestamp).toISOString(), sequence: ++sequence.current };
      if (socket.current?.readyState === WebSocket.OPEN) socket.current.send(JSON.stringify({ type: "location.update", data: payload }));
      else void api.sendLocation(tripId, payload, token).then(() => updateContext()).catch(() => setError("No se pudo enviar la ubicación."));
    }, (geoError) => {
      setPermission(geoError.code === geoError.PERMISSION_DENIED ? "denegado" : "no disponible");
      setError(geoError.code === geoError.PERMISSION_DENIED ? "El permiso de ubicación fue denegado." : "No se pudo obtener la ubicación del dispositivo.");
      stopWatch();
    }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 3000 });
    setWatching(true);
  }

  useEffect(() => {
    mounted.current = true; connectRef.current = connect;
    const timer = window.setTimeout(() => { if (token) { api.tracking(tripId, token).then(setTracking).catch(() => undefined); void updateContext(); void connect(); } }, 0);
    return () => { window.clearTimeout(timer); mounted.current = false; socket.current?.close(); stopWatch(); if (reconnect.current) window.clearTimeout(reconnect.current); };
  }, [connect, stopWatch, token, tripId, updateContext]);

  async function pause() { if (token) { stopWatch(); setTracking(await api.pauseTracking(tripId, token)); await updateContext(); } }
  async function resume() { if (token) { setTracking(await api.resumeTracking(tripId, token)); beginSharing(); } }
  async function stop() { if (token) { stopWatch(); setTracking(await api.shareLocation(tripId, false, token)); setContext(null); onContextChange?.(null); } }

  const location = context?.ubicacion ?? null;
  const markers = [
    ...(location ? [{ id: "driver", latitude: location.latitude, longitude: location.longitude, color: location.stale ? "#64748b" : "#047857", label: "Conductor" }] : []),
    ...(nextStop ? [{ id: "next", latitude: nextStop.latitude, longitude: nextStop.longitude, color: "#e87924", label: nextStop.label }] : []),
  ];
  return <section className="mobility-panel live-location" aria-live="polite">
    <header><div><p className="eyebrow">Ubicación como apoyo</p><h2 className="text-xl font-black">{location ? location.stale ? "Ubicación desactualizada" : "Ubicación del conductor" : "Aún sin ubicación compartida"}</h2></div><span className={status === "conectado" ? "badge-active" : "badge-pending"}>{status}</span></header>
    <MapView className="live-map" markers={markers} />
    {context?.estado === "disponible" && <div className="location-meta"><span><b>{context.distancia_texto}</b> hasta {context.parada_nombre}</span><span>Llegada aproximada {new Date(context.eta_aproximada!).toLocaleTimeString("es-PY", { hour: "2-digit", minute: "2-digit" })}</span></div>}
    {context?.estado === "error" && <p className="map-help">La ubicación está disponible, pero el proveedor de rutas no pudo calcular distancia y ETA.</p>}
    {context?.estado === "desactualizado" && <p className="map-help">Última posición desactualizada. La ETA se oculta hasta recibir una posición reciente.</p>}
    {location && <p className="map-help">Precisión {Math.round(location.accuracy)} m · última actualización {new Date(location.updated_at).toLocaleTimeString("es-PY")}</p>}
    {!location && <p className="map-help">El conductor debe consentir explícitamente compartir su ubicación.</p>}
    {error && <p className="error-message" role="alert">{error}</p>}
    {isDriver && <div className="tracking-controls"><span>Permiso: {permission}</span>{!watching && tracking?.estado !== "pausado" && <button className="button-primary" type="button" onClick={beginSharing}>Compartir ubicación</button>}{tracking?.estado === "activo" && tracking.compartir_ubicacion && <button className="button-secondary" type="button" onClick={() => void pause()}>Pausar ubicación</button>}{tracking?.estado === "pausado" && <button className="button-primary" type="button" onClick={() => void resume()}>Reanudar ubicación</button>}{tracking?.compartir_ubicacion && <button className="button-danger" type="button" onClick={() => void stop()}>Detener ubicación</button>}</div>}
    {nextStop && <a className="button-secondary inline-flex" href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${nextStop.latitude},${nextStop.longitude}`)}`} target="_blank" rel="noreferrer">Abrir navegación externa</a>}
  </section>;
}
