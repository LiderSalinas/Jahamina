import type { GeoPoint } from "@/lib/types";

export const PARAGUAY_COUNTRY_CODE = "py";
export const PARAGUAY_COUNTRY_NAME = "Paraguay";
export const PARAGUAY_BOUNDS: [[number, number], [number, number]] = [
  [-62.65, -27.61],
  [-54.26, -19.29],
];
export const PARAGUAY_CENTER: [number, number] = [-58.45, -23.45];

export function isWithinParaguay(point: GeoPoint): boolean {
  return Number.isFinite(point.latitude) && Number.isFinite(point.longitude)
    && point.latitude >= PARAGUAY_BOUNDS[0][1] && point.latitude <= PARAGUAY_BOUNDS[1][1]
    && point.longitude >= PARAGUAY_BOUNDS[0][0] && point.longitude <= PARAGUAY_BOUNDS[1][0];
}
