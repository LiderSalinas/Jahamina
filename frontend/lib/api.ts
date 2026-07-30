import type {
  TokenResponse,
  Trip,
  TripRequest,
  User,
  Vehicle,
} from "@/lib/types";

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

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

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
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
};
