"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import type { Vehicle } from "@/lib/types";

export default function NewTripPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    const timer = window.setTimeout(() => {
      api.vehicles(token)
        .then((items) => setVehicles(items.filter((item) => item.activo)))
        .catch((caught) => setError(caught instanceof ApiError ? caught.message : "No se pudieron cargar los vehículos."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [token]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setError("");
    const form = new FormData(event.currentTarget);
    setLoading(true);
    try {
      await api.createTrip({
        origen: String(form.get("origen")),
        destino: String(form.get("destino")),
        fecha: new Date(String(form.get("fecha"))).toISOString(),
        vehiculo_id: Number(form.get("vehiculo_id")),
        cupos_totales: Number(form.get("cupos_totales")),
        descripcion: String(form.get("descripcion") || ""),
        punto_salida: String(form.get("punto_salida")),
        punto_llegada: String(form.get("punto_llegada")),
      }, token);
      router.push("/mis-viajes?created=1");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ProtectedRoute>
      <section className="container grid min-h-[calc(100vh-4rem)] place-items-center py-12">
        <form className="form-card w-full max-w-2xl space-y-5" onSubmit={submit}>
          <div><p className="eyebrow">Compartí tu trayecto</p><h1 className="mt-2 text-3xl font-black">Nuevo viaje</h1></div>
          {error && <p className="error-message" role="alert">{error}</p>}
          {vehicles.length === 0 && <p className="status-card">Necesitás un vehículo activo. Crealo en Mis vehículos.</p>}
          <div className="grid gap-5 md:grid-cols-2">
            <div className="form-field"><label htmlFor="origen">Ciudad de origen</label><input id="origen" name="origen" minLength={2} maxLength={150} required /></div>
            <div className="form-field"><label htmlFor="destino">Ciudad de destino</label><input id="destino" name="destino" minLength={2} maxLength={150} required /></div>
            <div className="form-field"><label htmlFor="punto_salida">Punto de salida</label><input id="punto_salida" name="punto_salida" maxLength={200} required /></div>
            <div className="form-field"><label htmlFor="punto_llegada">Punto de llegada</label><input id="punto_llegada" name="punto_llegada" maxLength={200} required /></div>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            <div className="form-field md:col-span-2"><label htmlFor="fecha">Fecha y hora</label><input id="fecha" min={new Date().toISOString().slice(0, 16)} name="fecha" type="datetime-local" required /></div>
            <div className="form-field"><label htmlFor="cupos_totales">Cupos</label><input id="cupos_totales" min={1} max={8} name="cupos_totales" type="number" required /></div>
          </div>
          <div className="form-field">
            <label htmlFor="vehiculo_id">Vehículo</label>
            <select className="min-h-11 rounded-xl border border-slate-300 bg-white px-3" id="vehiculo_id" name="vehiculo_id" required>
              <option value="">Seleccioná un vehículo</option>
              {vehicles.map((vehicle) => <option key={vehicle.id} value={vehicle.id}>{vehicle.marca} {vehicle.modelo} · {vehicle.matricula} · {vehicle.capacidad} lugares</option>)}
            </select>
          </div>
          <div className="form-field"><label htmlFor="descripcion">Descripción opcional</label><textarea className="min-h-28 rounded-xl border border-slate-300 p-3" id="descripcion" maxLength={1000} name="descripcion" /></div>
          <button className="button-primary w-full" disabled={loading || vehicles.length === 0} type="submit">{loading ? "Publicando…" : "Publicar viaje"}</button>
        </form>
      </section>
    </ProtectedRoute>
  );
}
