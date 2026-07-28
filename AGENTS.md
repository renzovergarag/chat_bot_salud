# AGENTS.md

SaludBot: proyecto Django que registra solicitudes de morbilidad vía un chatbot
web (valida RUT chileno, calcula prioridad interna para el equipo de salud) y,
en construcción, un módulo interno de gestión para validar esas solicitudes.

## Comandos

```bash
# Levantar la base local (MySQL 8.4, mismo motor que produccion)
docker compose up -d

# Tests. Django test runner, NO pytest.
.venv/bin/python manage.py test

# Servidor local
.venv/bin/python manage.py runserver

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
  el subdominio `seleccion.cmvalparaiso.cl`.

**Routing por subdominio:** `HostBasedUrlconfMiddleware`
(`cesfam_chatbot/middleware.py`) fija `request.urlconf = "cesfam_chatbot.urls_gestion"`
cuando el host coincide con `GESTION_HOST`; si no, usa el `ROOT_URLCONF` (chatbot).
No hay dependencias externas para esto. `GESTION_HOST` se configura por `.env`
(`gestion.localhost` en local). Al agregar rutas de gestión, tocar
`cesfam_chatbot/urls_gestion.py` + `gestion/urls.py`, no el urlconf principal.

La decisión "un proyecto vs dos con BD compartida" está documentada y cerrada en
`docs/arquitectura-modulo-gestion.md`.

## Base de datos

**MySQL 8.4 en producción y también en local**, vía el `docker-compose.yml` de
la raíz (contenedor `saludbot-mysql`, en `127.0.0.1:3306`). Toda la config se lee
de `.env` (ver `.env.example`); con `DB_ENGINE=mysql` no hace falta anteponer
nada a los comandos. `TextField` mapea a `LONGTEXT` en MySQL.

Existe un fallback a SQLite con `DB_ENGINE=sqlite`, pero **no usarlo para dar
por buena una tarea**: esconde diferencias reales con producción. Ejemplo vivido:
el contador `AUTO_INCREMENT` de InnoDB no hace rollback con la transacción del
`TestCase`, y el rowid de SQLite sí, así que un test que afirmaba `id == 1`
pasaba en SQLite y fallaba en MySQL.

Para que el runner pueda crear su base de tests, el usuario de la app necesita
privilegios sobre `test\_%`. Si aparece `Access denied ... to database
'test_chat_bot_salud'`, aplicar con root:

```sql
GRANT ALL PRIVILEGES ON `test\_%`.* TO 'saludbot'@'%'; FLUSH PRIVILEGES;
```

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
