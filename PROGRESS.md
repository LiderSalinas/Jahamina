# Progreso Jahamina v1.0

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
