export type RoadmapRole = "conductor" | "pasajero";
export type LocationDemoState = "activa" | "sin_ubicacion" | "desactualizada";
export type StepStatus = "completed" | "current" | "pending" | "cancelled";

export type PassengerScenarioId = "reserva_confirmada" | "punto_acordado" | "no_listo" | "pasajero_listo" | "conductor_en_camino" | "conductor_llego" | "pasajero_abordado" | "viaje_en_curso" | "finalizado" | "cancelado";
export type DriverScenarioId = "preparando_salida" | "pasajeros_pendientes" | "conductor_en_camino" | "llegada_al_punto" | "recogida_pasajero" | "viaje_en_curso" | "finalizado" | "cancelado";
export type ScenarioId = PassengerScenarioId | DriverScenarioId;

export interface RoadmapStop { time:string; title:string; passenger:string; detail:string; occupancy:string; status:StepStatus; }
export interface TimelineStep { title:string; detail:string; status:StepStatus; time?:string; stopIndex:number; }
export interface ScenarioDefinition { id:ScenarioId; role:RoadmapRole; label:string; tripState:string; passengerState:string; heroTitle:string; heroNext:string; primaryAction:string; distance:string; minutes:string; currentStep:number; currentStop:number; onboard:number; pending:number; }
export interface RoadmapDemoState { role:RoadmapRole; scenarioId:ScenarioId; location:LocationDemoState; }
