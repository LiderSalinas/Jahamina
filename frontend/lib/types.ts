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
  punto_salida_latitud: number | null;
  punto_salida_longitud: number | null;
  punto_llegada_latitud: number | null;
  punto_llegada_longitud: number | null;
  distancia_estimada_km: number | null;
  duracion_estimada_minutos: number | null;
  ruta_codificada: string | null;
  estado: "publicado" | "completo" | "en_curso" | "finalizado" | "cancelado";
  updated_at: string;
}

export interface GeoPoint { latitude: number; longitude: number; }
export interface GeocodingResult extends GeoPoint { label: string; }
export interface RouteResult { distance_km: number; duration_minutes: number; geometry: string | null; }
export interface MeetingPoint {
  reserva_id: number; texto: string | null; latitude: number | null; longitude: number | null;
  estado: "sin_definir" | "propuesto" | "confirmado" | "rechazado" | "reemplazado";
  propuesto_por_id: number | null; propuesto_en: string | null;
  confirmado_por_conductor_en: string | null; confirmado_por_pasajero_en: string | null; actualizado_en: string | null;
}
export interface Tracking {
  id: number; viaje_id: number; conductor_id: number; estado: "inactivo" | "activo" | "pausado" | "finalizado" | "cancelado";
  iniciado_en: string | null; pausado_en: string | null; finalizado_en: string | null; compartir_ubicacion: boolean; ultima_actualizacion_en: string | null;
}
export interface CurrentLocation extends GeoPoint { accuracy: number; speed: number | null; heading: number | null; updated_at: string; stale: boolean; }

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
  estado_pasajero: "confirmado" | "listo" | "esperando" | "recogido" | "abordo" | "completado" | "ausente" | "cancelado";
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

export interface RoadmapStopReal { id:number|null; reserva_id:number|null; orden:number; tipo:string; nombre_publico:string; zona_general:string|null; latitud:number|null; longitud:number|null; hora_estimada:string|null; hora_real:string|null; estado:string; }
export interface RoadmapEventReal { id:number; reserva_id:number|null; tipo:string; descripcion_publica:string; metadata:Record<string, unknown>; created_at:string; }
export interface Roadmap {
  reserva:{id:number; estado:string; rol_actual:"conductor"|"pasajero"; mensaje_inicial:string|null};
  viaje:{id:number; origen:string; destino:string; fecha_salida:string; estado:string; cupos_totales:number; cupos_ocupados:number; ruta_codificada:string|null};
  conductor:{id:number; nombre:string}; pasajero_actual:{id:number; nombre:string};
  vehiculo:{id:number; marca:string; modelo:string; color:string; matricula:string}|null;
  punto_encuentro:{estado:string; nombre_publico:string|null; zona_general:string|null; latitud:number|null; longitud:number|null};
  paradas:RoadmapStopReal[]; eventos:RoadmapEventReal[];
  hoja_ruta:{id:string; titulo:string; descripcion:string; estado:"completado"|"actual"|"pendiente"|"cancelado"; timestamp:string|null; orden:number}[];
  ocupacion:{ocupados:number; totales:number; pendientes:number};
  estado_pasajero:{estado:string; nombre:string};
  proxima_accion:{label:string; action:string; enabled:boolean; reason_disabled:string|null; confirmation_required:boolean};
  permisos:{puede_operar_viaje:boolean; puede_actualizar_estado_propio:boolean; puede_ver_puntos_exactos:boolean; puede_ver_chat:boolean; puede_ver_punto_exacto:boolean; puede_modificar_viaje:boolean};
}
