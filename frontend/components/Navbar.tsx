"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { UnreadBadge } from "@/components/chat/UnreadBadge";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { api } from "@/lib/api";
import type { UnreadSummary } from "@/lib/types";
import { UserAvatar } from "@/components/ui/UserAvatar";

const links = [
  ["Viajes", "/viajes"], ["Vehículos", "/vehiculos"], ["Reservas", "/reservas"],
  ["Mis viajes", "/mis-viajes"], ["Perfil", "/perfil"],
] as const;

export function Navbar() {
  const { user, token, loading, logout } = useAuth();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const menuTriggerRef = useRef<HTMLButtonElement | null>(null);
  const accountRef = useRef<HTMLDivElement | null>(null);
  const [unread, setUnread] = useState<UnreadSummary>({ total: 0, conversaciones: [] });
  useEffect(() => {
    if (!token) return;
    const refresh = () => api.unreadChats(token).then(setUnread).catch(() => undefined);
    refresh(); const timer = window.setInterval(refresh, 10000);
    window.addEventListener("jahamina:unread-changed", refresh);
    return () => { window.clearInterval(timer); window.removeEventListener("jahamina:unread-changed", refresh); };
  }, [token]);
  useEffect(() => {
    if (!menuOpen && !accountOpen) return;
    const closeWithEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
        setAccountOpen(false);
        menuTriggerRef.current?.focus();
      }
    };
    const closeAccountOutside = (event: PointerEvent) => {
      if (accountOpen && !accountRef.current?.contains(event.target as Node)) setAccountOpen(false);
    };
    document.addEventListener("keydown", closeWithEscape);
    document.addEventListener("pointerdown", closeAccountOutside);
    return () => {
      document.removeEventListener("keydown", closeWithEscape);
      document.removeEventListener("pointerdown", closeAccountOutside);
    };
  }, [accountOpen, menuOpen]);
  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  return <header className="app-header"><nav className="app-header-inner" aria-label="Navegación principal">
    <Link href="/" className="brand" onClick={() => setMenuOpen(false)}><span className="brand-mark" aria-hidden="true">J</span><span><b>Jaha<em>mina</em></b><small>Vamos juntos</small></span></Link>
    {!loading && user ? <>
      <div className="desktop-navigation">{links.map(([label, href]) => <Link key={href} href={href} aria-current={isActive(href) ? "page" : undefined} className={isActive(href) ? "is-active" : ""}>{label}{href === "/reservas" && <UnreadBadge count={unread.total}/>}</Link>)}</div>
      <div className="header-actions" ref={accountRef}>{token && <NotificationBell token={token}/>}<button className="account-trigger" type="button" aria-label="Abrir menú de cuenta" aria-expanded={accountOpen} aria-controls="account-navigation" onClick={() => setAccountOpen(value => !value)}><UserAvatar name={user.nombre} imageUrl={user.imagen_url} size="sm"/><span className="account-copy"><b>{user.nombre}</b><small>Mi cuenta</small></span><span aria-hidden="true">⌄</span></button><button ref={menuTriggerRef} className="mobile-menu-trigger" type="button" aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"} aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => { setAccountOpen(false); setMenuOpen(value => !value); }}><span aria-hidden="true">{menuOpen ? "×" : "☰"}</span></button>{accountOpen && <div className="account-menu" id="account-navigation"><Link href="/perfil" onClick={() => setAccountOpen(false)}>Ver perfil</Link><button type="button" onClick={() => { setAccountOpen(false); logout(); }}>Cerrar sesión</button></div>}</div>
      {menuOpen && <><button className="mobile-menu-backdrop" type="button" aria-label="Cerrar menú" onClick={() => setMenuOpen(false)}/><div id="mobile-navigation" className="mobile-navigation"><div className="mobile-account-summary"><UserAvatar name={user.nombre} imageUrl={user.imagen_url} size="md"/><div><b>{user.nombre}</b><small>Tu cuenta Jahamina</small></div></div>{links.map(([label, href]) => <Link key={href} href={href} aria-current={isActive(href) ? "page" : undefined} onClick={() => setMenuOpen(false)} className={isActive(href) ? "is-active" : ""}>{label}{href === "/reservas" && <UnreadBadge count={unread.total}/>}</Link>)}<button type="button" onClick={() => { setMenuOpen(false); logout(); }}>Cerrar sesión</button></div></>}
    </> : <div className="public-navigation"><Link href="/login">Ingresar</Link><Link className="button-primary" href="/registro">Crear cuenta</Link></div>}
  </nav></header>;
}
