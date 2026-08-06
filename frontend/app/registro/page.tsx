"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { PasswordField } from "@/components/ui/PasswordField";

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
    <section className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <div>
          <span className="auth-mark" aria-hidden>J</span>
          <p className="eyebrow">Sumate a la comunidad</p>
          <h1>Creá tu cuenta</h1>
          <p className="auth-intro">Empezá a compartir trayectos dentro de Paraguay.</p>
        </div>
        {error && <p className="error-message" role="alert">{error}</p>}
        <div className="form-field">
          <label htmlFor="nombre">Nombre</label>
          <input id="nombre" name="nombre" autoComplete="name" minLength={2} maxLength={100} required />
        </div>
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input id="email" name="email" type="email" autoComplete="email" required />
        </div>
        <PasswordField id="password" name="password" autoComplete="new-password" minLength={8} maxLength={72} required />
        <small className="field-help">Usá entre 8 y 72 caracteres.</small>
        <button className="button-primary w-full" disabled={loading} type="submit">
          {loading ? "Creando…" : "Registrarme"}
        </button>
        <p className="auth-switch">
          ¿Ya tenés cuenta? <Link className="font-bold" href="/login">Ingresá</Link>
        </p>
      </form>
    </section>
  );
}
