# Jahamina

Jahamina es una plataforma MVP de viajes compartidos orientada a conectar
personas que realizan trayectos compatibles. La API permite gestionar usuarios,
viajes y participaciones conservando el historial mediante cancelación lógica.

## Funcionalidades

- Registro con email normalizado y contraseña bcrypt.
- Login OAuth2 y autenticación JWT.
- Consulta del perfil autenticado.
- Creación, listado y cancelación lógica de viajes.
- Vehículos propios, cupos y aprobación de solicitudes.
- Chat privado en tiempo real para reservas aceptadas.
- Validación de fechas, ubicaciones y permisos.
- Swagger, healthcheck, migraciones Alembic y pruebas automatizadas.

## Stack

- Python 3.11+, FastAPI, Pydantic 2
- SQLAlchemy 2, PostgreSQL y Alembic
- JWT/OAuth2 y bcrypt
- Pytest y HTTPX
- Docker y Docker Compose
- Next.js, TypeScript y Tailwind CSS

## Arquitectura

Las rutas HTTP delegan reglas y persistencia a servicios. Los schemas Pydantic
definen el contrato público y los modelos SQLAlchemy representan PostgreSQL.
La configuración se obtiene del entorno y Alembic es la fuente oficial del
esquema. Consulta [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Requisitos

- Python 3.11 o superior
- PostgreSQL 13 o superior, o Docker Desktop
- Node.js 20 o superior para el frontend

## Configuración

Copia `.env.example` a `.env` y completa valores locales:

```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000
REDIS_URL=redis://localhost:6379/0
```

Usa una clave JWT larga y aleatoria. Nunca versiones `.env`.

## Instalación local en Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
docker compose up -d db
alembic upgrade head
python -m uvicorn app.main:app --reload
```

La API estará en `http://localhost:8000`.

## Docker

PostgreSQL solamente:

```powershell
docker compose up -d db
```

Stack completo de desarrollo:

```powershell
Copy-Item .env.docker.example .env.docker
# Completar .env.docker con valores locales
docker compose --env-file .env.docker up -d --build
```

Producción local, sin recarga:

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml `
  --env-file .env.docker up -d --build
```

## Migraciones

```powershell
alembic current
alembic history
alembic upgrade head
alembic downgrade -1
```

No uses `Base.metadata.create_all()` para evolucionar el esquema.

## Pruebas

Las pruebas usan transacciones PostgreSQL revertidas:

```powershell
pytest -q
pytest --disable-warnings --maxfail=1
```

## Backend y frontend simultáneos

Terminal 1:

```powershell
docker compose up -d db
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Terminal 2:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Abre `http://localhost:3000`. La API debe permitir ese origen mediante
`CORS_ORIGINS`.

## Swagger

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Salud: `http://localhost:8000/health`

En Swagger, usa **Authorize** con el email en `username` y la contraseña.

## Endpoints principales

| Método | Ruta | Autenticación |
|---|---|---|
| GET | `/health` | No |
| POST | `/auth/registro` | No |
| POST | `/auth/login` | No |
| GET | `/auth/me` | JWT |
| POST/GET/PATCH | `/vehiculos` | JWT |
| POST | `/viajes/` | JWT |
| GET | `/viajes/disponibles` | JWT |
| GET | `/viajes/mis-viajes` | JWT |
| GET | `/viajes/unidos` | JWT |
| PUT | `/viajes/unirse/{viaje_id}` | JWT |
| PUT | `/viajes/cancelar/{viaje_id}` | JWT |
| POST | `/viajes/{viaje_id}/solicitudes` | JWT |
| GET | `/solicitudes/mias` | JWT |
| PATCH | `/solicitudes/{id}/aceptar` | JWT |
| PATCH | `/solicitudes/{id}/rechazar` | JWT |
| PATCH | `/solicitudes/{id}/cancelar` | JWT |
| GET | `/reservas/relacionadas` | JWT |
| GET | `/reservas/{id}/conversacion` | JWT |
| GET/POST | `/conversaciones/{id}/mensajes` | JWT |
| POST | `/conversaciones/{id}/ws-ticket` | JWT |
| WS | `/ws/chat?ticket=...` | Ticket efímero |

El contrato completo está en [docs/API.md](docs/API.md).

## Ejemplos

Registro:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/registro `
  -ContentType 'application/json' `
  -Body '{"nombre":"Ana","email":"ana@example.com","password":"Password123"}'
```

Login:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/login `
  -ContentType 'application/x-www-form-urlencoded' `
  -Body 'username=ana%40example.com&password=Password123'
```

Crear viaje con un token almacenado en `$token`:

```powershell
$headers = @{ Authorization = "Bearer $token" }
$body = '{"origen":"Asunción","destino":"San Lorenzo","fecha":"2030-01-01T09:00:00"}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/viajes/ `
  -Headers $headers -ContentType 'application/json' -Body $body
```

## Reglas de negocio

- Email único y normalizado a minúsculas.
- Contraseña entre 8 caracteres y 72 bytes.
- Viajes futuros con origen y destino distintos.
- El conductor no puede ser pasajero de su viaje.
- Una participación por usuario y viaje.
- Solo el creador cancela; la cancelación conserva el historial.
- Viajes pasados o cancelados no aparecen como disponibles.
- Los cupos respetan la capacidad del vehículo.
- El lugar se reserva cuando el conductor acepta la solicitud.
- Cancelar una reserva aceptada devuelve el cupo antes del inicio.
- Solo conductor y pasajero acceden al chat; al cerrar viaje o reserva el
  historial sigue visible y la escritura queda deshabilitada.

## Estructura

```text
app/
  api/routes/   Endpoints
  core/         Configuración, DB, JWT y seguridad
  models/       Entidades SQLAlchemy
  schemas/      Contratos Pydantic
  services/     Reglas y persistencia
alembic/        Migraciones
tests/          Pruebas backend
docs/           Documentación
frontend/       Aplicación Next.js
```

## Problemas conocidos

- El MVP no gestiona precios, archivos en chat ni seguimiento GPS.
- La suite necesita una instancia PostgreSQL de desarrollo accesible.

## Roadmap

Cupos, precios, vehículos, reservas, puntos de encuentro, mapas,
notificaciones, calificaciones, chat y aplicación móvil Flutter.

Consulta [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) y
[docs/PORTFOLIO.md](docs/PORTFOLIO.md).

## Autor

Completar con el nombre del responsable del repositorio.
