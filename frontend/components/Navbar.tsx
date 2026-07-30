"use client";

import Link from "next/link";

import { useAuth } from "@/components/AuthProvider";

export function Navbar() {
  const { user, loading, logout } = useAuth();
  return (
    <header className="border-b border-emerald-900/10 bg-white/90 backdrop-blur">
      <nav className="container flex min-h-16 items-center justify-between gap-4">
        <Link href="/" className="text-xl font-black tracking-tight text-emerald-800">
          Jaha<span className="text-amber-500">mina</span>
        </Link>
        <div className="flex flex-wrap items-center justify-end gap-3 text-sm font-semibold">
          {!loading && user ? (
            <>
              <Link href="/viajes">Viajes</Link>
              <Link href="/vehiculos">Vehículos</Link>
              <Link href="/reservas">Reservas</Link>
              <Link href="/mis-viajes">Mis viajes</Link>
              <Link href="/perfil">Perfil</Link>
              <button className="button-secondary" onClick={logout} type="button">
                Salir
              </button>
            </>
          ) : (
            <>
              <Link href="/login">Ingresar</Link>
              <Link className="button-primary" href="/registro">
                Crear cuenta
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
