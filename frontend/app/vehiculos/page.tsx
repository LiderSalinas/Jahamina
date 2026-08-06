"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import type { Vehicle } from "@/lib/types";
import { PageContainer } from "@/components/ui/PageContainer";
import { AsyncState, PageHeader, SurfaceCard } from "@/components/ui/AppUI";

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
      <PageContainer className="page-stack">
        <PageHeader eyebrow="Conductor" title="Mis vehículos" description="Registrá los vehículos que usás para compartir tus viajes."/>
        <div className="split-layout">
          <form className="surface-card form-stack" onSubmit={submit}>
            <div><p className="eyebrow">Nuevo vehículo</p><h2 className="section-title">Agregar vehículo</h2></div>
            {error && <p className="error-message" role="alert">{error}</p>}
            {success && <p className="success-message">{success}</p>}
            <div className="form-grid">{["marca", "modelo", "color", "matricula"].map((field) => <div className="form-field" key={field}><label htmlFor={field}>{field === "matricula" ? "Matrícula" : field}</label><input id={field} name={field} autoComplete="off" required /></div>)}</div>
            <div className="form-field"><label htmlFor="capacidad">Capacidad de pasajeros</label><input id="capacidad" max={8} min={1} name="capacidad" type="number" required /></div>
            <button className="button-primary w-full" type="submit">Guardar vehículo</button>
          </form>
          <section>
            <h2 className="section-title">Vehículos registrados</h2>
            {loading ? <AsyncState kind="loading" title="Cargando vehículos…"/> : vehicles.length === 0 ? <AsyncState title="Todavía no registraste vehículos" description="Agregá uno para poder publicar un viaje."/> :
              <div className="vehicle-list">{vehicles.map((vehicle) => <SurfaceCard as="article" className="vehicle-card" key={vehicle.id}><div className="vehicle-symbol" aria-hidden>V</div><div className="vehicle-copy"><div className="vehicle-heading"><div><h3>{vehicle.marca} {vehicle.modelo}</h3><p>{vehicle.color} · {vehicle.matricula}</p></div><span className={vehicle.activo ? "badge-active" : "badge-cancelled"}>{vehicle.activo ? "Activo" : "Inactivo"}</span></div><p className="vehicle-capacity">Hasta {vehicle.capacidad} pasajeros</p>{vehicle.activo && <button className="button-secondary" onClick={() => disable(vehicle.id)} type="button">Desactivar</button>}</div></SurfaceCard>)}</div>}
          </section>
        </div>
      </PageContainer>
    </ProtectedRoute>
  );
}
