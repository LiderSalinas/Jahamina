# API Jahamina v1

Base local: `http://localhost:8000`.

Las rutas privadas usan `Authorization: Bearer <token>`. Los errores siguen el
formato FastAPI `{"detail": "mensaje"}` o la estructura 422 de Pydantic.

## Sistema

### GET `/health`

- Autenticación: no.
- Respuesta 200: `{"status":"ok"}`.
- Posibles códigos: 200, 503 si PostgreSQL no responde.

## Autenticación

### POST `/auth/registro`

- Autenticación: no.
- Content-Type: `application/json`.
- Payload:

```json
{"nombre":"Ana","email":"ana@example.com","password":"Password123"}
```

- Respuesta 201:

```json
{"id":1,"nombre":"Ana","email":"ana@example.com"}
```

- Posibles códigos: 201, 409 email duplicado, 422 datos inválidos.

### POST `/auth/login`

- Autenticación: no.
- Content-Type: `application/x-www-form-urlencoded`.
- Campos: `username` contiene el email; `password` contiene la contraseña.
- Respuesta 200:

```json
{"access_token":"<jwt>","token_type":"bearer"}
```

- Posibles códigos: 200, 401 credenciales incorrectas, 422 formulario inválido.

### GET `/auth/me`

- Autenticación: JWT.
- Payload: ninguno.
- Respuesta 200: usuario sin contraseña ni hash.
- Posibles códigos: 200, 401 token ausente, inválido, expirado o sin usuario.

## Viajes

Objeto de viaje:

```json
{
  "id": 1,
  "origen": "Asunción",
  "destino": "San Lorenzo",
  "fecha": "2030-01-01T09:00:00",
  "cancelado": false,
  "creador_id": 1
}
```

### POST `/viajes/`

- Autenticación: JWT.
- Payload:

```json
{"origen":"Asunción","destino":"San Lorenzo","fecha":"2030-01-01T09:00:00"}
```

- Respuesta: 201 con el viaje.
- Posibles códigos: 201, 401, 422.

### GET `/viajes/disponibles`

- Autenticación: JWT.
- Respuesta: 200 con lista de viajes futuros no cancelados.
- Posibles códigos: 200, 401.

### GET `/viajes/mis-viajes`

- Autenticación: JWT.
- Respuesta: 200 con todos los viajes creados por el usuario, incluido historial
  cancelado.
- Posibles códigos: 200, 401.

### PUT `/viajes/cancelar/{viaje_id}`

- Autenticación: JWT.
- Payload: ninguno.
- Respuesta: 200 con el viaje y `cancelado: true`.
- Posibles códigos: 200, 400 ya cancelado, 401, 403 no es creador, 404.

## Pasajeros

### PUT `/viajes/unirse/{viaje_id}`

- Autenticación: JWT.
- Payload: ninguno.
- Respuesta 201:

```json
{"id":1,"viaje_id":1,"usuario_id":2}
```

- Posibles códigos: 201, 400 viaje cancelado, pasado o propio, 401, 404, 409
  participación duplicada.

### GET `/viajes/unidos`

- Autenticación: JWT.
- Respuesta: 200 con viajes no cancelados a los que se unió el usuario.
- Posibles códigos: 200, 401.

## Vehículos

- `POST /vehiculos`: crea un vehículo; 201 o 409 por matrícula duplicada.
- `GET /vehiculos`: lista solo vehículos propios.
- `GET /vehiculos/{id}`: detalle privado del propietario.
- `PATCH /vehiculos/{id}`: edición parcial.
- `PATCH /vehiculos/{id}/desactivar`: desactivación lógica.

La capacidad válida es 1 a 8 y la matrícula se normaliza a mayúsculas sin
espacios ni guiones.

## Solicitudes y reservas

- `POST /viajes/{viaje_id}/solicitudes`: solicitud pendiente.
- `GET /reservas/relacionadas`: reservas como pasajero y conductor, con
  conversación, participante, última actividad y no leídos.
- `GET /solicitudes/mias`: historial del pasajero.
- `GET /viajes/{viaje_id}/solicitudes`: panel privado del conductor.
- `GET /solicitudes/{id}`: detalle para sus participantes.
- `PATCH /solicitudes/{id}/aceptar`: acepta y descuenta cupo.
- `PATCH /solicitudes/{id}/rechazar`: rechaza sin descontar.
- `PATCH /solicitudes/{id}/cancelar`: cancela sin borrado físico.

