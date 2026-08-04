"use client";

import { useParams } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { MeetingPointSelector } from "@/components/maps/MeetingPointSelector";
import { RealTripRoadmap } from "@/components/trip-roadmap/RealTripRoadmap";

export default function ReservationDetailPage() {
  const { token } = useAuth();
  const params = useParams<{ id: string }>();
  const reservationId = Number(params.id);
  return <ProtectedRoute><section className="container py-8">
    {token && Number.isInteger(reservationId) && <RealTripRoadmap reservationId={reservationId} token={token}/>}
    <div className="mt-8 grid gap-6 xl:grid-cols-2" id="chat-reserva"><ChatPanel reservationId={reservationId}/><div id="meeting-point"><MeetingPointSelector reservationId={reservationId}/></div></div>
  </section></ProtectedRoute>;
}
