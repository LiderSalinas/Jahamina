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

export interface ChatMessage {
  id: number;
  conversacion_id: number;
  remitente_id: number | null;
  contenido: string;
  tipo: "texto" | "sistema";
  creado_en: string;
  editado_en: string | null;
  leido_en: string | null;
  eliminado: boolean;
  client_message_id: string | null;
}

export interface ChatMessagePage {
  items: ChatMessage[];
  next_cursor: number | null;
}

export interface Conversation {
  id: number;
  solicitud_id: number;
  creada_en: string;
  actualizada_en: string;
  ultimo_mensaje_en: string | null;
  cerrada_en: string | null;
  activa: boolean;
  puede_escribir: boolean;
  no_leidos: number;
  participante: string;
  viaje_id: number;
  origen: string;
  destino: string;
  estado_viaje: string;
  estado_reserva: string;
  ultimo_mensaje: string | null;
}

export interface UnreadSummary {
  total: number;
  conversaciones: { conversacion_id: number; solicitud_id: number; cantidad: number }[];
}

export interface RelatedReservation {
  reserva_id: number;
  viaje_id: number;
  origen: string;
  destino: string;
  fecha: string;
  estado: TripRequest["estado"];
  rol: "conductor" | "pasajero";
  participante_id: number;
  participante: string;
  conversacion_id: number | null;
  ultimo_mensaje: string | null;
  no_leidos: number;
  ultima_actividad: string;
}
