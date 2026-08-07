# Progreso Jahamina v1.0

## 2026-08-04 — Acciones de hoja de ruta en tiempo real

- Consolidada la máquina de estados y añadido `llego_al_punto` mediante migración incremental.
- Activada la acción principal autorizada por backend en `/reservas/{id}`.
- Eventos, mensajes de sistema y cambios de parada/ocupación son idempotentes y se publican después del commit.
- La hoja de ruta se actualiza con ticket WebSocket de un solo uso y Redis Pub/Sub.
- Corregidos título real, nombres de paradas, ocupación global y horarios sin cortes.
- Validación: 56 pruebas, Alembic check, ESLint y build aprobados.

## 2026-08-03 — Primera integración real de hoja de ruta

- `/reservas/{id}` consume un contrato consolidado de lectura.
- Cronología y paradas se derivan de reserva, viaje y punto de encuentro; no se añadieron migraciones.
- La pantalla real no expone controles de laboratorio, datos demo, ETA ni acciones de transición.
- Chat y punto de encuentro permanecen disponibles.
- Conductor y pasajero vinculado acceden; terceros reciben 404.
- Validación: 55 pruebas, Alembic check, ESLint y build aprobados.

## Fase 0 — Inventario y plan

Estado: completada.

## Fase 1 — Dependencias y configuración

Estado: completada.

- Manifiesto UTF-16 convertido a UTF-8 y normalizado.
- Eliminados duplicados, Passlib y python-decouple no usados.
- Agregados Alembic, Pytest y HTTPX.
- Creados `.env.example` y `.gitignore`.
- `compileall` e importación del backend correctos.

## Fase 2 — Alembic y base de datos

Estado: completada.

- PostgreSQL inspeccionado: esquema local sin filas y sin `alembic_version`.
- Migraciones incompatibles archivadas en `alembic/legacy_versions/`.
- Creada migración inicial v1 basada en los modelos actuales.
- Alembic usa la URL construida por settings; `alembic.ini` no contiene secretos.
- Eliminado `Base.metadata.create_all()` del arranque.
- Ciclo downgrade/upgrade y esquema verificados en PostgreSQL.

## Fase 3 — Pruebas automatizadas

Estado: completada.

- Creada suite Pytest transaccional para auth, JWT, viajes y pasajeros.
- Las pruebas usan PostgreSQL sin persistir datos.
- Añadido `pytest.ini` para resolución consistente del paquete `app`.
- 25 pruebas pasan en ambos comandos solicitados.

## Fase 4 — Calidad del backend

Estado: completada.

- Centralizada creación/autenticación de usuarios en el servicio existente.
- Agregados rollback y manejo de conflictos en escrituras.
- Consultas principales actualizadas a SQLAlchemy 2.
- Códigos 201, 403, 404 y 409 aplicados según contrato REST.
- CORS parametrizado y sin wildcard.
- Agregado `/health` con comprobación controlada de PostgreSQL.

## Fase 5 — Documentación del backend

Estado: completada.

- Creado README con instalación, Docker, Alembic, pruebas y contratos.
- Creados `docs/API.md` y `docs/ARCHITECTURE.md`.
- Documentadas reglas reales, limitaciones y roadmap sin secretos.

## Fase 6 — Docker profesional

Estado: completada.

- Actualizados Dockerfile y Compose sin secretos hardcodeados.
- PostgreSQL y API incluyen healthchecks y dependencia saludable.
- La API ejecuta Alembic antes de iniciar.
- Separados desarrollo con reload y override de producción.
- Documentados entornos Windows (`localhost:5433`) y Docker (`db:5432`).
- PostgreSQL 13 preservado porque existe un volumen activo de esa versión; no
  se intentó una actualización mayor destructiva.

## Fase 7 — Frontend web

Estado: completada.

- Creado frontend Next.js 16, TypeScript, App Router y Tailwind 4.
- Implementadas páginas de inicio, registro, login, viajes, creación, historial
  y perfil.
