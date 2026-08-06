"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { PublishTripFlow } from "@/components/publish-trip/PublishTripFlow";

export default function NewTripPage() {
  return <ProtectedRoute><PublishTripFlow/></ProtectedRoute>;
}
