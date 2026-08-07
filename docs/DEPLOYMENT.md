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
GEOCODING_PROVIDER=nominatim
GEOCODING_PROVIDER_URL=https://nominatim.openstreetmap.org
```

`CORS_ORIGINS` acepta varios orígenes separados por coma. Genera
`JWT_SECRET_KEY` con entropía suficiente y guárdala como secreto.

Para evaluar MapTiler sin cambiar el frontend configure `GEOCODING_PROVIDER=maptiler`,
`MAPTILER_GEOCODING_URL=https://api.maptiler.com/geocoding` y
`MAPTILER_API_KEY` como secreto del backend. Nominatim continúa como fallback.

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
# Web Push y HTTPS

Configure `WEB_PUSH_ENABLED`, las claves VAPID y un `WEB_PUSH_SUBJECT` válido
solo en el entorno del backend. Nunca use una variable `NEXT_PUBLIC_*` para la
clave privada. Producción necesita HTTPS para frontend y API, WSS para sockets
y orígenes explícitos en CORS.

## WEB PUSH PRODUCTION

1. Genere una sola vez el par VAPID, desde la raíz del repositorio, con `python scripts/generate_vapid.py`. El script imprime las claves localmente y no crea archivos. Como alternativa, use `npx web-push generate-vapid-keys --json` en un entorno confiable.
2. Copie inmediatamente la clave pública y la privada a un gestor de secretos. No las coloque en `.env.example`, tickets, capturas ni logs.
3. En Render configure `WEB_PUSH_VAPID_PUBLIC_KEY`, `WEB_PUSH_VAPID_PRIVATE_KEY`, `WEB_PUSH_SUBJECT=mailto:contacto@su-dominio`, `WEB_PUSH_ENABLED=true` y temporalmente `WEB_PUSH_TEST_ENABLED=true`.
4. En Vercel configure `NEXT_PUBLIC_VAPID_PUBLIC_KEY` con exactamente la misma clave pública. Esta variable es visible en el navegador; nunca use aquí la clave privada.
5. Vuelva a desplegar el backend de Render y compruebe que `GET /notificaciones/configuracion-push` devuelve `enabled=true` sin revelar la clave privada.
6. Vuelva a desplegar el frontend de Vercel para incorporar la clave pública en el build.
7. En Android Chrome abra Jahamina por HTTPS, inicie sesión y pulse **Activar notificaciones**. El permiso nunca se solicita automáticamente.
8. Verifique que `POST /notificaciones/suscripciones` responde 201 y que el dispositivo aparece en el perfil sin exponer endpoint ni claves.
9. Autenticado como ese usuario, ejecute `POST /notificaciones/prueba`; la respuesta indica `subscriptions_notified`.
10. Deje Jahamina en segundo plano y repita la prueba.
11. Cierre la pestaña o la PWA y genere un evento relevante o repita la prueba; la instalación PWA no es obligatoria en Chrome Android.
12. Pulse la notificación y confirme que enfoca o abre Jahamina únicamente en `/reservas`, `/viajes` o `/mis-viajes` y sus rutas hijas.
13. Al terminar, configure `WEB_PUSH_TEST_ENABLED=false` en Render y vuelva a desplegar. Mantenga `WEB_PUSH_ENABLED=true`.

El logout intenta revocar solo la suscripción del navegador actual y también llama a `PushSubscription.unsubscribe()`. Si el navegador cambia de usuario y conserva una suscripción ajena, el frontend la descarta y crea otra; el backend nunca permite modificar la suscripción de otro usuario. Fallos 404/410 del servicio Push desactivan el dispositivo. Los fallos Push no revierten la notificación interna ni la acción que la originó.

El Service Worker no cachea respuestas autenticadas, tokens, chat, perfil ni reservas. Solo atiende `push` y `notificationclick`, y limita la navegación a rutas internas conocidas.

## Imágenes en Cloudinary

Configure únicamente en Render `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` y `CLOUDINARY_API_SECRET`. El secreto nunca pertenece a Vercel ni a una variable `NEXT_PUBLIC_*`. `MEDIA_MAX_UPLOAD_BYTES` permite ajustar el límite, cuyo valor recomendado es `5242880` (5 MB).

Los uploads se firman en FastAPI y requieren JWT. No habilite presets unsigned. Jahamina genera identificadores aleatorios controlados bajo `jahamina/users/{id}` y `jahamina/vehicles/{id}`; PostgreSQL conserva la URL HTTPS y el `public_id` privado para reemplazar o eliminar el recurso correcto. El `public_id` nunca se devuelve al frontend ni se deriva del nombre enviado por el usuario. Antes de desplegar el backend ejecute `alembic upgrade head` para añadir las columnas opcionales.

Para pruebas móviles use un túnel HTTPS confiable o certificados locales
administrados fuera del repositorio. Verifique `/manifest.webmanifest`,
`/sw.js`, active las notificaciones desde la campana y use el endpoint de
prueba únicamente con `WEB_PUSH_TEST_ENABLED=true` en desarrollo.