- Centralizado cliente HTTP y contexto de sesión.
- Agregados estados de carga/error, rutas privadas y confirmación de cancelación.
- Agregados overrides puntuales para advisories de runtime de PostCSS y Sharp;
  no se aplicó `audit fix --force`.
- ESLint fijado en la versión 9 compatible con los plugins de Next.
- Audit de runtime sin vulnerabilidades, lint y build correctos.

## Fase 8 — Integración backend y frontend

Estado: completada.

- CORS configurable permite `http://localhost:3000`.
- Contratos frontend derivados del OpenAPI real.
- Cliente maneja 401, 403, 404, 409, 422 y errores de red.
- Documentada ejecución simultánea.

## Fase 9 — Preparación para despliegue

Estado: completada, sin despliegue real.

- Creado `docs/DEPLOYMENT.md` con PostgreSQL, backend, frontend y verificaciones.
- Documentadas variables, comandos, healthcheck y riesgos.

## Fase 10 — Portfolio

Estado: completada.

- Creado `docs/PORTFOLIO.md` sin métricas inventadas.
- Incluidos textos para CV, LinkedIn y GitHub, capturas sugeridas y roadmap.

## Fase 11 — Auditoría final

Estado: completada.

- Backend compilado e importado correctamente.
- Alembic en `20260729_0001 (head)`.
- 27 pruebas backend aprobadas.
- Dockerfile construido y servicios PostgreSQL/API saludables.
- `/health`, `/docs` y `/openapi.json` respondieron 200 en Docker.
- Flujo HTTP real validado: registro, login, perfil, creación, listado, unión,
  consultas y cancelación; datos temporales eliminados.
- Frontend con audit de runtime en cero, lint limpio y build aprobado.
- Uvicorn local validado y proceso temporal cerrado.

## Riesgos y validaciones pendientes

- PostgreSQL 13 debe actualizarse mediante `pg_dump/pg_restore` planificado; no
  se modificó la versión mayor por existir un volumen activo.
- `npm audit` completo reporta advisories altos en globbing del tooling ESLint;
  `npm audit --omit=dev` reporta cero vulnerabilidades de runtime. Forzar el fix
  rompe dependencias compatibles.
- La sesión web usa `localStorage` por alcance MVP; antes de producción conviene
  evaluar cookies HttpOnly y protección CSRF.
- Faltan CI, rate limiting y monitoreo externo para operación pública.

### Estado actual

- Backend FastAPI conectado a PostgreSQL y rutas principales operativas.
- JWT/OAuth2, modelos y schemas Pydantic 2 presentes.
- Docker Compose contiene PostgreSQL y API.
- Git estaba limpio al iniciar esta tarea.
- No existían README, `.gitignore`, ejemplos de entorno ni pruebas.

### Riesgos críticos

- Alembic apunta a SQLite y sus migraciones no representan los modelos.
- `Base.metadata.create_all()` oculta fallos de migración.
- CORS permite cualquier origen junto con credenciales.
- Operaciones de escritura no garantizan rollback ante error.
- Dependencias duplicadas; Passlib permanece aunque el código usa bcrypt.

### Deuda técnica

- Códigos HTTP y manejo de conflictos inconsistentes.
- Archivos auxiliares duplican responsabilidades.
- Falta configuración de CORS y healthcheck.
- Falta documentación, suite Pytest y frontend.

### Plan

1. Normalizar dependencias y configuración.
2. Reemplazar migraciones inválidas por una base inicial documentada.
3. Crear pruebas aisladas y corregir fallos.
4. Endurecer calidad, seguridad y códigos HTTP.
5. Documentar backend y arquitectura.
6. Profesionalizar Docker.
7. Implementar frontend MVP e integración.
8. Preparar despliegue y portfolio.
9. Ejecutar auditoría final.

## Registro

- 2026-07-29: inventario único completado sin leer ni modificar `.env`.
- 2026-07-29: creado `AGENTS.md` específico del proyecto.
- 2026-07-29: dependencias duplicadas y Passlib eliminados del manifiesto.
- 2026-07-29: pins actualizados por compatibilidad comprobada con Python 3.13.

