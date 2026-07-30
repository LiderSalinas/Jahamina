"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api, ApiError } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    setLoading(true);
    try {
      await api.register({
        nombre: String(form.get("nombre")),
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      router.push("/login?registered=1");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="container grid min-h-[calc(100vh-4rem)] place-items-center py-12">
      <form className="form-card w-full max-w-md space-y-5" onSubmit={submit}>
        <div>
          <p className="eyebrow">Nueva comunidad</p>
          <h1 className="mt-2 text-3xl font-black">Crear cuenta</h1>
        </div>
        {error && <p className="error-message" role="alert">{error}</p>}
        <div className="form-field">
          <label htmlFor="nombre">Nombre</label>
          <input id="nombre" name="nombre" minLength={2} maxLength={100} required />
        </div>
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input id="email" name="email" type="email" required />
        </div>
        <div className="form-field">
          <label htmlFor="password">Contraseña</label>
          <input id="password" name="password" type="password" minLength={8} maxLength={72} required />
          <small className="text-slate-500">Entre 8 caracteres y 72 bytes.</small>
        </div>
        <button className="button-primary w-full" disabled={loading} type="submit">
          {loading ? "Creando…" : "Registrarme"}
        </button>
        <p className="text-center text-sm text-slate-600">
          ¿Ya tenés cuenta? <Link className="font-bold" href="/login">Ingresá</Link>
        </p>
      </form>
    </section>
  );
}
