# Prototipo: hoja de ruta del viaje

## Objetivo y jerarquía

La pantalla responde primero estado, siguiente evento y acción; después aporta próxima parada, mapa contextual, cronología, paradas, ocupación, vehículo y chat. `/dev/hoja-ruta` usa datos simulados y no llama al backend.

## Fuente única de verdad

`scenarioMatrix.ts` define cada escenario. La UI conserva solo `role`, `scenarioId`, `location` y la parada seleccionada. Estado del viaje, estado del pasajero, textos, progreso, métricas, parada y acción se derivan de la definición seleccionada. Cambiar de rol selecciona un escenario válido para ese rol; ningún componente mantiene copias independientes del estado.

## Matriz de estados y acciones

| Rol | Escenario | Estado pasajero | Acción principal |
|---|---|---|---|
| Pasajero | Reserva confirmada | Confirmado | Ver detalles |
| Pasajero | Punto acordado | Punto acordado | Revisar indicaciones |
| Pasajero | Todavía no está listo | No listo | Confirmar que estoy listo |
| Pasajero | Pasajero listo | Listo | Esperar al conductor |
| Pasajero | Conductor en camino | Listo | Abrir indicaciones |
| Pasajero | Conductor llegó | Listo | Llegué al punto |
| Pasajero | Pasajero abordado | A bordo | Ver próxima parada |
| Pasajero | Viaje en curso | A bordo | Ver recorrido |
| Pasajero | Finalizado | Completado | Ver resumen |
| Pasajero | Cancelado | Cancelado | Ver detalles |
| Conductor | Preparando salida | Pendientes | Preparar salida |
| Conductor | Pasajeros pendientes | Pendientes | Salir hacia el punto |
| Conductor | Conductor en camino | Ramón listo | Llegué |
| Conductor | Llegada al punto | Esperando abordaje | Confirmar pasajero abordado |
| Conductor | Recogida de pasajero | Ramón a bordo | Iniciar viaje |
| Conductor | Viaje en curso | A bordo | Continuar recorrido |
| Conductor | Finalizado | Completado | Ver resumen |
| Conductor | Cancelado | Cancelado | Ver detalles |

Los textos hablan al pasajero en segunda persona (`Tu punto de encuentro`, `Rubén llegó`) y al conductor en términos operativos (`Próxima recogida`, `Confirmar pasajero abordado`). Chat, indicaciones y compartir estado son secundarios.

## Mapa y selección

El mapa es un SVG local compacto: origen, ruta, cinco marcadores, conductor demo y destino. No necesita tiles. Seleccionar un paso o una parada actualiza el marcador destacado; seleccionar el marcador también actualiza el detalle inferior. Ubicación ausente y desactualizada se comunican con texto, opacidad y forma, no solo color.

## Timeline y próxima parada

Cada paso presenta contexto realista: hora o `Ahora`, lugar general y última actualización. Completados usan su información histórica, el actual incluye etiqueta textual, pendientes bajan jerarquía y cancelados tienen tratamiento explícito. La próxima parada muestra posición, persona o propósito, zona, hora demo y pasajeros a bordo sin revelar dirección completa.

## Responsive y accesibilidad

- 1366 px: dos columnas; acción principal dentro de la columna izquierda.
- 768 px: una columna con mapa temprano y controles compactos.
- 390/360 px: títulos moderados, laboratorio colapsable, mapa bajo, botones táctiles y barra inferior con `safe-area`.
- El contenido reserva espacio inferior y no tiene scroll horizontal.
- Labels asociados, foco visible, `aria-current`, nombres de botón y estados textuales.

## Reglas contra inconsistencias

1. No definir copias de estado dentro de componentes presentacionales.
2. Toda acción y texto sale de `ScenarioDefinition`.
3. El índice actual deriva timeline, parada, mapa y ocupación.
4. Las métricas demo se etiquetan como tales y deben mantener relación distancia/tiempo.
5. No mostrar datos privados, coordenadas ni acciones reales.

## Pendiente de integración

Validar este prototipo con usuarios y luego diseñar un adaptador entre respuestas actuales y `ScenarioDefinition`. Aún faltan contratos reales de etapas/paradas, transiciones autorizadas, timestamps, ocupación y conexión con chat/mapa; no deben implementarse antes de esa validación.
# Integración con datos reales

La página real consume un único contrato autorizado por reserva. El backend define la próxima acción, sus permisos y si requiere confirmación; el cliente no inventa transiciones. El recorrido usa paradas persistidas cuando existen y un esquema derivado de origen, punto acordado y destino para datos históricos.

Transiciones del conductor: `publicado|completo|programado → preparando_salida → conductor_en_camino → conductor_en_punto → abordaje → en_curso ↔ pausado → finalizado`. Los estados heredados se mantienen como entradas compatibles.

Estados del pasajero: `confirmado → listo → esperando → recogido → abordo → completado`. Cancelado y ausente son estados terminales operativos. Solo el pasajero modifica `listo/esperando`; solo el conductor confirma `recogido/abordo`.

Los cambios se persisten antes de publicarse por Redis. `/ws/hoja-ruta` usa tickets temporales de un solo uso y provoca una recarga consolidada, evitando estados parciales en pantalla. GPS en vivo no forma parte de esta integración.