Estados: `pendiente`, `aceptada`, `rechazada`, `cancelada`, `finalizada`.
`/viajes/unirse/{id}` está deprecado y ahora crea una solicitud pendiente.

## Chat

Todas las rutas son privadas y responden 404 a usuarios ajenos para no revelar
conversaciones. El chat se crea al aceptar una reserva.

- `GET /reservas/{id}/conversacion`: resumen, participante, viaje y no leídos.
- `GET /conversaciones/{id}`: detalle autorizado.
- `GET /conversaciones/{id}/mensajes?before_id=&limit=`: historial por cursor.
- `POST /conversaciones/{id}/mensajes`: respaldo REST con `contenido` y
  `client_message_id` opcional.
- `PATCH /conversaciones/{id}/leido`: marca mensajes ajenos como leídos.
- `GET /conversaciones/no-leidos`: total y desglose por conversación.
- `POST /conversaciones/{id}/ws-ticket`: ticket aleatorio de un solo uso.
- `WS /ws/chat?ticket=...`: tiempo real sin JWT permanente en URL.

Eventos cliente: `message.send`, `message.read`, `typing.start`, `typing.stop`,
`ping`. Eventos servidor: `connected`, `message.created`, `message.read`,
`typing.started`, `typing.stopped`, `error`, `pong`.

## Mapas, encuentro y seguimiento

- `GET /mapas/geocodificar?q=`: sugerencias geográficas cacheadas.
- `POST /mapas/ruta`: distancia, duración y geometría aproximadas.
- `GET /reservas/{id}/punto-encuentro`: punto privado de participantes.
- `POST /reservas/{id}/punto-encuentro/proponer`: propone coordenadas y texto.
- `PATCH /reservas/{id}/punto-encuentro/confirmar`: confirma el punto vigente.
- `PATCH /reservas/{id}/punto-encuentro/rechazar`: rechaza el punto vigente.
- `POST /viajes/{id}/seguimiento/iniciar`: inicia viaje sin compartir automáticamente.
- `PATCH /viajes/{id}/seguimiento/{pausar|reanudar|finalizar}`: cambia el ciclo.
- `PATCH /viajes/{id}/seguimiento/compartir`: consentimiento explícito del conductor.
- `GET /viajes/{id}/seguimiento`: estado privado.
- `GET /viajes/{id}/ubicacion-actual`: última posición e indicador `stale`.
- `POST /viajes/{id}/ubicacion`: respaldo HTTP del publicador.
- `POST /viajes/{id}/ubicacion/ws-ticket`: ticket efímero por rol.
- `WS /ws/ubicacion?ticket=...`: tiempo real privado.

El WebSocket emite `connected`, `location.updated`, `tracking.finished`, `error` y `pong`; acepta `location.update` y `ping`. Las rutas privadas responden 404 a terceros.
# Hoja de ruta

## Contrato consolidado de lectura

`GET /reservas/{id}/hoja-ruta` reúne reserva, viaje, conductor, pasajero actual, vehículo, punto de encuentro, ocupación, cronología y paradas derivadas. Requiere JWT; devuelve 404 a terceros o IDs inexistentes y 409 para una reserva pendiente. No expone email, contraseñas, tokens ni información privada de otros pasajeros.

La primera integración visual usa este endpoint solo para lectura. No interpreta las paradas como geometría vial ni presenta ETA o GPS.

- `GET /reservas/{id}/hoja-ruta`: contrato consolidado para conductor o pasajero aceptado; terceros reciben 404.
- `POST /viajes/{id}/acciones/{accion}`: acciones del conductor (`preparar-salida`, `salir`, `llegar`, `iniciar`, `pausar`, `reanudar`, `finalizar`).
- `POST /reservas/{id}/acciones/{accion}`: acciones individuales (`listo`, `llegue`, `recoger`, `abordar`) según rol.
- `POST /reservas/{id}/hoja-ruta/ws-ticket`: ticket temporal de un solo uso.
- `WS /ws/hoja-ruta?ticket=...`: emite `trip.status.changed`, `passenger.status.changed` y confirma conexión con `connected`.

Las transiciones inválidas devuelven 409; recursos privados no autorizados devuelven 404.
