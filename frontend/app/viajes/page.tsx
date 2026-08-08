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

function localDateOffset(days: number) {
  const value = new Date();
  value.setDate(value.getDate() + days);
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
}

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
    try { setTrips(await api.availableTrips(token)); }
    catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) logout();
      else setError(caught instanceof ApiError ? caught.message : "No pudimos cargar los viajes.");
    } finally { setLoading(false); }
  }, [logout, token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function join(id: number) {
    if (!token) return;
    setBusyId(id); setError("");
    try { await api.createRequest(id, {}, token); setTrips((current) => current.filter((trip) => trip.id !== id)); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "No pudimos solicitar este lugar."); }
    finally { setBusyId(null); }
  }

  const search = query.trim().toLocaleLowerCase("es-PY");
  const filtered = trips.filter((trip) => {
    const matchesText = !search || `${trip.origen} ${trip.destino}`.toLocaleLowerCase("es-PY").includes(search);
    return matchesText && (!date || trip.fecha.slice(0, 10) === date);
  });
  const clearFilters = () => { setQuery(""); setDate(""); };

  return <ProtectedRoute><PageContainer className="page-stack trips-explore-page">
    <PageHeader eyebrow="VIAJES" title="Encontrá tu próximo viaje" description="Explorá trayectos disponibles y elegí el que mejor se adapte a vos." action={<Link className="button-primary" href="/viajes/nuevo">Publicar viaje</Link>} />
    <section className="trip-search-panel" aria-label="Buscar viajes">
      <form className="trip-search-main" role="search" onSubmit={(event) => { event.preventDefault(); setQuery((value) => value.trim()); }}>
        <div className="form-field"><label htmlFor="trip-search">Origen o destino</label><div className="search-input-wrap"><span aria-hidden>⌕</span><input id="trip-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ej. Asunción, Ayolas…" /></div></div>
        <div className="form-field"><label htmlFor="trip-date">Fecha</label><input id="trip-date" type="date" value={date} onChange={(event) => setDate(event.target.value)} /></div>
        <button className="button-primary trip-search-button" type="submit">Buscar viajes</button>
      </form>
      <div className="trip-quick-filters" aria-label="Fechas rápidas"><span>Ver:</span><button className={date === localDateOffset(0) ? "is-active" : ""} onClick={() => setDate(localDateOffset(0))} type="button">Hoy</button><button className={date === localDateOffset(1) ? "is-active" : ""} onClick={() => setDate(localDateOffset(1))} type="button">Mañana</button><button className={!date ? "is-active" : ""} onClick={() => setDate("")} type="button">Próximos días</button>{(query || date) && <button className="trip-clear-filter" type="button" onClick={clearFilters}>Limpiar filtros</button>}</div>
    </section>
    {error && <p className="error-message" role="alert">{error}</p>}
    {loading ? <AsyncState kind="loading" title="Buscando viajes…" description="Estamos preparando los trayectos disponibles." /> : filtered.length === 0 ? <AsyncState icon="⌕" title="No encontramos viajes con esos filtros" description="Probá otro origen, destino o fecha." action={(query || date) ? <button className="button-secondary" type="button" onClick={clearFilters}>Limpiar filtros</button> : undefined} /> : <div className="card-grid trips-results-grid">{filtered.map((trip) => <TripCard actionLabel="Solicitar lugar" busy={busyId === trip.id} key={trip.id} onAction={() => void join(trip.id)} trip={trip} />)}</div>}
  </PageContainer></ProtectedRoute>;
}
