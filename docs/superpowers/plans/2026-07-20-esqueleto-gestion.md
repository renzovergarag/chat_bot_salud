# Esqueleto app `gestion` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear el andamiaje estructural de la app `gestion` dentro del proyecto Django `cesfam_chatbot`, con routing por subdominio, sin modelos ni lógica de negocio.

**Architecture:** Un único proyecto Django. Un middleware inspecciona el host de cada request y, para el subdominio de gestión, fija `request.urlconf` a un urlconf propio (`cesfam_chatbot/urls_gestion.py`) que solo expone la app `gestion`. El host default sigue usando `ROOT_URLCONF` (chatbot). Sin dependencias externas.

**Tech Stack:** Django 5.2.8, Python 3.11, test runner nativo de Django (`manage.py test`).

## Global Constraints

- Sin dependencias nuevas (no agregar nada a `requirements.txt`).
- Sin modelos, sin migraciones nuevas, sin auth, sin lógica de negocio.
- Host de gestión configurable por env `GESTION_HOST` (default `gestion.localhost`; producción `gestion.cmvalparaiso.cl`).
- Comando de tests: `.venv/bin/python manage.py test`.
- La suite existente (9 tests del chatbot en `solicitudes/tests.py`) debe seguir en verde.
- Trailers de commit obligatorios al final de cada mensaje:
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01E5xMqoH6DhS6XmqCavfAUX
  ```

---

## File Structure

- Create: `gestion/__init__.py`, `gestion/apps.py`, `gestion/models.py`, `gestion/views.py`, `gestion/urls.py`, `gestion/admin.py`, `gestion/tests.py`, `gestion/migrations/__init__.py` (vía `startapp`)
- Create: `cesfam_chatbot/urls_gestion.py` — urlconf raíz del subdominio de gestión
- Create: `cesfam_chatbot/middleware.py` — `HostBasedUrlconfMiddleware`
- Modify: `cesfam_chatbot/settings.py` — `INSTALLED_APPS`, `MIDDLEWARE`, `GESTION_HOST`, `ALLOWED_HOSTS`
- Modify: `.env.example` — documentar `GESTION_HOST`

---

## Task 1: Scaffolding de la app `gestion` con vista placeholder

**Files:**
- Create: `gestion/` (app completa vía `manage.py startapp gestion`)
- Modify: `gestion/apps.py`, `gestion/views.py`
- Create: `gestion/urls.py`
- Modify: `cesfam_chatbot/settings.py:44` (agregar `"gestion"` a `INSTALLED_APPS`)
- Test: `gestion/tests.py`

**Interfaces:**
- Produces: `gestion.views.panel(request) -> HttpResponse` (status 200, texto `"Módulo de gestión — en construcción"`); urlconf `gestion.urls` con `app_name = "gestion"` y ruta `""` name `panel`.

- [ ] **Step 1: Crear la app**

Run: `.venv/bin/python manage.py startapp gestion`
Expected: se crea el directorio `gestion/` con archivos base.

- [ ] **Step 2: Registrar la app en INSTALLED_APPS**

En `cesfam_chatbot/settings.py`, dentro de `INSTALLED_APPS`, agregar `"gestion",` después de `"solicitudes",`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "solicitudes",
    "gestion",
]
```

- [ ] **Step 3: Escribir el test que falla (vista placeholder)**

Reemplazar el contenido de `gestion/tests.py` por:

```python
from django.test import TestCase
from django.test.client import RequestFactory

from gestion.views import panel


class PanelPlaceholderTests(TestCase):
    def test_panel_responde_200(self):
        request = RequestFactory().get("/")
        response = panel(request)
        self.assertEqual(response.status_code, 200)

    def test_panel_muestra_texto_en_construccion(self):
        request = RequestFactory().get("/")
        response = panel(request)
        self.assertIn("construcción", response.content.decode("utf-8"))
```

- [ ] **Step 4: Correr el test para verificar que falla**

Run: `.venv/bin/python manage.py test gestion -v 2`
Expected: FAIL con `ImportError` / `cannot import name 'panel'` (la vista aún no existe).

