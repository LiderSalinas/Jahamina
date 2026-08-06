"use client";

import { useParams } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ChatPreview } from "@/components/chat/ChatPreview";
import { MeetingPointSelector } from "@/components/maps/MeetingPointSelector";
import { RealTripRoadmap } from "@/components/trip-roadmap/RealTripRoadmap";
import { PageContainer } from "@/components/ui/PageContainer";

export default function ReservationDetailPage() {
  const { token } = useAuth();
  const params = useParams<{ id: string }>();
  const reservationId = Number(params.id);
  return <ProtectedRoute><PageContainer className="reservation-page">
    {token && Number.isInteger(reservationId) && <RealTripRoadmap reservationId={reservationId} token={token} meetingPoint={({ reservationState, tripState }) => <MeetingPointSelector reservationId={reservationId} reservationState={reservationState} tripState={tripState}/>} chat={({ reservationState }) => <ChatPreview reservationId={reservationId} reservationState={reservationState}/>}/>}
  </PageContainer></ProtectedRoute>;
}
