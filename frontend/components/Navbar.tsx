"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { UnreadBadge } from "@/components/chat/UnreadBadge";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { UserAvatar } from "@/components/ui/UserAvatar";
import { api } from "@/lib/api";
import type { UnreadSummary } from "@/lib/types";

const links = [
  ["Viajes", "/viajes", "⌕"],
  ["Reservas", "/reservas", "▣"],
  ["Mis viajes", "/mis-viajes", "↗"],
  ["Perfil", "/perfil", "♙"],
] as const;

export function Navbar() {
  const { user, token, loading, logout } = useAuth();
  const pathname = usePathname();
  const [accountOpen, setAccountOpen] = useState(false);
  const accountRef = useRef<HTMLDivElement | null>(null);
  const [unread, setUnread] = useState<UnreadSummary>({ total: 0, conversaciones: [] });

  useEffect(() => {
    if (!token) return;
    const refresh = () => api.unreadChats(token).then(setUnread).catch(() => undefined);
    refresh();
    const timer = window.setInterval(refresh, 10000);
    window.addEventListener("jahamina:unread-changed", refresh);
    return () => { window.clearInterval(timer); window.removeEventListener("jahamina:unread-changed", refresh); };
  }, [token]);

  useEffect(() => {
    if (!accountOpen) return;
    const closeWithEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setAccountOpen(false); };
    const closeOutside = (event: PointerEvent) => { if (!accountRef.current?.contains(event.target as Node)) setAccountOpen(false); };
    document.addEventListener("keydown", closeWithEscape);
    document.addEventListener("pointerdown", closeOutside);
    return () => { document.removeEventListener("keydown", closeWithEscape); document.removeEventListener("pointerdown", closeOutside); };
  }, [accountOpen]);

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
  const closeAccount = () => setAccountOpen(false);

  return <header className="app-header">
    <nav className="app-header-inner" aria-label="Navegación principal">
      <Link href="/" className="brand" onClick={closeAccount}><span className="brand-mark" aria-hidden="true">J</span><span><b>Jaha<em>mina</em></b><small>Vamos juntos</small></span></Link>
      {!loading && user ? <>
        <div className="desktop-navigation">{links.map(([label, href, icon]) => <Link key={href} href={href} aria-current={isActive(href) ? "page" : undefined} className={isActive(href) ? "is-active" : ""}><span aria-hidden>{icon}</span>{label}{href === "/reservas" && <UnreadBadge count={unread.total} />}</Link>)}</div>
        <div className="header-actions" ref={accountRef}>
          {token && <NotificationBell token={token} />}
          <button className="account-trigger" type="button" aria-label="Abrir menú de cuenta" aria-expanded={accountOpen} aria-controls="account-navigation" onClick={() => setAccountOpen((value) => !value)}><UserAvatar name={user.nombre} imageUrl={user.imagen_url} size="sm" /><span className="account-copy"><b>{user.nombre}</b><small>Mi cuenta</small></span><span aria-hidden="true">⌄</span></button>
          {accountOpen && <div className="account-menu" id="account-navigation"><Link href="/perfil" onClick={closeAccount}>Mi perfil</Link><Link href="/vehiculos" onClick={closeAccount}>Mis vehículos</Link><button type="button" onClick={() => { closeAccount(); logout(); }}>Cerrar sesión</button></div>}
        </div>
        <div className="mobile-bottom-nav" aria-label="Navegación móvil">{links.map(([label, href, icon]) => <Link key={href} href={href} aria-current={isActive(href) ? "page" : undefined} className={isActive(href) ? "is-active" : ""}><span aria-hidden>{icon}</span><small>{label}</small>{href === "/reservas" && <UnreadBadge count={unread.total} />}</Link>)}</div>
      </> : <div className="public-navigation"><Link href="/login">Ingresar</Link><Link className="button-primary" href="/registro">Crear cuenta</Link></div>}
    </nav>
  </header>;
}
