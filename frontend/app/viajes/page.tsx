"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { TripCard } from "@/components/TripCard";
import { api, ApiError } from "@/lib/api";
import type { Trip } from "@/lib/types";
import { PageContainer } from "@/components/ui/PageContainer";
import { AsyncState, PageHeader } from "@/components/ui/AppUI";

export default function TripsPage() {
  const { token, logout } = useAuth();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [date, setDate] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setTrips(await api.availableTrips(token));
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) logout();
      else setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    } finally {
      setLoading(false);
    }
  }, [logout, token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function join(id: number) {
    if (!token) return;
    setBusyId(id);
    setError("");
    try {
      await api.createRequest(id, {}, token);
      setTrips((current) => current.filter((trip) => trip.id !== id));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    } finally {
      setBusyId(null);
    }
  }

  const filtered = trips.filter((trip) => {
    const search = query.trim().toLocaleLowerCase("es-PY");
    const matchesText = !search || `${trip.origen} ${trip.destino}`.toLocaleLowerCase("es-PY").includes(search);
    return matchesText && (!date || trip.fecha.slice(0, 10) === date);
  });
  return (
    <ProtectedRoute>
      <PageContainer className="page-stack">
        <PageHeader eyebrow="Explorá Paraguay" title="Viajes disponibles" description="Encontrá un trayecto que coincida con tu camino." action={<Link className="button-primary" href="/viajes/nuevo">Publicar viaje</Link>}/>
        <div className="filter-bar" role="search"><div className="form-field"><label htmlFor="trip-search">Origen o destino</label><input id="trip-search" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar origen o destino en Paraguay"/></div><div className="form-field"><label htmlFor="trip-date">Fecha</label><input id="trip-date" type="date" value={date} onChange={event => setDate(event.target.value)}/></div>{(query || date) && <button className="button-secondary" type="button" onClick={() => { setQuery(""); setDate(""); }}>Limpiar filtros</button>}</div>
        {error && <p className="error-message mt-6" role="alert">{error}</p>}
        {loading ? <AsyncState kind="loading" title="Buscando viajes…" description="Esto puede tardar unos segundos."/> :
          filtered.length === 0 ? <AsyncState icon="J" title="No encontramos viajes para esta búsqueda" description="Probá con otra fecha o publicá tu propio trayecto desde la acción superior."/> :
          <div className="card-grid">
            {filtered.map((trip) => <TripCard actionLabel="Solicitar lugar" busy={busyId === trip.id} key={trip.id} onAction={() => join(trip.id)} trip={trip} />)}
          </div>}
      </PageContainer>
    </ProtectedRoute>
  );
}