## Pendientes

- Ninguna fase funcional pendiente; permanecen los riesgos preproducción
  documentados arriba.

## Evolución movilidad — vehículos, cupos y reservas

Estado: completado y validado.

- Agregados modelos `Vehiculo` y `SolicitudViaje`.
- `Viaje` ampliado con vehículo, cupos, puntos, descripción, coordenadas,
  estado y actualización.
- Creada migración incremental `20260729_0002`.
- Implementado CRUD privado y desactivación lógica de vehículos.
- Implementado flujo pendiente/aceptada/rechazada/cancelada/finalizada.
- Aceptación protegida con bloqueo PostgreSQL `FOR UPDATE`.
- Endpoint antiguo de unión deprecado y redirigido a solicitudes.
- Agregadas transiciones iniciar/finalizar y reglas de cupos.
- Suite ampliada a 34 pruebas, incluida concurrencia sin sobreventa y
  autorización de conductor/pasajero.
- Frontend ampliado con vehículos, cupos, paneles y detalle de reserva.
- Chat y GPS permanecen explícitamente fuera de alcance.
- Validación final: `python -m compileall app` correcto.
- Validación final: 34 pruebas Pytest aprobadas.
- Alembic en `20260729_0002 (head)` y sin operaciones pendientes.
- Migración validada en una base temporal limpia con upgrade, downgrade y
  nuevo upgrade; la base principal no fue degradada.
- Frontend validado con ESLint y build de producción de Next.js.

## Chat seguro en tiempo real

Estado: completado y validado.

- Conversaciones únicas por reserva y mensajes persistidos en PostgreSQL.
- Creación automática y mensaje de sistema al aceptar.
- Historial por cursor, respaldo REST, lectura y contadores de no leídos.
- Tickets WebSocket de un solo uso en Redis, Pub/Sub y rate limiting.
- WebSocket privado con mensajes, lectura, typing, ping/pong y reconexión.
- Escritura cerrada al cancelar/finalizar, con historial conservado.
- Frontend responsive con estados de entrega, reintento y no leídos.
- GPS, mapas, adjuntos y notificaciones push permanecen fuera de alcance.
- Suite ampliada a 41 pruebas aprobadas.
- Migración `20260730_0003` validada con upgrade/downgrade en base temporal.
- Redis 7.4 saludable, Compose válido, frontend con lint y build correctos.
- Reservas relacionadas unificadas para conductor y pasajero, con actividad,
  conversación y no leídos coherentes entre listado, detalle y navbar.

## Mapas, punto de encuentro y seguimiento

Estado: completado y validado.

- Viajes ampliados con coordenadas, puntos operativos, distancia, duración y ruta simplificada.
- Geocodificación y rutas desacopladas mediante servicios configurables, timeout y caché Redis.
- Punto de encuentro privado con propuesta, confirmación, rechazo y mensajes de sistema idempotentes.
- Seguimiento con consentimiento explícito, ciclo de vida en PostgreSQL y última posición activa en Redis.
- WebSocket de ubicación con tickets efímeros de un solo uso, roles publisher/subscriber y Pub/Sub.
- Frontend con MapLibre, selección visual de trayecto y panel de ubicación en la reserva.
- Privacidad: no se conserva historial detallado del recorrido ni se inicia GPS automáticamente.
- Suite completa: 45 pruebas aprobadas; compileall correcto.
- Migración `20260731_0004` validada con upgrade/downgrade en base temporal y `alembic check` limpio.
- Frontend validado con ESLint y build de producción; Docker Compose, imagen, health y OpenAPI correctos.

## Login desde red local

- Formulario protegido contra envío GET aun antes de la hidratación.
- Cliente OAuth2 usa exclusivamente `NEXT_PUBLIC_API_URL` validada y detecta loopback desde dispositivos LAN.
- CORS explícito para localhost, 127.0.0.1 y 192.168.0.107.
- Login directo, preflight, esquema PostgreSQL y migraciones verificados sin modificar datos.
- URLs WebSocket de chat y ubicación comparten configuración validada con conversión HTTP/HTTPS a WS/WSS.
- Validación final: 51 pruebas, lint y build correctos; login LAN alcanza la API mediante POST.
- 2026-08-03: detectado cambio DHCP de `192.168.0.107` a `192.168.1.20`; configuración LAN actualizada sin exponer secretos.

