"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { GeoPoint } from "@/lib/types";
import { MapErrorState } from "./MapErrorState";
import { MapLoadingState } from "./MapLoadingState";
import { isWithinParaguay, PARAGUAY_BOUNDS, PARAGUAY_CENTER } from "@/lib/paraguayGeo";

const DEFAULT_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";
const MAP_ERROR_MESSAGE = "No se pudo cargar el mapa. El punto de encuentro continúa disponible.";

export interface MapMarker extends GeoPoint {
  id: string;
  color?: string;
  label?: string;
  draggable?: boolean;
}

interface MapViewProps {
  markers: MapMarker[];
  route?: GeoPoint[];
  onMarkerMove?: (id: string, point: GeoPoint) => void;
  onInvalidPoint?: () => void;
  className?: string;
}

function validPoint(point: GeoPoint | undefined): point is GeoPoint {
  return Boolean(
    point
      && Number.isFinite(point.latitude)
      && Number.isFinite(point.longitude)
      && isWithinParaguay(point),
  );
}

function configuredStyleUrl(): { url: string | null; usingFallback: boolean } {
  const configured = process.env.NEXT_PUBLIC_MAP_STYLE_URL?.trim();
  if (configured) {
    try {
      const url = new URL(configured);
      if (url.protocol === "https:" || (process.env.NODE_ENV === "development" && url.protocol === "http:")) {
        return { url: configured, usingFallback: false };
      }
    } catch {
      // The UI below reports invalid public configuration without printing it.
    }
    return { url: null, usingFallback: false };
  }
  return { url: DEFAULT_STYLE_URL, usingFallback: true };
}

