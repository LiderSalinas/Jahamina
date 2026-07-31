"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { UnreadBadge } from "@/components/chat/UnreadBadge";
import { api } from "@/lib/api";
import type { UnreadSummary } from "@/lib/types";

export function Navbar() {
  const { user, token, loading, logout } = useAuth();
  const [unread, setUnread] = useState<UnreadSummary>({
    total: 0,
    conversaciones: [],
  });
  useEffect(() => {
    if (!token) return;
    const refresh = () => api.unreadChats(token).then(setUnread).catch(() => undefined);
    refresh();
    const timer = window.setInterval(refresh, 10000);
    window.addEventListener("jahamina:unread-changed", refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("jahamina:unread-changed", refresh);
    };
  }, [token]);
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
              <Link className="nav-with-badge" href={unread.conversaciones[0] ? `/reservas/${unread.conversaciones[0].solicitud_id}` : "/reservas"}>Reservas<UnreadBadge count={token ? unread.total : 0} /></Link>
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
