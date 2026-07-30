# Jahamina — Presentación de proyecto

## Problema

Personas que realizan trayectos similares necesitan una forma simple de publicar
y descubrir viajes compartidos sin perder claridad sobre quién crea, comparte o
cancela cada recorrido.

## Solución

Jahamina ofrece un MVP web con identidad autenticada, publicación de viajes,
descubrimiento de trayectos disponibles, participación de pasajeros y
cancelación lógica para conservar historial.

## Stack

- FastAPI, Pydantic 2 y Python.
- SQLAlchemy 2, PostgreSQL y Alembic.
- OAuth2, JWT y bcrypt.
- Pytest y HTTPX.
- Docker y Docker Compose.
- Next.js, React, TypeScript y Tailwind CSS.

## Arquitectura

Backend por capas con rutas, servicios, schemas y modelos. PostgreSQL evoluciona
mediante Alembic. El frontend App Router consume un cliente HTTP centralizado y
mantiene una sesión compartida sin dependencias de estado global.

## Funcionalidades

- Registro, login, perfil y cierre de sesión.
- Viajes futuros con validaciones de recorrido.
- Listados de disponibles, creados y compartidos.
- Unión y prevención de duplicados.
- Autorización de cancelación y conservación del historial.
- Swagger, healthcheck, Docker y documentación.

## Desafíos técnicos

- Reemplazar migraciones históricas incompatibles sin ocultarlas.
- Unificar firma y validación JWT.
- Compatibilizar bcrypt moderno sin exponer hashes.
- Diseñar pruebas PostgreSQL revertibles.
- Separar configuración host y contenedor.
- Mantener contratos HTTP coherentes entre backend y frontend.

## Decisiones importantes

- Alembic como única fuente oficial del esquema.
- Cancelación lógica en lugar de borrado.
- Restricción única de usuario y viaje en base de datos.
- Códigos 201, 401, 403, 404, 409 y 422 con significado explícito.
- Cliente frontend sin librerías de estado innecesarias.
- Configuración y secretos exclusivamente por entorno.

## Seguridad y validaciones

- Password bcrypt de 8 caracteres y hasta 72 bytes.
- JWT con expiración UTC y clave externa.
- Emails normalizados.
- Rutas privadas con OAuth2 Bearer.
- CORS con allowlist.
- Respuestas sin contraseña ni hash.
- Rollback seguro ante fallos de escritura.

## Pruebas

La suite cubre autenticación, JWT válido/inválido/expirado, reglas de viajes,
pasajeros, contratos Pydantic, códigos HTTP, OpenAPI, CORS y healthcheck. Las
pruebas usan transacciones revertidas y no dejan datos.

## Capturas sugeridas

1. Landing responsive.
2. Swagger con rutas y OAuth2.
3. Registro y login.
4. Tarjetas de viajes disponibles.
5. Formulario de creación.
6. Historial creado/compartido y confirmación de cancelación.
7. Suite Pytest aprobada.
8. Contenedores saludables en Docker Compose.

## Texto breve para CV

Desarrollé Jahamina, un MVP full-stack de viajes compartidos con FastAPI,
PostgreSQL, SQLAlchemy 2, Alembic, JWT, Pytest, Docker y Next.js/TypeScript.
Implementé reglas de autorización, migraciones reproducibles, pruebas
transaccionales y una interfaz responsive integrada mediante API REST.

## Texto para LinkedIn

Jahamina es mi proyecto full-stack de viajes compartidos. Construí una API
FastAPI con PostgreSQL, migraciones Alembic, autenticación JWT y pruebas
automatizadas; además desarrollé un frontend responsive en Next.js y TypeScript.
El foco estuvo en contratos REST claros, seguridad, reproducibilidad con Docker
y documentación preparada para despliegue.

## Descripción para GitHub

MVP full-stack de viajes compartidos con FastAPI, PostgreSQL, Alembic, JWT,
Pytest, Docker y Next.js.

## Roadmap posterior al MVP

- Cupos disponibles.
- Precios.
- Vehículos.
- Reservas.
- Puntos de encuentro.
- Mapas.
- Notificaciones.
- Calificaciones.
- Chat.
- Aplicación móvil Flutter.

Estas mejoras son propuestas futuras y no están implementadas en la versión 1.0.
