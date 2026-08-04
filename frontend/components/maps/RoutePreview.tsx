import type { RouteResult } from "@/lib/types";
export function RoutePreview({ route }: { route: RouteResult | null }) { return route ? <div className="route-summary"><strong>{route.distance_km} km</strong><span>≈ {route.duration_minutes} min</span></div> : null; }
