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
        <SurfaceCard className="profile-card">
          <div className="profile-identity"><UserAvatar name={user?.nombre ?? "Jahamina"} imageUrl={user?.imagen_url} size="lg"/><div><h2>{user?.nombre}</h2><p>Miembro de Jahamina</p></div></div>
          {token && <ImageUploadControl hasImage={Boolean(user?.imagen_url)} uploading={uploading} onUpload={upload} onDelete={remove} description="Una foto ayuda a que te reconozcan durante el viaje."/>}
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
