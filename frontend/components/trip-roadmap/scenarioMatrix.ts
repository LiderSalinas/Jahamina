import type { DriverScenarioId, PassengerScenarioId, RoadmapRole, ScenarioDefinition, ScenarioId, StepStatus, TimelineStep } from "./types";

const passenger = (id:PassengerScenarioId,label:string,tripState:string,passengerState:string,heroTitle:string,heroNext:string,primaryAction:string,currentStep:number,currentStop:number,onboard:number,pending:number,distance="2,8 km",minutes="aprox. 7 min"):ScenarioDefinition => ({ id,role:"pasajero",label,tripState,passengerState,heroTitle,heroNext,primaryAction,currentStep,currentStop,onboard,pending,distance,minutes });
const driver = (id:DriverScenarioId,label:string,tripState:string,passengerState:string,heroTitle:string,heroNext:string,primaryAction:string,currentStep:number,currentStop:number,onboard:number,pending:number,distance="8 km",minutes="aprox. 15 min"):ScenarioDefinition => ({ id,role:"conductor",label,tripState,passengerState,heroTitle,heroNext,primaryAction,currentStep,currentStop,onboard,pending,distance,minutes });

export const scenarioMatrix:Record<RoadmapRole,ScenarioDefinition[]> = {
  pasajero:[
    passenger("reserva_confirmada","Reserva confirmada","programado","confirmado","Tu lugar está confirmado","Acordar tu punto de encuentro","Ver detalles",0,0,0,3,"18 km","aprox. 25 min"),
    passenger("punto_acordado","Punto acordado","programado","punto acordado","Tu punto de encuentro está listo","Terminal de San Miguel · zona centro","Revisar indicaciones",1,1,0,3),
    passenger("no_listo","Todavía no está listo","programado","no listo","Todo listo para coordinar","Tu punto de encuentro","Confirmar que estoy listo",2,1,0,3),
    passenger("pasajero_listo","Pasajero listo","programado","listo","Estás listo para viajar","Rubén prepara la salida","Esperar al conductor",3,1,0,3),
    passenger("conductor_en_camino","Conductor en camino","en camino","listo","El conductor está en camino","Tu punto de encuentro","Abrir indicaciones",3,1,0,3),
    passenger("conductor_llego","Conductor llegó","en punto","listo","Rubén llegó al punto","Terminal de San Miguel · zona centro","Llegué al punto",4,1,0,3),
    passenger("pasajero_abordado","Pasajero abordado","en punto","a bordo","Ya estás a bordo","Recoger a María · zona norte","Ver próxima parada",5,2,2,1,"8 km","aprox. 15 min"),
    passenger("viaje_en_curso","Viaje en curso","en curso","a bordo","Tu viaje comenzó","Parada en Coronel Bogado","Ver recorrido",6,3,3,0,"18 km","aprox. 25 min"),
    passenger("finalizado","Finalizado","finalizado","completado","Llegaste a Asunción","Viaje completado","Ver resumen",8,4,0,0,"0 km","completado"),
    passenger("cancelado","Cancelado","cancelado","cancelado","El viaje fue cancelado","No habrá nuevas paradas","Ver detalles",2,1,0,0,"—","sin recorrido"),
  ],
  conductor:[
    driver("preparando_salida","Preparando salida","programado","pendientes","Prepará la salida","Revisar pasajeros y vehículo","Preparar salida",1,0,1,2,"18 km","aprox. 25 min"),
    driver("pasajeros_pendientes","Pasajeros pendientes","programado","pendientes","Faltan pasajeros por confirmar","Próxima recogida: Ramón","Salir hacia el punto",2,1,1,2),
    driver("conductor_en_camino","Conductor en camino","en camino","Ramón listo","Vas hacia la próxima recogida","Próxima recogida: Ramón","Llegué",3,1,1,2),
    driver("llegada_al_punto","Llegada al punto","en punto","esperando abordaje","Llegaste al punto acordado","Ramón · Terminal de San Miguel","Confirmar pasajero abordado",4,1,1,2,"0 km","en el punto"),
    driver("recogida_pasajero","Recogida de pasajero","en punto","Ramón a bordo","Ramón está a bordo","Próxima recogida: María","Iniciar viaje",5,2,2,1),
    driver("viaje_en_curso","Viaje en curso","en curso","a bordo","El viaje está en curso","Parada en Coronel Bogado","Continuar recorrido",6,3,3,0,"18 km","aprox. 25 min"),
    driver("finalizado","Finalizado","finalizado","completado","Viaje finalizado","Todos llegaron a destino","Ver resumen",8,4,0,0,"0 km","completado"),
    driver("cancelado","Cancelado","cancelado","cancelado","El viaje fue cancelado","No habrá nuevas paradas","Ver detalles",2,1,0,0,"—","sin recorrido"),
  ],
};

const timelineContent = [
  ["Reserva confirmada","Lugar reservado","Hoy, 18:42",0], ["Punto acordado","Terminal de San Miguel","Hoy, 18:55",1], ["Pasajero listo","Confirmación para salir",undefined,1], ["Conductor en camino","Última actualización hace 2 min","Ahora",1], ["Llegada al punto","Encuentro en zona pública",undefined,1], ["Pasajero abordado","Lugar ocupado confirmado",undefined,2], ["Viaje iniciado","Todos coordinados",undefined,2], ["Destino","Asunción · zona centro",undefined,4], ["Finalización","Resumen disponible",undefined,4],
] as const;

export function timelineFor(scenario:ScenarioDefinition):TimelineStep[] { return timelineContent.map(([title,detail,time,stopIndex],index)=>{ const status:StepStatus=scenario.tripState==="cancelado"&&index>=scenario.currentStep?"cancelled":index<scenario.currentStep?"completed":index===scenario.currentStep?"current":"pending"; return {title,detail,time:status==="current"?"Ahora · última actualización hace 2 min":time,status,stopIndex}; }); }
export function scenarioById(role:RoadmapRole,id:ScenarioId):ScenarioDefinition { return scenarioMatrix[role].find(item=>item.id===id)??scenarioMatrix[role][0]; }
