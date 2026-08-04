"use client";
import { useState } from "react";
import { scenarioById,scenarioMatrix,timelineFor } from "./scenarioMatrix";
import { TripMapPreview } from "./TripMapPreview";
import { TripNextStopCard } from "./TripNextStopCard";
import { TripPassengerProgress } from "./TripPassengerProgress";
import { TripPrimaryAction } from "./TripPrimaryAction";
import { TripQuickActions } from "./TripQuickActions";
import { TripStatusHero } from "./TripStatusHero";
import { TripStopList } from "./TripStopList";
import { TripTimeline } from "./TripTimeline";
import { TripVehicleCard } from "./TripVehicleCard";
import type { LocationDemoState,RoadmapDemoState,RoadmapRole,RoadmapStop,ScenarioId,StepStatus } from "./types";

const baseStops=[
  ["08:00","Salida de San Juan","Inicio del recorrido","Terminal · zona pública","1/4"],
  ["08:15","Punto de encuentro","Ramón","Terminal de San Miguel · zona centro","2/4"],
  ["08:30","Segunda recogida","María","Acceso principal · zona norte","3/4"],
  ["10:40","Parada de descanso","Todos","Coronel Bogado · zona comercial","3/4"],
  ["12:00","Llegada a Asunción","Destino","Centro · zona general","0/4"],
] as const;
function stopsFor(current:number,cancelled:boolean):RoadmapStop[]{return baseStops.map(([time,title,passenger,detail,occupancy],index)=>{const status:StepStatus=cancelled&&index>=current?"cancelled":index<current?"completed":index===current?"current":"pending";return{time,title,passenger,detail,occupancy,status};});}

export function TripRoadmapPreview(){
  const [state,setState]=useState<RoadmapDemoState>({role:"pasajero",scenarioId:"conductor_en_camino",location:"activa"});
  const scenario=scenarioById(state.role,state.scenarioId);
  const [selectedStop,setSelectedStop]=useState(scenario.currentStop);
  const stops=stopsFor(scenario.currentStop,scenario.tripState==="cancelado");
  function changeRole(role:RoadmapRole){const first=scenarioMatrix[role][0];setState(current=>({...current,role,scenarioId:first.id}));setSelectedStop(first.currentStop);}
  function changeScenario(id:ScenarioId){const next=scenarioById(state.role,id);setState(current=>({...current,scenarioId:id}));setSelectedStop(next.currentStop);}
  return <main className="roadmap-page"><details className="roadmap-demo-controls" open><summary><span><span className="roadmap-kicker">Laboratorio de experiencia</span><b>Configurar escenario demo</b></span><span className="demo-chevron" aria-hidden="true">⌄</span></summary><div className="demo-control-grid"><label htmlFor="demo-role">Rol<select id="demo-role" value={state.role} onChange={event=>changeRole(event.target.value as RoadmapRole)}><option value="pasajero">Pasajero</option><option value="conductor">Conductor</option></select></label><label htmlFor="demo-state">Estado<select id="demo-state" value={scenario.id} onChange={event=>changeScenario(event.target.value as ScenarioId)}>{scenarioMatrix[state.role].map(item=><option value={item.id} key={item.id}>{item.label}</option>)}</select></label><label htmlFor="demo-location">Ubicación<select id="demo-location" value={state.location} onChange={event=>setState(current=>({...current,location:event.target.value as LocationDemoState}))}><option value="activa">Activa (demo)</option><option value="sin_ubicacion">Sin ubicación</option><option value="desactualizada">Desactualizada</option></select></label></div><p>Solo visible en esta página. No ejecuta acciones reales.</p></details>
  <header className="roadmap-trip-header"><div><p>Miércoles, 6 de agosto · 08:00</p><h1>San Juan <span>→</span> Asunción</h1><small>Reserva #JH-2048 · {state.role==="conductor"?"Viajás como conductor":"Viajás con Rubén"}</small></div><span className={`trip-state-pill is-${scenario.tripState.replace(" ","_")}`}>{scenario.tripState}</span></header>
  <div className="roadmap-layout"><div className="roadmap-main-column"><TripStatusHero scenario={scenario} location={state.location}/><TripPrimaryAction scenario={scenario}/><TripNextStopCard stop={stops[scenario.currentStop]} index={scenario.currentStop} scenario={scenario}/><TripMapPreview stops={stops} location={state.location} selectedStop={selectedStop} onSelect={setSelectedStop}/><TripQuickActions/><TripVehicleCard/><TripPassengerProgress scenario={scenario}/></div><div className="roadmap-side-column"><TripTimeline steps={timelineFor(scenario)} selectedStop={selectedStop} onSelect={setSelectedStop}/><TripStopList stops={stops} selected={selectedStop} onSelect={setSelectedStop}/><section className="roadmap-chat-entry" id="chat-demo"><span aria-hidden="true">💬</span><div><p className="roadmap-kicker">Coordinación</p><h2>Chat del viaje</h2><p>Acceso al chat existente, sin perder el contexto de la ruta.</p></div><button type="button" aria-label="Abrir chat del viaje, demostración">Abrir chat</button></section></div></div></main>;
}
