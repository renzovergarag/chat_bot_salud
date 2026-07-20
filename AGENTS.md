# AGENTS.md

SaludBot: proyecto Django que registra solicitudes de morbilidad vía un chatbot
web (valida RUT chileno, calcula prioridad interna para el equipo de salud) y,
en construcción, un módulo interno de gestión para validar esas solicitudes.

## Comandos

```bash
# Tests (usar SQLite para no depender de MySQL). Django test runner, NO pytest.
DB_ENGINE=sqlite .venv/bin/python manage.py test

# Servidor local con SQLite
DB_ENGINE=sqlite .venv/bin/python manage.py runserver

# Migraciones
.venv/bin/python manage.py makemigrations
.venv/bin/python manage.py migrate
```

Correr los tests antes de dar una tarea por terminada. Los `.ps1` de la raíz son
para el entorno Windows del autor; en Linux usar `.venv/bin/python`.

## Arquitectura

Un solo proyecto Django (`cesfam_chatbot`) con dos apps:

- **`solicitudes`** — el chatbot público. Dueña del modelo `Solicitud` (única que
  lo crea). Se accede por `morbilidad.cmvalparaiso.cl`.
- **`gestion`** — módulo interno de validación (en construcción). Se accede por
  el subdominio `gestion.cmvalparaiso.cl`.

**Routing por subdominio:** `HostBasedUrlconfMiddleware`
(`cesfam_chatbot/middleware.py`) fija `request.urlconf = "cesfam_chatbot.urls_gestion"`
cuando el host coincide con `GESTION_HOST`; si no, usa el `ROOT_URLCONF` (chatbot).
No hay dependencias externas para esto. `GESTION_HOST` se configura por `.env`
(`gestion.localhost` en local). Al agregar rutas de gestión, tocar
`cesfam_chatbot/urls_gestion.py` + `gestion/urls.py`, no el urlconf principal.

La decisión "un proyecto vs dos con BD compartida" está documentada y cerrada en
`docs/arquitectura-modulo-gestion.md`.

## Base de datos

MySQL 8.4 en producción; SQLite en local con `DB_ENGINE=sqlite`. Toda la config
se lee de `.env` (ver `.env.example`). `TextField` mapea a `LONGTEXT` en MySQL.

## Convenciones

- Código, comentarios, mensajes de commit y docs en **español**, sin tildes en
  identificadores. Sin emojis en commits.
- Seguir los patrones de la app que se está tocando; no hacer refactors no pedidos.
- Docs de arquitectura y deuda técnica viven en `docs/`; specs y planes de
  desarrollo en `docs/superpowers/`.

## Deuda técnica conocida (leer antes de tocar estas zonas)

- **Fotos de credencial de discapacidad** se guardan como base64 dentro de la
  fila (`Solicitud.credencial_cuidador_discapacidad_foto`), no como archivo. Tiene
  un bug de tamaño de request y no escala. Detalle y fix propuesto en
  `docs/deuda-almacenamiento-imagenes-credencial.md`. No ampliar este patrón.

## No commitear

`.env`, `.venv/`, `db.sqlite3`, `staticfiles/`.
