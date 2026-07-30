"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { ApiError } from "@/lib/api";

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    setLoading(true);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      const destination = params.get("next");
      router.push(destination?.startsWith("/") ? destination : "/viajes");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="form-card w-full max-w-md space-y-5" onSubmit={submit}>
      <div>
        <p className="eyebrow">Bienvenido de vuelta</p>
        <h1 className="mt-2 text-3xl font-black">Ingresar</h1>
      </div>
      {params.get("registered") && <p className="success-message">Cuenta creada. Ya podés ingresar.</p>}
      {error && <p className="error-message" role="alert">{error}</p>}
      <div className="form-field">
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" required />
      </div>
      <div className="form-field">
        <label htmlFor="password">Contraseña</label>
        <input id="password" name="password" type="password" required />
      </div>
      <button className="button-primary w-full" disabled={loading} type="submit">
        {loading ? "Ingresando…" : "Ingresar"}
      </button>
      <p className="text-center text-sm text-slate-600">
        ¿Todavía no tenés cuenta? <Link className="font-bold" href="/registro">Registrate</Link>
      </p>
    </form>
  );
}

export default function LoginPage() {
  return (
    <section className="container grid min-h-[calc(100vh-4rem)] place-items-center py-12">
      <Suspense fallback={<div className="status-card">Cargando…</div>}>
        <LoginForm />
      </Suspense>
    </section>
  );
}