## Prototipo visual de hoja de ruta

- Creada demo local `/dev/hoja-ruta` con datos simulados y sin llamadas al backend.
- Componentes reutilizables para estado, mapa local, timeline, paradas, vehículo, pasajeros, acciones y acceso al chat.
- Variantes de rol, ciclo del viaje y disponibilidad de ubicación.
- Diseño responsive validado con ESLint y build de producción.
- Pendiente: validar la experiencia con usuarios antes de definir contratos o estados de backend.
- Refinamiento: matriz única de 18 escenarios, lenguaje por rol, selección sincronizada mapa/timeline/paradas y acción no superpuesta en escritorio.
# 2026-08-03 — Hoja de ruta conectada

- Añadido contrato consolidado `GET /reservas/{id}/hoja-ruta`, autorizado para conductor y pasajero aceptado.
- Incorporada máquina de estados operativa de viaje y estado individual del pasajero.
- Añadidas paradas y eventos persistentes mediante migración incremental `20260803_0005`.
- Acciones idempotentes generan eventos y mensajes de sistema; Redis publica cambios tras el commit.
- Añadido WebSocket `/ws/hoja-ruta` con ticket corto y de un solo uso.
- La página real `/reservas/{id}` reutiliza el lenguaje visual del prototipo y conserva chat/punto de encuentro.
- Validación: compileall OK, 54 pytest OK, Alembic upgrade/check OK, ESLint OK, Next build OK.

# 2026-08-04 — Ubicación y ETA en hoja de ruta

- Reutilizado `SeguimientoViaje`, Redis Pub/Sub y tickets WebSocket de un solo uso; no se creó otra tabla.
- El permiso del navegador precede a la activación de compartir y existe un único watcher con limpieza al desmontar.
- Añadido contexto autorizado de posición, próxima parada, distancia vial y ETA mediante OSRM.
- ETA con caché corta y agrupación de posición; una ubicación stale nunca muestra ETA como vigente.
- La hoja de ruta sigue siendo principal y el mapa queda como panel compacto de apoyo.
- No se almacena historial de posiciones ni se inicia geolocalización automáticamente.

# 2026-08-04 — Simplificación de la experiencia principal

- La página real muestra exactamente cinco etapas: reserva, punto acordado, conductor en camino, viaje en curso y finalización.
- Los estados técnicos permanecen en backend, pero ya no se presentan al usuario.
- Se retiraron de la pantalla principal la ubicación, ETA, ocupación repetida, lista operativa de paradas y acciones intermedias.
- Se conserva un único botón principal, el recorrido esquemático compacto, el punto de encuentro y el chat.
- `/dev/hoja-ruta` permanece disponible como referencia del prototipo previo.
- Flujo real conectado a tres acciones del conductor: salir, iniciar y finalizar, sin transiciones visibles intermedias.
- Cada acción conserva eventos y mensajes de sistema idempotentes y difunde `roadmap.updated` tras confirmar la transacción.

# 2026-08-04 — Alcance geográfico Paraguay

- Geocodificación limitada a `py` con `bounded=1`, viewbox, address details y filtrado defensivo.
- Validación backend central para viajes, puntos de encuentro, rutas y ubicación activa.
- MapLibre inicia, se encuadra y limita a los límites operativos de Paraguay.
- Origen, destino, punto de salida y punto de llegada requieren selecciones con coordenadas válidas.
- La ubicación del dispositivo fuera de Paraguay se rechaza con un mensaje explícito.

# 2026-08-04 — Publicación de viaje en tres etapas

