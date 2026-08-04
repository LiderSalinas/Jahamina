# Jahamina

## Propósito

Jahamina es una plataforma de viajes compartidos. Un usuario puede registrarse,
autenticarse, crear y cancelar lógicamente viajes, y unirse como pasajero.

## Stack

- Python 3.11+, FastAPI, Pydantic 2
- SQLAlchemy 2, PostgreSQL, Alembic
- JWT/OAuth2, bcrypt
- Pytest y HTTPX
- Docker y Docker Compose
- Next.js, TypeScript y Tailwind CSS en `frontend/`

## Arquitectura

- `app/api/routes/`: endpoints HTTP.
- `app/services/`: reglas de negocio y persistencia.
- `app/models/`: modelos SQLAlchemy.
- `app/schemas/`: contratos Pydantic.
- `app/core/`: configuración, base de datos, JWT y seguridad.
- `alembic/`: evolución oficial del esquema.
- `tests/`: pruebas aisladas.
- `docs/`: documentación técnica.

No reestructurar el proyecto ni renombrar carpetas sin una necesidad comprobada.

## Reglas de negocio

- Los emails son únicos y se normalizan a minúsculas.
- Las contraseñas tienen 8 a 72 bytes y nunca se exponen.
- Todo endpoint de viajes requiere JWT.
- Un viaje debe ser futuro y tener origen y destino diferentes.
- El creador no puede unirse a su propio viaje.
- Un usuario no puede unirse dos veces al mismo viaje.
- No se puede unir a viajes cancelados o inexistentes.
- Solo el creador cancela su viaje.
- La cancelación es lógica y conserva el historial.
- Cada viaje nuevo usa un vehículo activo del conductor.
- Los cupos no superan la capacidad ni pueden ser negativos.
- Un pasajero solicita lugar y el conductor acepta o rechaza.
- Aceptar bloquea el viaje y descuenta un cupo sin sobreventa.
- Las solicitudes conservan historial y no se borran físicamente.
- El chat existe solo para reservas aceptadas y es privado para sus dos
  participantes; los tickets WebSocket son breves y de un solo uso.

## Comandos

```powershell
python -m uvicorn app.main:app --reload
pytest -q
alembic current
alembic upgrade head
alembic downgrade base
docker compose up -d --build
docker compose logs --tail=100 jahamina-api
```

Frontend:

```powershell
cd frontend
npm install
npm run lint
npm run build
npm run dev
```

## Seguridad

- Nunca leer, registrar, documentar ni versionar secretos reales.
- Configurar JWT, PostgreSQL y CORS mediante variables de entorno.
- No usar `allow_origins=["*"]` con credenciales.
- No registrar contraseñas, tokens ni hashes.
- Validar autenticación y autorización en servidor.
- No borrar datos sin verificar que la base sea de desarrollo o pruebas.
- La ubicación exige consentimiento explícito, acceso limitado a participantes y nunca debe registrarse en logs normales ni conservarse como recorrido detallado.

## Archivos ignorados

Ignorar `.env*` reales, entornos virtuales, `__pycache__`, `*.pyc`,
`node_modules`, `.next`, `dist`, `build`, logs y bases locales generadas.
Mantener versionados los archivos `*.example`.

## Validaciones obligatorias

- Antes de modificar: revisar `git status` y el diff relevante.
- Backend: `compileall`, importación, Pytest, Alembic y OpenAPI.
- Docker: `docker compose config`, estado, logs y `/health`.
- Frontend: lint y build.
- Registrar avances, decisiones y pendientes en `PROGRESS.md`.
- No declarar una fase completa si falla su validación.

## Git

No hacer commit ni push automáticamente. Preservar cambios ajenos y evitar
operaciones destructivas como `git reset --hard`.