- [ ] **Step 5: Implementar la vista placeholder**

Reemplazar el contenido de `gestion/views.py` por:

```python
from django.http import HttpResponse


def panel(request):
    return HttpResponse("Módulo de gestión — en construcción")
```

- [ ] **Step 6: Crear el urlconf de la app**

Crear `gestion/urls.py`:

```python
from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.panel, name="panel"),
]
```

- [ ] **Step 7: Correr los tests y verificar que pasan**

Run: `.venv/bin/python manage.py test gestion -v 2`
Expected: PASS (2 tests).

- [ ] **Step 8: Verificar el proyecto y ausencia de migraciones nuevas**

Run: `.venv/bin/python manage.py check`
Expected: `System check identified no issues`.

Run: `.venv/bin/python manage.py makemigrations --check --dry-run`
Expected: `No changes detected` (no hay modelos).

- [ ] **Step 9: Commit**

```bash
git add gestion/ cesfam_chatbot/settings.py
git commit -m "$(cat <<'EOF'
Scaffolding de la app gestion con vista placeholder

Crea la app gestion (sin modelos), la registra en INSTALLED_APPS y expone
una vista placeholder con su urlconf de app.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01E5xMqoH6DhS6XmqCavfAUX
EOF
)"
```

---

## Task 2: Routing por subdominio (middleware + urlconf + settings)

**Files:**
- Create: `cesfam_chatbot/urls_gestion.py`
- Create: `cesfam_chatbot/middleware.py`
- Modify: `cesfam_chatbot/settings.py` (`GESTION_HOST`, `ALLOWED_HOSTS`, `MIDDLEWARE`)
- Modify: `.env.example`
- Test: `gestion/tests.py` (agregar clase de routing)

**Interfaces:**
- Consumes: `gestion.urls` (Task 1), `gestion.views.panel` (Task 1).
- Produces: `cesfam_chatbot.middleware.HostBasedUrlconfMiddleware`; setting `GESTION_HOST`; urlconf `cesfam_chatbot.urls_gestion`.

- [ ] **Step 1: Escribir los tests de routing que fallan**

Agregar al final de `gestion/tests.py`:

```python
from django.test import override_settings


@override_settings(ALLOWED_HOSTS=["gestion.localhost", "testserver"], GESTION_HOST="gestion.localhost")
class HostRoutingTests(TestCase):
    def test_subdominio_gestion_resuelve_placeholder(self):
        response = self.client.get("/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 200)
        self.assertIn("construcción", response.content.decode("utf-8"))

    def test_host_default_resuelve_chatbot(self):
        response = self.client.get("/", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("construcción", response.content.decode("utf-8"))

    def test_url_del_chatbot_no_existe_en_subdominio_gestion(self):
        response = self.client.get("/terminos/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 404)
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `.venv/bin/python manage.py test gestion.tests.HostRoutingTests -v 2`
Expected: FAIL — sin el middleware, `/` en `gestion.localhost` resuelve el home del chatbot (no contiene "construcción") y `/terminos/` responde 200 en vez de 404.

- [ ] **Step 3: Crear el urlconf del subdominio**

Crear `cesfam_chatbot/urls_gestion.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("", include("gestion.urls")),
]
```

- [ ] **Step 4: Crear el middleware**

Crear `cesfam_chatbot/middleware.py`:

```python
from django.conf import settings