- La publicación real se organiza en `Recorrido`, `Detalles` y `Confirmación`, sin cambiar el contrato del backend.
- El mapa queda como apoyo lateral en escritorio y vista compacta superior en móvil.
- La búsqueda reutilizable incorpora estados claros de carga, ausencia de resultados y error del proveedor.
- La confirmación permite editar cada bloque sin perder los datos y mantiene una única acción principal.
- Se conserva `/dev/publicar-viaje` como comparación visual con datos simulados.
- Validación: ESLint y build de producción de Next.js aprobados.

# 2026-08-04 — Notificaciones internas y Web Push

- Añadidas notificaciones persistentes e idempotentes y suscripciones Push por dispositivo.
- Redis/WebSocket actualiza la campana sin recargar; Web Push es complementario y nunca revierte la acción principal.
- Integrados mensajes, solicitudes, aceptación/rechazo, punto confirmado, salida, inicio, cancelación y finalización.
- Añadidos Service Worker, manifiesto PWA, permiso contextual y apertura segura de rutas internas.
- VAPID permanece desactivado por defecto y no se versionaron claves reales.

# 2026-08-04 — Sistema visual oficial, fase 1

- Consolidada la base visual con tokens semánticos, tipografía de sistema y jerarquía consistente.
- Header superior responsive con navegación activa, menú móvil, cuenta y notificaciones; sin sidebar.
- Rediseñada `/reservas/{id}` con datos reales, estado principal, cinco pasos, recorrido compacto, punto y chat.
- Se conservaron acciones, WebSockets, mapas y contratos existentes sin cambios de backend.
- ESLint y build de producción aprobados.
# Actualización 2026-08-04 — Sistema visual oficial, fase 2

- Se extendió la identidad visual oficial a login, registro, viajes disponibles, publicación, mis viajes, reservas, vehículos, perfil y notificaciones.
- Se añadieron primitivas compartidas para encabezados, superficies, estados asíncronos y contraseñas visibles/ocultas.
- Se conservaron contratos API, lógica de autenticación, mapas, chat, WebSockets y notificaciones.
- Validaciones: `npm run lint` y `npm run build` aprobados; `git diff --check` sin errores.

# 2026-08-07 — Reanudación de Web Push/VAPID

- Auditado el trabajo previo sin reescribir ni revertir cambios existentes: configuración VAPID, suscripciones autenticadas por dispositivo, Service Worker seguro, activación explícita, eventos de negocio, chat y documentación ya estaban implementados.
- Completados unsubscribe del dispositivo actual y limpieza segura en logout/cambio de usuario, presencia de chat para evitar Push mientras el destinatario está conectado y respuesta verificable del endpoint de prueba.
- Los errores 404/410 desactivan la suscripción; 401/403 se registran sin endpoint, claves ni payload y conservan el dispositivo para corregir VAPID sin obligar a una nueva suscripción.
- El generador local reutiliza `py-vapid`, imprime las claves una sola vez y no crea archivos. No se generaron ni versionaron claves reales.
- Validación local: `compileall`, importación/OpenAPI, contratos frontend Push, lint, build y `git diff --check` correctos. La suite completa y `alembic check` quedan bloqueados porque PostgreSQL local no está escuchando en `localhost:5433` y Docker Desktop no está iniciado.
- Pendiente operativo: iniciar PostgreSQL/Docker y repetir Pytest/Alembic; después cargar secretos en Render/Vercel, redesplegar y probar en Android con HTTPS.

# 2026-08-07 — Rediseño de publicación de viaje

- `/viajes/nuevo` conserva el flujo real de tres pasos, validaciones, búsqueda limitada a Paraguay, cálculo vial, marcadores movibles y contrato de publicación.
- Cabecera y stepper unificados con jerarquía de producto; el mapa real permanece visible como protagonista en ruta, detalles y confirmación.
- Eliminada la vista esquemática redundante de esta pantalla y consolidado el recorrido en una tarjeta compacta con origen, destino, distancia y duración.
- Inputs, sugerencias, selector de vehículo, asientos, revisión y acciones adoptan radios, sombras, estados de foco y espaciado consistentes con Jahamina.
- Responsive mobile-first con mapa prioritario, controles táctiles altos y acciones persistentes; desktop utiliza una composición equilibrada de panel y mapa.
- Validación aprobada con ESLint, build de producción de Next.js y `git diff --check`.

