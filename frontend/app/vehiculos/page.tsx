"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import type { Vehicle } from "@/lib/types";

export default function VehiclesPage() {
  const { token } = useAuth();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    try { setVehicles(await api.vehicles(token)); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Error inesperado."); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    setError(""); setSuccess("");
    try {
      await api.createVehicle({
        marca: String(form.get("marca")),
        modelo: String(form.get("modelo")),
        color: String(form.get("color")),
        matricula: String(form.get("matricula")),
        capacidad: Number(form.get("capacidad")),
      }, token);
      event.currentTarget.reset();
      setSuccess("Vehículo registrado correctamente.");
      await load();
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : "Error inesperado."); }
  }

  async function disable(id: number) {
    if (!token || !window.confirm("¿Desactivar este vehículo? No podrá usarse en nuevos viajes.")) return;
    try { await api.disableVehicle(id, token); await load(); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Error inesperado."); }
  }

  return (
    <ProtectedRoute>
      <section className="container py-12">
        <p className="eyebrow">Conductor</p><h1 className="mt-2 text-4xl font-black">Mis vehículos</h1>
        <div className="mt-8 grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <form className="form-card space-y-4" onSubmit={submit}>
            <h2 className="text-xl font-black">Agregar vehículo</h2>
            {error && <p className="error-message" role="alert">{error}</p>}
            {success && <p className="success-message">{success}</p>}
            {["marca", "modelo", "color", "matricula"].map((field) => <div className="form-field" key={field}><label htmlFor={field}>{field === "matricula" ? "Matrícula" : field}</label><input id={field} name={field} required /></div>)}
            <div className="form-field"><label htmlFor="capacidad">Capacidad de pasajeros</label><input id="capacidad" max={8} min={1} name="capacidad" type="number" required /></div>
            <button className="button-primary w-full" type="submit">Guardar vehículo</button>
          </form>
          <div>
            <h2 className="text-xl font-black">Vehículos registrados</h2>
            {loading ? <div className="status-card mt-4">Cargando…</div> : vehicles.length === 0 ? <div className="status-card mt-4">No registraste vehículos.</div> :
              <div className="mt-4 grid gap-4">{vehicles.map((vehicle) => <article className="trip-card" key={vehicle.id}><div className="flex items-start justify-between gap-4"><div><h3 className="text-lg font-black">{vehicle.marca} {vehicle.modelo}</h3><p className="mt-1 text-slate-600">{vehicle.color} · {vehicle.matricula}</p><p className="mt-2 text-sm font-semibold">{vehicle.capacidad} pasajeros</p></div><span className={vehicle.activo ? "badge-active" : "badge-cancelled"}>{vehicle.activo ? "Activo" : "Inactivo"}</span></div>{vehicle.activo && <button className="button-secondary mt-4" onClick={() => disable(vehicle.id)} type="button">Desactivar</button>}</article>)}</div>}
          </div>
        </div>
      </section>
    </ProtectedRoute>
  );
}
