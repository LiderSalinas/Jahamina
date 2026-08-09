"use client";

import { useState } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/components/AuthProvider";
import { PageContainer } from "@/components/ui/PageContainer";
import { PageHeader, SurfaceCard } from "@/components/ui/AppUI";
import { NotificationPermissionCard } from "@/components/notifications/NotificationPermissionCard";
import { UserAvatar } from "@/components/ui/UserAvatar";
import { ImageUploadControl } from "@/components/media/ImageUploadControl";
import { api } from "@/lib/api";

export default function ProfilePage() {
  const { user, token, refreshUser } = useAuth();
  const [uploading, setUploading] = useState(false);
  const upload = async (file: File) => { if (!token) return; setUploading(true); try { await api.uploadProfileImage(file, token); await refreshUser(); } finally { setUploading(false); } };
  const remove = async () => { if (!token) return; setUploading(true); try { await api.deleteProfileImage(token); await refreshUser(); } finally { setUploading(false); } };
  return (
    <ProtectedRoute>
      <PageContainer className="page-stack profile-page">
        <PageHeader eyebrow="Tu cuenta" title="Perfil" description="Tu información y preferencias de Jahamina."/>
        <div className="profile-layout">
        <SurfaceCard className="profile-card profile-account-card">
          <section className="profile-section profile-identity-section" aria-labelledby="profile-identity-title">
            <p className="eyebrow">Tu cuenta</p>
            <div className="profile-identity"><UserAvatar name={user?.nombre ?? "Jahamina"} imageUrl={user?.imagen_url} size="lg"/><div><h2 id="profile-identity-title">{user?.nombre}</h2><p>Miembro de Jahamina</p></div></div>
          </section>
          <section className="profile-section profile-photo-section" aria-labelledby="profile-photo-title">
            <div className="profile-section-heading"><div><p className="eyebrow">Imagen</p><h2 id="profile-photo-title" className="section-title">Foto de perfil</h2></div><span className="profile-section-mark" aria-hidden>✦</span></div>
            {token && <ImageUploadControl hasImage={Boolean(user?.imagen_url)} uploading={uploading} onUpload={upload} onDelete={remove} description="Una foto ayuda a que te reconozcan durante el viaje."/>}
          </section>
          <section className="profile-section profile-details-section" aria-labelledby="profile-details-title">
            <p className="eyebrow">Datos personales</p><h2 id="profile-details-title" className="section-title">Información personal</h2>
            <dl className="profile-details">
              <div><dt className="eyebrow">Nombre</dt><dd>{user?.nombre}</dd></div>
              <div><dt className="eyebrow">Email</dt><dd>{user?.email}</dd></div>
            </dl>
          </section>
        </SurfaceCard>
        <SurfaceCard className="profile-preferences-card"><section className="profile-section" aria-labelledby="profile-notifications-title"><p className="eyebrow">Preferencias</p><h2 id="profile-notifications-title" className="section-title">Notificaciones</h2><p className="section-description">Elegí qué avisos importantes querés recibir en este dispositivo.</p>{token && <NotificationPermissionCard token={token}/>}</section></SurfaceCard>
        </div>
      </PageContainer>
    </ProtectedRoute>
  );
}
