import type { GeoPoint } from "@/lib/types";

export function decodePolyline(encoded: string, precision = 5): GeoPoint[] {
  if (!encoded) return [];
  const factor = 10 ** precision;
  const points: GeoPoint[] = [];
  let index = 0;
  let latitude = 0;
  let longitude = 0;

  const nextValue = (): number | null => {
    let result = 0;
    let shift = 0;
    let byte: number;
    do {
      if (index >= encoded.length) return null;
      byte = encoded.charCodeAt(index++) - 63;
      if (byte < 0 || byte > 63) return null;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    return result & 1 ? ~(result >> 1) : result >> 1;
  };

  while (index < encoded.length) {
    const latitudeDelta = nextValue();
    const longitudeDelta = nextValue();
    if (latitudeDelta === null || longitudeDelta === null) return [];
    latitude += latitudeDelta;
    longitude += longitudeDelta;
    points.push({ latitude: latitude / factor, longitude: longitude / factor });
  }
  return points;
}