class HostBasedUrlconfMiddleware:
    """Selecciona el urlconf segun el host: el subdominio de gestion usa
    cesfam_chatbot.urls_gestion; cualquier otro host usa el ROOT_URLCONF."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]
        if host == settings.GESTION_HOST:
            request.urlconf = "cesfam_chatbot.urls_gestion"
        return self.get_response(request)
```

- [ ] **Step 5: Agregar `GESTION_HOST` y sumarlo a `ALLOWED_HOSTS`**

En `cesfam_chatbot/settings.py`, inmediatamente después del bloque que arma `ALLOWED_HOSTS` (después de la línea 22, el cierre de la lista), agregar:

```python
# Host del modulo interno de gestion. En produccion: gestion.cmvalparaiso.cl
GESTION_HOST = os.getenv("GESTION_HOST", "gestion.localhost")
if GESTION_HOST and GESTION_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(GESTION_HOST)
```

- [ ] **Step 6: Registrar el middleware**

En `cesfam_chatbot/settings.py`, dentro de `MIDDLEWARE`, agregar la línea del middleware justo después de `SecurityMiddleware`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "cesfam_chatbot.middleware.HostBasedUrlconfMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

- [ ] **Step 7: Correr los tests de routing y verificar que pasan**

Run: `.venv/bin/python manage.py test gestion.tests.HostRoutingTests -v 2`
Expected: PASS (3 tests).

- [ ] **Step 8: Documentar `GESTION_HOST` en `.env.example`**

En `.env.example`, después de la línea `ALLOWED_HOSTS=...` (línea 3), agregar:

```
# Host del modulo interno de gestion (routing por subdominio).
# Local: gestion.localhost  |  Produccion: gestion.cmvalparaiso.cl
GESTION_HOST=gestion.localhost
# En produccion, sumar el origin del subdominio a CSRF_TRUSTED_ORIGINS:
# CSRF_TRUSTED_ORIGINS=https://morbilidad.cmvalparaiso.cl,https://gestion.cmvalparaiso.cl
```

- [ ] **Step 9: Correr la suite completa (regresión)**

Run: `.venv/bin/python manage.py test -v 2`
Expected: PASS — los 9 tests del chatbot + los 5 de `gestion` (2 de Task 1 + 3 de routing).

- [ ] **Step 10: Verificación final del proyecto**

Run: `.venv/bin/python manage.py check`
Expected: `System check identified no issues`.

- [ ] **Step 11: Commit**

```bash
git add cesfam_chatbot/urls_gestion.py cesfam_chatbot/middleware.py cesfam_chatbot/settings.py .env.example gestion/tests.py
git commit -m "$(cat <<'EOF'
Routing por subdominio para el modulo de gestion

Agrega HostBasedUrlconfMiddleware que fija request.urlconf al urlconf de
gestion cuando el host coincide con GESTION_HOST. Sin dependencias externas.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01E5xMqoH6DhS6XmqCavfAUX
EOF
)"
```

---

## Self-Review

**1. Spec coverage:**
- App `gestion` con archivos base + placeholder → Task 1. ✓
- Routing por host vía middleware que fija `request.urlconf` (Opción A) → Task 2. ✓
- `urls_gestion.py` sin rutas del chatbot → Task 2 Step 3. ✓
- `GESTION_HOST` configurable (default `gestion.localhost`) → Task 2 Step 5. ✓
- `INSTALLED_APPS`, `MIDDLEWARE`, `ALLOWED_HOSTS` → Task 1 Step 2, Task 2 Steps 5-6. ✓
- `.env.example` documenta `GESTION_HOST` + patrón CSRF → Task 2 Step 8. ✓
- Verificación: `check`, `makemigrations --check`, tests de aislamiento, suite existente verde → Task 1 Step 8, Task 2 Steps 7/9/10. ✓
- `admin.py` vacío / sin modelos → generado por `startapp`, no se toca. ✓
- Fuera de alcance (modelos, auth, UI, nginx/DNS) → no aparecen en ninguna tarea. ✓

**2. Placeholder scan:** Sin TBD/TODO ni pasos vagos; todo el código está explícito.

**3. Type consistency:** `gestion.views.panel` y `app_name = "gestion"` usados consistentemente entre Task 1 y Task 2. `settings.GESTION_HOST` definido en Task 2 Step 5 y consumido por el middleware en Step 4. `HostBasedUrlconfMiddleware` nombrado igual en middleware y en `MIDDLEWARE`.

Nota sobre `CSRF_TRUSTED_ORIGINS`: en esta etapa no hay formularios en el subdominio, por lo que no requiere cambio de código; se deja documentado el patrón en `.env.example` para el deploy (coherente con el spec, "patrón listo").
