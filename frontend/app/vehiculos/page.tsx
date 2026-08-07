"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import type { Vehicle } from "@/lib/types";
import { PageContainer } from "@/components/ui/PageContainer";
import { AsyncState, PageHeader, SurfaceCard } from "@/components/ui/AppUI";
import { ImageUploadControl } from "@/components/media/ImageUploadControl";
import { VehicleImage } from "@/components/trip-roadmap/VehicleImage";

function vehicleError(caught: unknown): string {
  if (!(caught instanceof ApiError)) return "No pudimos completar la operación.";
  if (caught.status === 0) return "No pudimos conectar con el servidor.";
  if (caught.status === 401) return "Tu sesión venció. Volvé a iniciar sesión.";
  if (caught.status === 403) return "No tenés permiso para realizar esta acción.";
  if (caught.status === 409) return "La matrícula ya está registrada.";
  if (caught.status === 422) return caught.message;
  if (caught.status >= 500) return "El servidor no pudo completar la operación. Intentá nuevamente.";
  return caught.message;
}

export default function VehiclesPage() {
  const { token } = useAuth();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [listError, setListError] = useState("");
  const [uploadingVehicle, setUploadingVehicle] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setListError("");
    try { setVehicles(await api.vehicles(token)); }
    catch (caught) { setListError(vehicleError(caught)); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || submitting) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setError(""); setSuccess(""); setSubmitting(true);
    let created: Vehicle;
    try {
      created = await api.createVehicle({
        marca: String(form.get("marca")),
        modelo: String(form.get("modelo")),
        color: String(form.get("color")),
        matricula: String(form.get("matricula")),
        capacidad: Number(form.get("capacidad")),
      }, token);
    } catch (caught) {
      setError(vehicleError(caught));
      setSubmitting(false);
      return;
    }

    formElement.reset();
    setSuccess("Vehículo registrado correctamente.");
    setVehicles((current) => current.some((vehicle) => vehicle.id === created.id) ? current : [created, ...current]);

    try {
      setVehicles(await api.vehicles(token));
      setListError("");
    } catch {
      setListError("El vehículo se registró, pero no pudimos actualizar la lista.");
    } finally {
      setLoading(false);
      setSubmitting(false);
    }
  }

  async function disable(id: number) {
    if (!token || !window.confirm("¿Desactivar este vehículo? No podrá usarse en nuevos viajes.")) return;
    try { await api.disableVehicle(id, token); await load(); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Error inesperado."); }
  }

  async function uploadImage(vehicle: Vehicle, file: File) {
    if (!token) return;
    setUploadingVehicle(vehicle.id);
    try { const updated = await api.uploadVehicleImage(vehicle.id, file, token); setVehicles((current) => current.map((item) => item.id === updated.id ? updated : item)); }
    finally { setUploadingVehicle(null); }
  }

  async function deleteImage(vehicle: Vehicle) {
    if (!token) return;
    setUploadingVehicle(vehicle.id);
    try { const updated = await api.deleteVehicleImage(vehicle.id, token); setVehicles((current) => current.map((item) => item.id === updated.id ? updated : item)); }
    finally { setUploadingVehicle(null); }
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
            <button className="button-primary w-full" disabled={submitting} type="submit">{submitting ? "Guardando…" : "Guardar vehículo"}</button>
          </form>
          <section>
            <h2 className="section-title">Vehículos registrados</h2>
            {listError && <div className="error-message mt-4" role="alert"><span>{listError}</span><button className="button-secondary ml-3" type="button" onClick={() => void load()}>Reintentar lista</button></div>}
            {loading ? <AsyncState kind="loading" title="Cargando vehículos…"/> : vehicles.length === 0 ? <AsyncState title="Todavía no registraste vehículos" description="Agregá uno para poder publicar un viaje."/> :
              <div className="vehicle-list">{vehicles.map((vehicle) => <SurfaceCard as="article" className="vehicle-card vehicle-photo-card" key={vehicle.id}><VehicleImage brand={vehicle.marca} model={vehicle.modelo} color={vehicle.color} registration={vehicle.matricula} imageUrl={vehicle.imagen_url}/><div className="vehicle-copy"><div className="vehicle-heading"><div><h3>{vehicle.marca} {vehicle.modelo}</h3><p>{vehicle.color} · {vehicle.matricula}</p></div><span className={vehicle.activo ? "badge-active" : "badge-cancelled"}>{vehicle.activo ? "Activo" : "Inactivo"}</span></div><p className="vehicle-capacity">Hasta {vehicle.capacidad} pasajeros</p><ImageUploadControl hasImage={Boolean(vehicle.imagen_url)} uploading={uploadingVehicle === vehicle.id} onUpload={(file) => uploadImage(vehicle, file)} onDelete={() => deleteImage(vehicle)} description="Una foto clara ayuda a que los pasajeros reconozcan tu vehículo."/>{vehicle.activo && <button className="button-secondary vehicle-disable" onClick={() => disable(vehicle.id)} type="button">Desactivar</button>}</div></SurfaceCard>)}</div>}
          </section>
        </div>
      </PageContainer>
    </ProtectedRoute>
  );
}
