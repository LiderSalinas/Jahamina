"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useRef, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ApiError } from "@/lib/api";
import { PasswordField } from "@/components/ui/PasswordField";

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const submitting = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setError("");
    const form = new FormData(event.currentTarget);
    setLoading(true);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      const destination = params.get("next");
      router.push(destination?.startsWith("/") ? destination : "/viajes");
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        setError("Email o contraseña incorrectos.");
      } else if (caught instanceof ApiError && caught.status === 0) {
        setError("No se pudo conectar con Jahamina. Comprueba tu conexión e inténtalo nuevamente.");
      } else {
        setError(caught instanceof ApiError ? caught.message : "No se pudo iniciar sesión.");
      }
    } finally {
      submitting.current = false;
      setLoading(false);
    }
  }

  return (
    <form className="auth-card" method="post" onSubmit={submit}>
      <div>
        <span className="auth-mark" aria-hidden>J</span>
        <p className="eyebrow">Bienvenido de vuelta</p>
        <h1>Ingresá a Jahamina</h1>
        <p className="auth-intro">Tus viajes, reservas y conversaciones están en un solo lugar.</p>
      </div>
      {params.get("registered") && <p className="success-message">Cuenta creada. Ya podés ingresar.</p>}
      {error && <p className="error-message" role="alert">{error}</p>}
      <div className="form-field">
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" autoComplete="email" required />
      </div>
      <PasswordField id="password" name="password" autoComplete="current-password" required />
      <button className="button-primary w-full" disabled={loading} type="submit">
        {loading ? "Ingresando…" : "Ingresar"}
      </button>
      <p className="auth-switch">
        ¿Todavía no tenés cuenta? <Link className="font-bold" href="/registro">Registrate</Link>
      </p>
    </form>
  );
}

export default function LoginPage() {
  return (
    <section className="auth-page">
      <Suspense fallback={<div className="async-state">Preparando Jahamina…</div>}>
        <LoginForm />
      </Suspense>
    </section>
  );
}