# 2026-08-07 — Segunda pasada premium de publicación

- Auditada visualmente la ruta demo en anchos de referencia móvil, tablet y desktop; las capturas y la ruta auxiliar fueron temporales y se eliminaron al terminar.
- Refinados proporciones, pesos tipográficos, escala de espacios, stepper y superficies sin alterar el flujo ni sus contratos.
- El mapa conserva la mayor presencia, con trazo profundo, halo suave y marcadores propios para origen, destino y puntos secundarios.
- El resumen quedó reducido a origen, destino y métricas únicamente cuando existe un cálculo vial real; estados breves reemplazan títulos repetidos.
- Origen/destino incorporan conexión visual, autocomplete compacto y estados de foco; Detalles y Confirmación mantienen jerarquías y acciones de edición claras.
- El CTA de ruta vuelve a pertenecer al formulario, eliminando el vacío que producía el alto del mapa en desktop; móvil queda protegido contra desborde horizontal.
- Validación final aprobada: ESLint, build de producción de Next.js y `git diff --check`.

# 2026-08-07 — Corrección de detección Web Push en frontend

- Identificada la causa del falso estado no configurado: la tarjeta y los helpers exigían `NEXT_PUBLIC_VAPID_PUBLIC_KEY` antes de consultar la configuración pública del backend.
- `GET /notificaciones/configuracion-push` pasa a ser la fuente autoritativa para `enabled` y `public_key`; la variable de Vercel queda únicamente como fallback público cuando el backend está habilitado.
- La carga distingue comprobación, disponible, suscrito, permiso denegado, navegador incompatible, contexto inseguro, backend deshabilitado y error de red.
- `Notification.requestPermission()` continúa ejecutándose solamente tras pulsar **Activar notificaciones**.
- Restauración, unsubscribe, Service Worker, logout y registro por dispositivo permanecen sin cambios funcionales.
- Contratos Push ampliados y contratos visuales previamente desactualizados alineados con el diseño vigente.
- Validación: 126 pruebas Pytest, ESLint, build de producción de Next.js y `git diff --check` aprobados.

# 2026-08-07 — Panel premium de viaje compartido

- La reserva aceptada conserva su carga real, WebSocket, permisos, acciones de etapa, punto de encuentro y chat; el cambio es de presentación y composición.
- El estado actual pasa a ser un hero verde con conductor, datos reales del vehículo, ocupación, salida y próxima acción claramente jerarquizados.
- Se incorporó `VehicleImage`, preparado para una URL pública segura y con una ilustración SVG local cuando el backend todavía no entrega fotografía.
- La ruta gana presencia, marcadores diferenciados, parada seleccionada y salida programada; si no existen paradas, se mantiene un fallback visual sin inventar distancia ni duración.
- Hoja de ruta, encuentro, preview de chat e información usan superficies, espaciado y orden responsive consistentes con Jahamina.
- Validación final aprobada: ESLint, build de producción de Next.js, 126 pruebas Pytest y `git diff --check`.

# 2026-08-07 — Tercera pasada del viaje compartido

- El hero mantiene estructura y acciones, pero cambia el bloque verde sólido por una superficie clara crema/verde con acento lateral y headline más contenido.
- Conductor y vehículo ganan jerarquía: avatar opcional seguro, iniciales refinadas y `VehicleImage` con prioridad foto real, catálogo opcional e ilustración automotriz local.
- La ilustración fallback usa una vista en perspectiva, volumen, cristales, luces y ruedas detalladas; los datos del vehículo quedan en una franja blanca independiente.
- Métricas y próxima acción tienen mayor aire, iconografía discreta y un CTA naranja menos dominante.
- La hoja de ruta aumenta su ritmo vertical, suaviza el paso actual y reduce el peso visual del contador.
- Validación aprobada: ESLint, build de producción de Next.js, 126 pruebas Pytest y `git diff --check`.
