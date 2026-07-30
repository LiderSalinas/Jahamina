"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { TripCard } from "@/components/TripCard";
import { api, ApiError } from "@/lib/api";
import type { Trip } from "@/lib/types";

export default function TripsPage() {
  const { token, logout } = useAuth();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

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

  return (
    <ProtectedRoute>
      <section className="container py-12">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div><p className="eyebrow">Explorá</p><h1 className="mt-2 text-4xl font-black">Viajes disponibles</h1></div>
          <Link className="button-primary" href="/viajes/nuevo">Publicar viaje</Link>
        </div>
        {error && <p className="error-message mt-6" role="alert">{error}</p>}
        {loading ? <div className="status-card mt-8">Buscando viajes…</div> :
          trips.length === 0 ? <div className="status-card mt-8"><h2 className="text-xl font-bold">Todavía no hay viajes disponibles</h2><p className="mt-2 text-slate-600">Podés publicar el primero o volver más tarde.</p></div> :
          <div className="mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {trips.map((trip) => <TripCard actionLabel="Solicitar lugar" busy={busyId === trip.id} key={trip.id} onAction={() => join(trip.id)} trip={trip} />)}
          </div>}
      </section>
    </ProtectedRoute>
  );
}
