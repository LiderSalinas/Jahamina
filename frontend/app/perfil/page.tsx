"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/components/AuthProvider";
import { PageContainer } from "@/components/ui/PageContainer";
import { PageHeader, SurfaceCard } from "@/components/ui/AppUI";
import { NotificationPermissionCard } from "@/components/notifications/NotificationPermissionCard";

export default function ProfilePage() {
  const { user, token } = useAuth();
  const initials = user?.nombre.split(/\s+/).slice(0, 2).map(part => part[0]).join("").toUpperCase() || "J";
  return (
    <ProtectedRoute>
      <PageContainer className="page-stack profile-page">
        <PageHeader eyebrow="Tu cuenta" title="Perfil" description="Tu información y preferencias de Jahamina."/>
        <div className="profile-layout">
        <SurfaceCard className="profile-card">
          <div className="profile-identity"><span aria-hidden>{initials}</span><div><h2>{user?.nombre}</h2><p>Miembro de Jahamina</p></div></div>
          <dl className="profile-details">
            <div><dt className="eyebrow">Nombre</dt><dd className="mt-1 text-lg font-bold">{user?.nombre}</dd></div>
            <div><dt className="eyebrow">Email</dt><dd className="mt-1 text-lg font-bold">{user?.email}</dd></div>
          </dl>
        </SurfaceCard>
        <SurfaceCard><p className="eyebrow">Preferencias</p><h2 className="section-title">Notificaciones</h2><p className="section-description">Elegí qué avisos importantes querés recibir en este dispositivo.</p>{token && <NotificationPermissionCard token={token}/>}</SurfaceCard>
        </div>
      </PageContainer>
    </ProtectedRoute>
  );
}
