export interface User {
  id: number;
  nombre: string;
  email: string;
}

export interface Trip {
  id: number;
  origen: string;
  destino: string;
  fecha: string;
  cancelado: boolean;
  creador_id: number;
  vehiculo_id: number | null;
  cupos_totales: number;
  cupos_disponibles: number;
  descripcion: string | null;
  punto_salida: string;
  punto_llegada: string;
  origen_latitud: number | null;
  origen_longitud: number | null;
  destino_latitud: number | null;
  destino_longitud: number | null;
  estado: "publicado" | "completo" | "en_curso" | "finalizado" | "cancelado";
  updated_at: string;
}

export interface JoinedTrip {
  id: number;
  viaje_id: number;
  usuario_id: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface Vehicle {
  id: number;
  propietario_id: number;
  marca: string;
  modelo: string;
  color: string;
  matricula: string;
  capacidad: number;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface TripRequest {
  id: number;
  viaje_id: number;
  pasajero_id: number;
  estado: "pendiente" | "aceptada" | "rechazada" | "cancelada" | "finalizada";
  mensaje_inicial: string | null;
  punto_encuentro_propuesto: string | null;
  punto_encuentro_latitud: number | null;
  punto_encuentro_longitud: number | null;
  created_at: string;
  updated_at: string;
  responded_at: string | null;
}
