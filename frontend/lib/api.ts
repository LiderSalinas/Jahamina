import type {
  TokenResponse,
  Trip,
  TripRequest,
  User,
  Vehicle,
  ChatMessage,
  ChatMessagePage,
  Conversation,
  UnreadSummary,
  RelatedReservation,
  GeocodingResult,
  GeoPoint,
  RouteResult,
  MeetingPoint,
  Tracking,
  CurrentLocation,
  LocationEta,
  Roadmap,
} from "@/lib/types";

type ValidationDetail = {
  msg?: string;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function apiUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!configured) {
    throw new ApiError(
      0,
      "La API de Jahamina no está configurada. Define NEXT_PUBLIC_API_URL y reinicia el frontend.",
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(configured);
  } catch {
    throw new ApiError(0, "NEXT_PUBLIC_API_URL no contiene una URL válida.");
  }
  if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password) {
    throw new ApiError(0, "NEXT_PUBLIC_API_URL utiliza una configuración no permitida.");
  }
  if (
    typeof window !== "undefined"
    && !["localhost", "127.0.0.1"].includes(window.location.hostname)
    && ["localhost", "127.0.0.1"].includes(parsed.hostname)
  ) {
    throw new ApiError(
      0,
      "La API está configurada como localhost y no es accesible desde este dispositivo.",
    );
  }
  return configured.replace(/\/$/, "");
}

export function buildWebSocketUrl(path: string): string {
  if (!path.startsWith("/")) {
    throw new ApiError(0, "La ruta WebSocket no es válida.");
  }
  const url = new URL(`${apiUrl()}${path}`);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as {
      detail?: string | ValidationDetail[];
    };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((item) => item.msg).filter(Boolean).join(". ");
    }
  } catch {
    // La respuesta sin JSON usa el mensaje HTTP.
  }
  if (response.status === 401) return "Tu sesión no es válida.";
  if (response.status === 403) return "No tienes permiso para esta operación.";
  if (response.status === 404) return "El recurso no existe.";
  if (response.status === 409) return "El recurso ya existe.";
  return "No se pudo completar la solicitud.";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const baseUrl = apiUrl();
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...options,
      headers,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con Jahamina.");
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response));
  }
  return response.json() as Promise<T>;
}

