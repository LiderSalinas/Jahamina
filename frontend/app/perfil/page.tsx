"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/components/AuthProvider";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  return (
    <ProtectedRoute>
      <section className="container grid min-h-[calc(100vh-4rem)] place-items-center py-12">
        <div className="form-card w-full max-w-xl">
          <p className="eyebrow">Tu cuenta</p>
          <h1 className="mt-2 text-3xl font-black">Perfil</h1>
          <dl className="mt-8 grid gap-5">
            <div><dt className="eyebrow">Nombre</dt><dd className="mt-1 text-lg font-bold">{user?.nombre}</dd></div>
            <div><dt className="eyebrow">Email</dt><dd className="mt-1 text-lg font-bold">{user?.email}</dd></div>
          </dl>
          <button className="button-secondary mt-8" onClick={logout} type="button">Cerrar sesión</button>
        </div>
      </section>
    </ProtectedRoute>
  );
}
