# Preparación de despliegue

Esta guía es neutral. No requiere ni contiene credenciales reales. Render,
Railway, Vercel u otros proveedores equivalentes pueden cambiar sus interfaces;
verifica siempre su documentación vigente.

## Arquitectura recomendada

- PostgreSQL gestionado.
- Backend como servicio web basado en Docker o Python.
- Frontend Next.js en Vercel o plataforma compatible.
- HTTPS en ambos servicios.

## 1. Crear PostgreSQL

1. Crea una base PostgreSQL gestionada en la región más cercana.
2. Conserva host, puerto, base, usuario y contraseña en el gestor de secretos.
3. Restringe acceso de red al backend cuando el proveedor lo permita.
4. No ejecutes `downgrade` ni limpiezas sobre producción.

## 2. Variables del backend

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
POSTGRES_HOST
POSTGRES_PORT
JWT_SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=https://frontend.example
PORT=8000
REDIS_URL=redis://host:6379/0
WS_TICKET_EXPIRE_SECONDS=60
CHAT_MAX_MESSAGE_LENGTH=1000
CHAT_RATE_LIMIT_MESSAGES=10
CHAT_RATE_LIMIT_WINDOW_SECONDS=10
```

`CORS_ORIGINS` acepta varios orígenes separados por coma. Genera
`JWT_SECRET_KEY` con entropía suficiente y guárdala como secreto.

## 3. Comandos del backend

Instalación:

```text
python -m pip install -r requirements.txt
```

Migración:

```text
alembic upgrade head
```

Inicio en shell compatible con variables POSIX:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Con Docker, el `CMD` ya ejecuta migraciones antes de Uvicorn. En equipos con
múltiples réplicas conviene ejecutar Alembic como release command único.

## 4. Verificar backend

```text
GET https://api.example/health
GET https://api.example/docs
GET https://api.example/openapi.json
```

`/health` debe responder `{"status":"ok"}`. Luego verifica registro, login,
perfil y un flujo completo de viaje con cuentas de prueba autorizadas.

## 5. Frontend en Vercel o equivalente

1. Configura `frontend` como directorio raíz del proyecto.
2. Usa `npm install` como instalación y `npm run build` como build.
3. Configura:

```text
NEXT_PUBLIC_API_URL=https://api.example
```

4. Despliega y añade el dominio final a `CORS_ORIGINS` del backend.
5. Vuelve a desplegar/reiniciar el backend si el proveedor no recarga variables.

## 6. Verificación funcional

- Registro y validaciones.
- Login y recuperación de `/auth/me`.
- Creación y listado de viaje.
- Unión como segundo usuario.
- Consulta de viajes creados y unidos.
- Cancelación y desaparición del listado disponible.
- Logout y rechazo de token inválido.
- Layout móvil y escritorio.

## Seguridad previa a producción

- Rotar cualquier secreto usado en desarrollo.
- Restringir Swagger si la política del producto lo exige.
- Configurar backups, retención y restauración de PostgreSQL.
- Habilitar logs centralizados sin tokens, hashes ni contraseñas.
- Añadir rate limiting al login en el perímetro o aplicación.
- Evaluar cookies HttpOnly en lugar de `localStorage` para sesiones web.
- Usar Redis administrado con TLS y red privada; comprobar tickets, Pub/Sub y
  reconexión WebSocket en todas las réplicas.
- Configurar proveedores de geocodificación/rutas con SLA; no usar servidores públicos gratuitos bajo carga.
- Servir el frontend por HTTPS: los permisos de geolocalización lo requieren fuera de localhost.
- Ejecutar auditorías de dependencias y pruebas en CI.
- Configurar monitoreo de `/health`, TLS y alertas.

## Desarrollo móvil en LAN

Next.js carga `frontend/.env.local`; Docker Compose interpola por defecto el `.env` de la raíz. Los archivos `*.example` son plantillas y no se cargan automáticamente. Para otro dispositivo usa `NEXT_PUBLIC_API_URL=http://IP_DEL_EQUIPO:8000`, agrega `http://IP_DEL_EQUIPO:3000` a `CORS_ORIGINS` e inicia Next con `npx next dev -H 0.0.0.0 -p 3000`. Reinicia ambos procesos tras cambiar variables. No uses `localhost` como URL de API desde el teléfono.
# Geolocalización móvil en desarrollo

Los navegadores móviles normalmente exigen HTTPS para `navigator.geolocation` fuera de `localhost`. Use un proxy/túnel HTTPS de desarrollo o certificados locales confiables fuera del repositorio; configure las URLs HTTPS/WSS y el origen exacto en CORS. No versione certificados ni claves. Compruebe primero `/health`, luego inicie el frontend enlazado a `0.0.0.0` y acepte el permiso únicamente al pulsar **Compartir ubicación**.