export function MapView({ markers, route, onMarkerMove, onInvalidPoint, className = "" }: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<import("maplibre-gl").Map | null>(null);
  const maplibreRef = useRef<typeof import("maplibre-gl") | null>(null);
  const markerInstances = useRef<import("maplibre-gl").Marker[]>([]);
  const hasLoadedRef = useRef(false);
  const lastAutomaticCameraRef = useRef("");
  const callbackRef = useRef(onMarkerMove);
  const invalidCallbackRef = useRef(onInvalidPoint);
  const style = useMemo(() => configuredStyleUrl(), []);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(() => style.url ? "" : MAP_ERROR_MESSAGE);
  const validMarkers = useMemo(() => markers.filter(validPoint), [markers]);
  const validRoute = useMemo(() => route?.filter(validPoint) ?? [], [route]);
  const selectionSignature = useMemo(
    () => validMarkers.map((point) => `${point.id}:${point.latitude.toFixed(6)},${point.longitude.toFixed(6)}`).join("|"),
    [validMarkers],
  );

  useEffect(() => { callbackRef.current = onMarkerMove; }, [onMarkerMove]);
  useEffect(() => { invalidCallbackRef.current = onInvalidPoint; }, [onInvalidPoint]);

  const fitContent = useCallback(() => {
    const map = mapRef.current;
    const maplibre = maplibreRef.current;
    if (!map || !maplibre) return;
    const points = validRoute.length >= 2 ? validRoute : validMarkers;
    if (points.length === 0) {
      map.fitBounds(PARAGUAY_BOUNDS, { padding: 28, duration: 0 });
      return;
    }
    if (points.length === 1) {
      map.easeTo({ center: [points[0].longitude, points[0].latitude], zoom: 14, duration: 650 });
      return;
    }
    const bounds = new maplibre.LngLatBounds();
    points.forEach((point) => bounds.extend([point.longitude, point.latitude]));
    map.fitBounds(bounds, { padding: 55, maxZoom: 15, duration: 650 });
  }, [validMarkers, validRoute]);

  useEffect(() => {
    const styleUrl = style.url;
    if (!container.current || !styleUrl || mapRef.current) return;
    let disposed = false;
    if (style.usingFallback && process.env.NODE_ENV === "development") {
      console.info("Mapa: NEXT_PUBLIC_MAP_STYLE_URL no está configurada; se usa el estilo público de desarrollo.");
    }
    void import("maplibre-gl").then((maplibre) => {
      if (disposed || !container.current || mapRef.current) return;
      maplibreRef.current = maplibre;
      const defaultLatitude = Number(process.env.NEXT_PUBLIC_DEFAULT_LATITUDE ?? -25.2867);
      const defaultLongitude = Number(process.env.NEXT_PUBLIC_DEFAULT_LONGITUDE ?? -57.3333);
      const first = validPoint({ latitude: defaultLatitude, longitude: defaultLongitude })
        ? { latitude: defaultLatitude, longitude: defaultLongitude }
        : { latitude: PARAGUAY_CENTER[1], longitude: PARAGUAY_CENTER[0] };
      const map = new maplibre.Map({
        container: container.current,
        style: styleUrl,
        center: [first.longitude, first.latitude],
        zoom: Number(process.env.NEXT_PUBLIC_DEFAULT_ZOOM ?? 11),
        minZoom: 5,
        maxBounds: PARAGUAY_BOUNDS,
        attributionControl: {},
      });
      mapRef.current = map;
      map.addControl(new maplibre.NavigationControl({ showCompass: false }), "top-right");
      map.on("load", () => {
        if (disposed) return;
        hasLoadedRef.current = true;
        setLoaded(true);
        setError("");
        map.resize();
        map.fitBounds(PARAGUAY_BOUNDS, { padding: 28, duration: 0 });
      });
      map.on("error", (event) => {
        if (disposed) return;
        if (!hasLoadedRef.current) {
          setLoaded(false);
          setError(MAP_ERROR_MESSAGE);
        }
        if (process.env.NODE_ENV === "development") {
          console.warn("Mapa: falló la carga del estilo o de uno de sus recursos.", event.error?.name ?? "MapError");
        }
      });
    }).catch(() => setError(MAP_ERROR_MESSAGE));
    return () => {
      disposed = true;
      markerInstances.current.forEach((marker) => marker.remove());
      markerInstances.current = [];
      mapRef.current?.remove();
      mapRef.current = null;
      maplibreRef.current = null;
      hasLoadedRef.current = false;
    };
    // Map construction depends only on the validated style, preventing duplicate Strict Mode instances.
  }, [style.url, style.usingFallback]);

  useEffect(() => {
    const map = mapRef.current;
    const maplibre = maplibreRef.current;
    if (!map || !maplibre || !loaded) return;
    markerInstances.current.forEach((marker) => marker.remove());
    markerInstances.current = validMarkers.map((item) => {
      const element = document.createElement("span");
      element.className = `jahamina-map-marker is-${item.id}`;
      element.setAttribute("aria-hidden", "true");
      element.style.setProperty("--marker-color", item.color ?? "#075b49");
      const core = document.createElement("span");
      element.appendChild(core);
      const marker = new maplibre.Marker({ element, draggable: item.draggable })
        .setLngLat([item.longitude, item.latitude])
        .addTo(map);
      if (item.label) marker.setPopup(new maplibre.Popup({ offset: 20 }).setText(item.label));
      if (item.draggable) marker.on("dragend", () => {
        const point = marker.getLngLat();
        const next = { latitude: point.lat, longitude: point.lng };
        if (!isWithinParaguay(next)) {
          marker.setLngLat([item.longitude, item.latitude]);
          invalidCallbackRef.current?.();
          return;
        }
        callbackRef.current?.(item.id, next);
      });
      return marker;
    });

    if (map.getLayer("route")) map.removeLayer("route");
    if (map.getLayer("route-shadow")) map.removeLayer("route-shadow");
    if (map.getSource("route")) map.removeSource("route");
    if (validRoute.length >= 2) {
      map.addSource("route", { type: "geojson", data: { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: validRoute.map((point) => [point.longitude, point.latitude]) } } });
      map.addLayer({ id: "route-shadow", type: "line", source: "route", layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": "#d7e9e0", "line-width": 10, "line-opacity": 0.88 } });
      map.addLayer({ id: "route", type: "line", source: "route", layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": "#075b49", "line-width": 5.5, "line-opacity": 0.96 } });
    }
    if (selectionSignature !== lastAutomaticCameraRef.current) {
      lastAutomaticCameraRef.current = selectionSignature;
      fitContent();
    }
  }, [fitContent, loaded, selectionSignature, validMarkers, validRoute]);

  return (
    <div className={`map-container ${className}`}>
      {!loaded && !error && <MapLoadingState />}
      <div className={`map-view ${loaded && !error ? "is-loaded" : ""}`} ref={container} role="application" aria-label="Mapa interactivo" />
      {error && <MapErrorState message={error} />}
      {loaded && !error && validMarkers.length > 0 && (
        <button className="map-recenter" type="button" onClick={fitContent} aria-label="Centrar nuevamente el mapa">
          Centrar recorrido
        </button>
      )}
    </div>
  );
}
