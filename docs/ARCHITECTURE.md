# Arquitectura de Jahamina

## Visión general

Jahamina mantiene una arquitectura por capas pequeña. FastAPI recibe y valida
HTTP, los servicios aplican reglas y SQLAlchemy persiste en PostgreSQL.

## Rutas

`app/api/routes/auth.py` expone registro, login y perfil.  
`app/api/routes/viajes.py` expone viajes y estados. `vehiculos.py` administra
la flota privada y `solicitudes.py` gestiona intención, aprobación y reserva.

Las rutas declaran dependencias, schemas y códigos HTTP; no almacenan secretos.

## Servicios

`user_service.py` crea y autentica usuarios. `viaje_service.py` concentra las
reglas de creación, consulta, cancelación y unión. Las escrituras hacen rollback
ante errores de base de datos.

Los módulos auxiliares restantes son adaptadores de compatibilidad y delegan en
las implementaciones principales.

## Modelos

- `Usuario`: identidad, email único y hash bcrypt.
- `Vehiculo`: propiedad, matrícula normalizada, capacidad y actividad.
- `Viaje`: trayecto, vehículo, cupos, puntos y ciclo de estado.
- `SolicitudViaje`: intención y reserva histórica del pasajero.
- `ViajeUnido`: relación pasajero-viaje con restricción única compuesta.

Las relaciones ORM conservan la navegación entre entidades.

Aceptar una solicitud bloquea con `SELECT ... FOR UPDATE` la solicitud y el
viaje. Así se serializan descuentos de cupos entre procesos.

## Schemas

Pydantic 2 valida emails, longitudes, límite bcrypt, ubicaciones y fechas.
Los schemas de respuesta omiten siempre `hashed_password`.

## Seguridad

OAuth2 Password Bearer recibe credenciales en `/auth/login`. JWT incluye el
email como `sub` y una expiración UTC timezone-aware. Cada ruta privada resuelve
el usuario actual desde PostgreSQL.

## Configuración

`app/core/settings.py` carga PostgreSQL, JWT y CORS desde variables de entorno.
La URL se construye con `SQLAlchemy.URL` para escapar credenciales correctamente.

## Base de datos

`app/core/db.py` administra el engine y sesiones por petición. PostgreSQL es la
única base soportada para ejecución y pruebas de integración.

## Migraciones

Alembic es la fuente oficial del esquema. `alembic/env.py` usa la misma URL y
metadata que la aplicación. `20260729_0001` define la línea base y
`20260729_0002` agrega vehículos, cupos y solicitudes. Los scripts
incompatibles anteriores están documentados en
`alembic/legacy_versions/` y no forman parte del grafo activo.

La aplicación no ejecuta `create_all` al iniciar; el despliegue debe ejecutar
`alembic upgrade head` antes de Uvicorn.

## Chat en tiempo real

`Conversacion` enlaza de forma única una reserva aceptada y `Mensaje` conserva
el historial en PostgreSQL. La autorización se deriva siempre del conductor y
pasajero persistidos. Redis almacena tickets efímeros, rate limiting y Pub/Sub
entre instancias. Si Redis falla, el historial continúa disponible, pero los
tickets y el tiempo real fallan cerrados. `20260730_0003` agrega las tablas e
índices.

## Mapas y ubicación

`map_service` abstrae geocodificación y rutas HTTP configurables. Redis limita y cachea consultas. `SeguimientoViaje` conserva el ciclo y solo la última posición en PostgreSQL; Redis mantiene la posición activa, tickets y Pub/Sub. El WebSocket separa publisher (conductor) y subscriber (pasajero aceptado). `20260731_0004` agrega columnas geográficas, acuerdo de encuentro y seguimiento sin reemplazar migraciones anteriores.
# Hoja de ruta operativa

`roadmap_service` centraliza autorización, transición de estados, eventos idempotentes, mensajes de sistema y el contrato de lectura. `ParadaViaje` ordena origen/recogidas/destino y `EventoViaje` conserva la cronología sin datos privados en metadata. Las rutas confirman la transacción antes de publicar el evento por Redis. El frontend vuelve a consultar el contrato consolidado ante cada evento WebSocket.