export const api = {
  register(payload: {
    nombre: string;
    email: string;
    password: string;
  }): Promise<User> {
    return request<User>("/auth/registro", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  login(email: string, password: string): Promise<TokenResponse> {
    const body = new URLSearchParams({ username: email, password });
    return request<TokenResponse>("/auth/login", { method: "POST", body });
  },
  me(token: string): Promise<User> {
    return request<User>("/auth/me", {}, token);
  },
  availableTrips(token: string): Promise<Trip[]> {
    return request<Trip[]>("/viajes/disponibles", {}, token);
  },
  myTrips(token: string): Promise<Trip[]> {
    return request<Trip[]>("/viajes/mis-viajes", {}, token);
  },
  joinedTrips(token: string): Promise<Trip[]> {
    return request<Trip[]>("/viajes/unidos", {}, token);
  },
  createTrip(
    payload: {
      origen: string;
      destino: string;
      fecha: string;
      vehiculo_id: number;
      cupos_totales: number;
      descripcion?: string;
      punto_salida: string;
      punto_llegada: string;
      origen_latitud?: number;
      origen_longitud?: number;
      destino_latitud?: number;
      destino_longitud?: number;
      punto_salida_latitud?: number;
      punto_salida_longitud?: number;
      punto_llegada_latitud?: number;
      punto_llegada_longitud?: number;
      distancia_estimada_km?: number;
      duracion_estimada_minutos?: number;
      ruta_codificada?: string;
    },
    token: string,
  ): Promise<Trip> {
    return request<Trip>(
      "/viajes/",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  createRequest(
    tripId: number,
    payload: {
      mensaje_inicial?: string;
      punto_encuentro_propuesto?: string;
    },
    token: string,
  ): Promise<TripRequest> {
    return request<TripRequest>(
      `/viajes/${tripId}/solicitudes`,
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  cancelTrip(id: number, token: string): Promise<Trip> {
    return request<Trip>(
      `/viajes/cancelar/${id}`,
      { method: "PUT" },
      token,
    );
  },
  vehicles(token: string): Promise<Vehicle[]> {
    return request<Vehicle[]>("/vehiculos", {}, token);
  },
  createVehicle(
    payload: {
      marca: string;
      modelo: string;
      color: string;
      matricula: string;
      capacidad: number;
    },
    token: string,
  ): Promise<Vehicle> {
    return request<Vehicle>(
      "/vehiculos",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  updateVehicle(
    id: number,
    payload: Partial<Pick<Vehicle, "marca" | "modelo" | "color" | "matricula" | "capacidad">>,
    token: string,
  ): Promise<Vehicle> {
    return request<Vehicle>(
      `/vehiculos/${id}`,
      { method: "PATCH", body: JSON.stringify(payload) },
      token,
    );
  },
  disableVehicle(id: number, token: string): Promise<Vehicle> {
    return request<Vehicle>(
      `/vehiculos/${id}/desactivar`,
      { method: "PATCH" },
      token,
    );
  },
  myRequests(token: string): Promise<TripRequest[]> {
    return request<TripRequest[]>("/solicitudes/mias", {}, token);
  },
  relatedReservations(token: string): Promise<RelatedReservation[]> {
    return request<RelatedReservation[]>("/reservas/relacionadas", {}, token);
  },
  tripRequests(tripId: number, token: string): Promise<TripRequest[]> {
    return request<TripRequest[]>(
      `/viajes/${tripId}/solicitudes`,
      {},
      token,
    );
  },
  request(id: number, token: string): Promise<TripRequest> {
    return request<TripRequest>(`/solicitudes/${id}`, {}, token);
  },
  acceptRequest(id: number, token: string): Promise<TripRequest> {
    return request<TripRequest>(
      `/solicitudes/${id}/aceptar`,
      { method: "PATCH" },
      token,
    );
  },
  rejectRequest(id: number, token: string): Promise<TripRequest> {
    return request<TripRequest>(
      `/solicitudes/${id}/rechazar`,
      { method: "PATCH" },
      token,
    );
  },
  cancelRequest(id: number, token: string): Promise<TripRequest> {
    return request<TripRequest>(
      `/solicitudes/${id}/cancelar`,
      { method: "PATCH" },
      token,
    );
  },
  conversationByReservation(id: number, token: string): Promise<Conversation> {
    return request<Conversation>(`/reservas/${id}/conversacion`, {}, token);
  },
  chatMessages(id: number, token: string, beforeId?: number | null): Promise<ChatMessagePage> {
    const query = beforeId ? `?before_id=${beforeId}&limit=30` : "?limit=30";
    return request<ChatMessagePage>(`/conversaciones/${id}/mensajes${query}`, {}, token);
  },
  sendChatMessage(id: number, payload: { contenido: string; client_message_id: string }, token: string): Promise<ChatMessage> {
    return request<ChatMessage>(`/conversaciones/${id}/mensajes`, { method: "POST", body: JSON.stringify(payload) }, token);
  },
  markChatRead(id: number, token: string): Promise<unknown> {
    return request(`/conversaciones/${id}/leido`, { method: "PATCH" }, token);
  },
  unreadChats(token: string): Promise<UnreadSummary> {
    return request<UnreadSummary>("/conversaciones/no-leidos", {}, token);
  },
  async chatWebSocketUrl(id: number, token: string): Promise<string> {
    const response = await request<{ ticket: string }>(`/conversaciones/${id}/ws-ticket`, { method: "POST" }, token);
    return buildWebSocketUrl(`/ws/chat?ticket=${encodeURIComponent(response.ticket)}`);
  },
  geocode(query: string, token: string, signal?: AbortSignal): Promise<GeocodingResult[]> {
    return request<GeocodingResult[]>(`/mapas/geocodificar?q=${encodeURIComponent(query)}`, { signal }, token);
  },
  route(origin: GeoPoint, destination: GeoPoint, token: string): Promise<RouteResult> {
    return request<RouteResult>("/mapas/ruta", { method: "POST", body: JSON.stringify({ origin, destination }) }, token);
  },
  meetingPoint(id: number, token: string): Promise<MeetingPoint> { return request(`/reservas/${id}/punto-encuentro`, {}, token); },
  proposeMeetingPoint(id: number, payload: { texto: string; latitude: number; longitude: number }, token: string): Promise<MeetingPoint> { return request(`/reservas/${id}/punto-encuentro/proponer`, { method: "POST", body: JSON.stringify(payload) }, token); },
  confirmMeetingPoint(id: number, token: string): Promise<MeetingPoint> { return request(`/reservas/${id}/punto-encuentro/confirmar`, { method: "PATCH" }, token); },
  rejectMeetingPoint(id: number, token: string): Promise<MeetingPoint> { return request(`/reservas/${id}/punto-encuentro/rechazar`, { method: "PATCH" }, token); },
  startTracking(id: number, token: string): Promise<Tracking> { return request(`/viajes/${id}/seguimiento/iniciar`, { method: "POST" }, token); },
  tracking(id: number, token: string): Promise<Tracking> { return request(`/viajes/${id}/seguimiento`, {}, token); },
  pauseTracking(id: number, token: string): Promise<Tracking> { return request(`/viajes/${id}/seguimiento/pausar`, { method: "PATCH" }, token); },
  resumeTracking(id: number, token: string): Promise<Tracking> { return request(`/viajes/${id}/seguimiento/reanudar`, { method: "PATCH" }, token); },
  finishTracking(id: number, token: string): Promise<Tracking> { return request(`/viajes/${id}/seguimiento/finalizar`, { method: "PATCH" }, token); },
  shareLocation(id: number, enabled: boolean, token: string): Promise<Tracking> { return request(`/viajes/${id}/seguimiento/compartir`, { method: "PATCH", body: JSON.stringify({ enabled }) }, token); },
  sendLocation(id: number, payload: { latitude: number; longitude: number; accuracy: number; speed?: number | null; heading?: number | null; client_timestamp: string; sequence?: number }, token: string): Promise<CurrentLocation> { return request(`/viajes/${id}/ubicacion`, { method: "POST", body: JSON.stringify(payload) }, token); },
  currentLocation(id: number, token: string): Promise<CurrentLocation> { return request(`/viajes/${id}/ubicacion-actual`, {}, token); },
  locationContext(id: number, token: string): Promise<LocationEta> { return request(`/reservas/${id}/ubicacion-contexto`, {}, token); },
  async locationWebSocketUrl(id: number, token: string): Promise<{ url: string; role: "publisher" | "subscriber" }> {
    const response = await request<{ ticket: string; role: "publisher" | "subscriber" }>(`/viajes/${id}/ubicacion/ws-ticket`, { method: "POST" }, token);
    return { url: buildWebSocketUrl(`/ws/ubicacion?ticket=${encodeURIComponent(response.ticket)}`), role: response.role };
  },
  roadmap(id: number, token: string): Promise<Roadmap> { return request(`/reservas/${id}/hoja-ruta`, {}, token); },
  roadmapAction(data: Roadmap, token: string): Promise<Roadmap> {
    const action = data.proxima_accion.id;
    const tripAction = data.reserva.rol_actual === "conductor" && !["recoger", "abordar"].includes(action);
    const path = tripAction ? `/viajes/${data.viaje.id}/acciones/${action}` : `/reservas/${data.reserva.id}/acciones/${action}`;
    return request(path, { method: "POST" }, token);
  },
  async roadmapWebSocketUrl(id: number, token: string): Promise<string> {
    const response = await request<{ticket:string}>(`/reservas/${id}/hoja-ruta/ws-ticket`, {method:"POST"}, token);
    return buildWebSocketUrl(`/ws/hoja-ruta?ticket=${encodeURIComponent(response.ticket)}`);
  },
};
