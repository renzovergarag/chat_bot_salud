# Esqueleto de la arquitectura del módulo de gestión — Diseño

Fecha: 2026-07-20
Rama: `feature/esqueleto-arquitectura-gestion`
Relacionado: `docs/arquitectura-modulo-gestion.md`

## Objetivo

Construir el **andamiaje estructural puro** de la nueva arquitectura: crear la
app `gestion` dentro del proyecto Django `cesfam_chatbot` y dejar montado el
routing por subdominio que la separa del chatbot público. Esta etapa **no
incluye modelos, auth ni lógica de negocio**: solo el esqueleto que prueba que
el cableado por host funciona.

## Alcance

**Dentro de alcance:**

- App `gestion` con archivos base y una vista placeholder.
- Routing por host dentro de un único proyecto Django (Opción A: middleware
  que fija `request.urlconf`), sin dependencias externas.
- Cambios de `settings.py` y `.env.example` para soportar el subdominio.
- Tests que verifican el aislamiento host-por-host.

**Fuera de alcance (etapas siguientes):**

- Modelos `Gestion` (OneToOne con `Solicitud`), M2M usuario↔centros,
  `ConfiguracionChatbot` y sus migraciones.
- Auth / login gating del subdominio de gestión.
- UI real de la cola (Etapa 1), deep-links de WhatsApp (Etapa 2), validación
  de ventana horaria del chatbot.
- Configuración de nginx / DNS del subdominio (se documenta aquí, se aplica en
  el deploy).

## Decisiones tomadas

- **Un solo proyecto**, app `gestion` nueva (ver `docs/arquitectura-modulo-gestion.md`).
- **Routing por subdominio** vía middleware que setea `request.urlconf` según
  el host (Opción A). Se descartó `django-hosts` (dependencia innecesaria para
  2 hosts) y el enfoque de prefijo de ruta (no da separación real).
- **Esta etapa es solo código Django.** La config de nginx/DNS se documenta,
  se aplica en el deploy.

## Estructura de la app

Creada con `manage.py startapp gestion`:

```
gestion/
├── __init__.py
├── apps.py            # GestionConfig
├── models.py          # vacío (sin modelos en esta etapa)
├── views.py           # vista placeholder: "Módulo de gestión — en construcción"
├── urls.py            # urlconf de la app, app_name = "gestion", 1 ruta → placeholder
├── admin.py           # vacío por ahora
├── tests.py           # tests del routing por host
└── migrations/
    └── __init__.py
```

La vista placeholder devuelve una respuesta mínima (un `HttpResponse` simple)
solo para confirmar que el subdominio resuelve. Sin auth-gating todavía.

## Mecanismo de routing por host

Tres piezas nuevas a nivel de proyecto:

1. **Urlconf del subdominio** — `cesfam_chatbot/urls_gestion.py`: urlconf raíz
   cuando el host es el de gestión. Incluye `gestion.urls` y **no** incluye las
   rutas del chatbot. El `admin/` de Django permanece en el urlconf principal
   por ahora (se reevalúa en una etapa posterior).

2. **Middleware de selección de urlconf** — `cesfam_chatbot/middleware.py`:
   `HostBasedUrlconfMiddleware`. En cada request compara `request.get_host()`
   con el host de gestión; si coincide, hace
   `request.urlconf = "cesfam_chatbot.urls_gestion"`. Si no, no toca nada y se
   usa el `ROOT_URLCONF` default (chatbot). Se ubica en `MIDDLEWARE` justo
   después de `SecurityMiddleware`, para fijar el urlconf antes de que corra el
   resolver de URLs.

3. **Host configurable por entorno** — variable `GESTION_HOST`: default
   `gestion.localhost` para desarrollo local (se resuelve sin DNS, o con una
   línea en `/etc/hosts`); en producción se setea a `gestion.cmvalparaiso.cl`
   vía `.env`.

Resultado: una request a `gestion.<host>` solo ve las URLs de `gestion`; una a
`morbilidad.<host>` solo ve las del chatbot. Separación real, sin dependencias
externas.

## Cambios en configuración

En `cesfam_chatbot/settings.py`:

- `INSTALLED_APPS`: agregar `"gestion"`.
- `MIDDLEWARE`: agregar `HostBasedUrlconfMiddleware` después de
  `SecurityMiddleware`.
- Leer `GESTION_HOST` del entorno (default `gestion.localhost`).
- `ALLOWED_HOSTS`: sumar el valor de `GESTION_HOST`.
- `CSRF_TRUSTED_ORIGINS`: contemplar el subdominio de gestión (patrón listo
  para cuando haya formularios).

En `.env.example`: documentar `GESTION_HOST` (default `gestion.localhost`,
producción `gestion.cmvalparaiso.cl`).

## Verificación

- `python manage.py check` sin issues.
- `python manage.py makemigrations --check --dry-run` sin migraciones nuevas
  (no hay modelos).
- Tests en `gestion/tests.py` con el `Client` usando `HTTP_HOST`:
  - `HTTP_HOST = gestion.localhost` → la vista placeholder responde 200.
  - `HTTP_HOST` default (chatbot) → el home del chatbot responde 200.
  - Una URL del chatbot **no** resuelve en el host de gestión (404).
  - Una URL de gestión **no** resuelve en el host default (404).
- La suite existente (9 tests del chatbot) sigue verde.

## Notas de despliegue (fuera de alcance, para etapa de deploy)

- nginx: nuevo `server_name gestion.cmvalparaiso.cl` apuntando al mismo WSGI.
- DNS: registro para el subdominio.
- `.env` de producción: `GESTION_HOST=gestion.cmvalparaiso.cl` y sumar el
  origin a `CSRF_TRUSTED_ORIGINS`.
