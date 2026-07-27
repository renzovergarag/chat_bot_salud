# Login con Google Workspace y perfiles de usuario — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que un funcionario entre al subdominio de gestión autenticándose con su cuenta de Google Workspace institucional, y que el sistema sepa su rol y su centro; quien no tenga perfil dado de alta no entra.

**Architecture:** `mozilla-django-oidc` maneja el flujo OIDC contra Google. La identidad (correo, nombre) vive en el `User` de `django.contrib.auth`; la autorización (rol, centro) vive en `PerfilUsuario`, un `OneToOne → User` en la app `gestion`. Un backend de autenticación propio aplica las dos reglas de acceso en los hooks `verify_claims` (dominio institucional) y `filter_users_by_claims` (perfil existente y activo). Las rutas de login se exponen **solo** en el urlconf del subdominio de gestión; el host público del chatbot no las tiene.

**Tech Stack:** Django 5.2.8, `mozilla-django-oidc==5.0.2`, Python 3.11 en local / 3.14 en producción, test runner nativo de Django (`manage.py test`).

## Global Constraints

- Spec de referencia: `docs/superpowers/specs/2026-07-27-login-google-perfiles-design.md`, que a su vez se apoya en `docs/arquitectura-modulo-gestion.md` (secciones "Autenticación: OAuth con Google Workspace" y "Perfil de usuario: rol y centro").
- Código, comentarios y mensajes de commit en **español, sin tildes en identificadores**. Sin emojis en commits.
- Comando de tests: `DB_ENGINE=sqlite .venv/bin/python manage.py test`. Django test runner, **no pytest**.
- La suite existente debe seguir en verde en cada tarea: **10 tests en `solicitudes` + 5 en `gestion` = 15 en total** antes de empezar.
- Una única dependencia nueva: `mozilla-django-oidc==5.0.2` (pinneada). Arrastra `pyjwt` y `requests`; `cryptography` ya está en `requirements.txt`.
- **Ningún secreto en el repo.** `client_id` y `client_secret` se leen de `.env`; en producción viajan dentro del secret `ENV_PROD` del workflow de deploy.
- Los roles del sistema son exactamente siete: `ADMIN`, `SUPERVISOR_DAS`, `SUPERVISOR_CENTRO`, `SOME`, `FULL`, `SELECTOR`, `COMUNICADOR`. Un rol por usuario.
- `PerfilUsuario` **no** duplica `correo` ni `nombre`: esos campos son de `User` y los puebla Google.
- No se crean cuentas automáticamente al primer login (`OIDC_CREATE_USER = False`).
- Trailers de commit obligatorios al final de cada mensaje:
  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01NTceB3VF7V3KyFngJuJc2T
  ```

### Fuera de alcance de este plan

Son planes aparte, no tareas de este: el modelo `Gestion` con las Etapas 1 y 2, las vistas worklist, el deep-link de WhatsApp, la ventana horaria del chatbot, y la UI de administración de perfiles para el rol `SOME` (en este plan el alta se hace por el admin de Django).

---

## File Structure

- Modify: `requirements.txt` — agregar `mozilla-django-oidc==5.0.2`
- Create: `gestion/models.py` (reemplazo del archivo vacío) — modelo `PerfilUsuario`
- Create: `gestion/migrations/0001_initial.py` — vía `makemigrations`
- Modify: `gestion/admin.py` — registrar `PerfilUsuarioAdmin`
- Create: `gestion/auth.py` — `OIDCAuthenticationBackendGestion`
- Modify: `gestion/views.py` — gating del panel
- Modify: `cesfam_chatbot/settings.py` — `INSTALLED_APPS`, `AUTHENTICATION_BACKENDS`, bloque de settings OIDC, `LOGIN_*`
- Modify: `cesfam_chatbot/urls_gestion.py` — rutas de `mozilla_django_oidc` + admin
- Modify: `cesfam_chatbot/urls.py` — sacar el admin del host público
- Modify: `.env.example` — documentar las variables de Google
- Modify: `gestion/tests.py` — tests de modelo, backend y routing

---

## Task 1: Modelo `PerfilUsuario` con rol, centro y alcance

**Files:**
- Modify: `gestion/models.py`
- Create: `gestion/migrations/0001_initial.py` (generada)
- Modify: `gestion/admin.py`
- Test: `gestion/tests.py`

**Interfaces:**
- Consumes: `solicitudes.models.Centro` (ya en `main`, PK `id_centro`).
- Produces:
  - `gestion.models.PerfilUsuario` con campos `usuario` (OneToOne a `settings.AUTH_USER_MODEL`, `related_name="perfil_gestion"`), `rol`, `centro`, `centro_satelite`, `anexo_telefono`, `activo`.
  - `PerfilUsuario.Rol` — `TextChoices` con los siete roles.
  - `PerfilUsuario.ve_todos_los_centros` → `bool` (property).
  - `PerfilUsuario.centros_permitidos()` → `QuerySet[Centro]`.

- [ ] **Step 1: Escribir los tests que fallan**

Reemplazar el contenido de `gestion/tests.py` por lo siguiente. Ojo: se conservan las dos clases que ya existen (`PanelPlaceholderTests` y `HostRoutingTests`) tal cual, y se agrega `PerfilUsuarioTests` en medio.

```python
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from gestion.models import PerfilUsuario
from gestion.views import panel
from solicitudes.models import Centro


class PanelPlaceholderTests(TestCase):
    def test_panel_responde_200(self):
        request = RequestFactory().get("/")
        response = panel(request)
        self.assertEqual(response.status_code, 200)

    def test_panel_muestra_texto_en_construccion(self):
        request = RequestFactory().get("/")
        response = panel(request)
        self.assertIn("construcción", response.content.decode("utf-8"))


class PerfilUsuarioTests(TestCase):
    def setUp(self):
        self.centro = Centro.objects.get(pk=620)
        self.satelite = Centro.objects.get(pk=626)

    def _perfil(self, rol, correo, satelite=None):
        usuario = User.objects.create_user(correo, email=correo)
        return PerfilUsuario.objects.create(
            usuario=usuario,
            rol=rol,
            centro=self.centro,
            centro_satelite=satelite,
        )

    def test_perfil_arranca_activo(self):
        perfil = self._perfil(PerfilUsuario.Rol.SELECTOR, "selector@example.com")
        self.assertTrue(perfil.activo)
        self.assertEqual(perfil.usuario.perfil_gestion, perfil)

    def test_rol_de_centro_solo_ve_su_centro(self):
        perfil = self._perfil(PerfilUsuario.Rol.SELECTOR, "selector@example.com")
        self.assertFalse(perfil.ve_todos_los_centros)
        self.assertEqual([c.pk for c in perfil.centros_permitidos()], [620])

    def test_rol_de_centro_con_satelite_ve_ambos(self):
        perfil = self._perfil(
            PerfilUsuario.Rol.COMUNICADOR, "comunicador@example.com", satelite=self.satelite
        )
        self.assertEqual(sorted(c.pk for c in perfil.centros_permitidos()), [620, 626])

    def test_admin_y_supervisor_das_ven_todos_los_centros(self):
        admin = self._perfil(PerfilUsuario.Rol.ADMIN, "admin@example.com")
        das = self._perfil(PerfilUsuario.Rol.SUPERVISOR_DAS, "das@example.com")

        total = Centro.objects.count()
        for perfil in (admin, das):
            self.assertTrue(perfil.ve_todos_los_centros)
            self.assertEqual(perfil.centros_permitidos().count(), total)

    def test_supervisor_centro_no_ve_todos(self):
        perfil = self._perfil(PerfilUsuario.Rol.SUPERVISOR_CENTRO, "supervisor@example.com")
        self.assertFalse(perfil.ve_todos_los_centros)

    def test_un_usuario_no_puede_tener_dos_perfiles(self):
        perfil = self._perfil(PerfilUsuario.Rol.SELECTOR, "selector@example.com")
        # transaction.atomic es necesario: sin el, la IntegrityError deja la
        # transaccion del TestCase rota y falla el teardown.
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilUsuario.objects.create(
                usuario=perfil.usuario,
                rol=PerfilUsuario.Rol.COMUNICADOR,
                centro=self.centro,
            )

    def test_los_siete_roles_estan_definidos(self):
        self.assertEqual(
            [rol.value for rol in PerfilUsuario.Rol],
            [
                "ADMIN",
                "SUPERVISOR_DAS",
                "SUPERVISOR_CENTRO",
                "SOME",
                "FULL",
                "SELECTOR",
                "COMUNICADOR",
            ],
        )


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

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test gestion -v 2`
Expected: FAIL con `ImportError: cannot import name 'PerfilUsuario' from 'gestion.models'`.

- [ ] **Step 3: Escribir el modelo**

Reemplazar el contenido de `gestion/models.py` por:

```python
from django.conf import settings
from django.db import models

from solicitudes.models import Centro


class PerfilUsuario(models.Model):
    """Complementa al User de Django con la informacion que Google no entrega:
    el rol dentro del sistema y el centro al que pertenece el funcionario.

    Ademas funciona como lista de autorizacion: sin perfil activo no se entra
    al modulo de gestion, aunque el login con Google sea correcto.
    """

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador/a"
        SUPERVISOR_DAS = "SUPERVISOR_DAS", "Supervisor/a DAS"
        SUPERVISOR_CENTRO = "SUPERVISOR_CENTRO", "Supervisor/a de centro"
        SOME = "SOME", "SOME"
        FULL = "FULL", "Full"
        SELECTOR = "SELECTOR", "Selector"
        COMUNICADOR = "COMUNICADOR", "Comunicador"

    # Roles cuyo alcance es toda la corporacion y no un centro puntual.
    ROLES_TODOS_LOS_CENTROS = frozenset({Rol.ADMIN, Rol.SUPERVISOR_DAS})

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_gestion",
    )
    rol = models.CharField(max_length=20, choices=Rol.choices)
    centro = models.ForeignKey(
        Centro,
        on_delete=models.RESTRICT,
        related_name="perfiles",
        help_text="Centro base. Para ADMIN y SUPERVISOR_DAS es informativo: ven todos.",
    )
    centro_satelite = models.ForeignKey(
        Centro,
        on_delete=models.SET_NULL,
        related_name="perfiles_satelite",
        blank=True,
        null=True,
        help_text="CECOSF u otro centro asociado que este funcionario tambien gestiona.",
    )
    anexo_telefono = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(
        default=True,
        help_text="Desmarcar para revocar el acceso sin borrar el historial.",
    )

    class Meta:
        db_table = "gestion_perfil_usuario"
        ordering = ["usuario__email"]
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self):
        return f"{self.usuario.email} ({self.get_rol_display()})"

    @property
    def ve_todos_los_centros(self):
        return self.rol in self.ROLES_TODOS_LOS_CENTROS

    def centros_permitidos(self):
        """Centros cuyas solicitudes puede ver este perfil."""
        if self.ve_todos_los_centros:
            return Centro.objects.all()

        ids = [self.centro_id]
        if self.centro_satelite_id:
            ids.append(self.centro_satelite_id)
        return Centro.objects.filter(pk__in=ids)
```

- [ ] **Step 4: Generar la migración**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py makemigrations gestion`
Expected: `Migrations for 'gestion': gestion/migrations/0001_initial.py - Create model PerfilUsuario`.

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test gestion -v 2`
Expected: PASS (12 tests: 2 de placeholder + 7 de perfil + 3 de routing).

- [ ] **Step 6: Registrar el modelo en el admin**

Reemplazar el contenido de `gestion/admin.py` por:

```python
from django.contrib import admin

from .models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol", "centro", "centro_satelite", "activo")
    list_filter = ("rol", "activo", "centro")
    search_fields = ("usuario__email", "usuario__first_name", "usuario__last_name")
    autocomplete_fields = ("usuario",)
    list_select_related = ("usuario", "centro", "centro_satelite")
```

- [ ] **Step 7: Verificar el proyecto**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py check`
Expected: `System check identified no issues`. (`autocomplete_fields` exige que el admin del modelo referenciado defina `search_fields`; el `UserAdmin` de Django ya los trae, así que pasa. Si igualmente apareciera `admin.E040`, reemplazar `autocomplete_fields = ("usuario",)` por `raw_id_fields = ("usuario",)` y volver a correr.)

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

- [ ] **Step 8: Correr la suite completa (regresión)**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test`
Expected: PASS — 22 tests (10 de `solicitudes` + 12 de `gestion`).

- [ ] **Step 9: Commit**

```bash
git add gestion/models.py gestion/migrations/0001_initial.py gestion/admin.py gestion/tests.py
git commit -m "$(cat <<'EOF'
Agrega PerfilUsuario con rol y centro para el modulo de gestion

Complementa al User de Django con la informacion que Google no entrega: el
rol dentro del sistema y el centro (mas satelite opcional). Los roles con
alcance corporativo, ADMIN y SUPERVISOR_DAS, ven todos los centros; el resto
solo su centro y su satelite.

El perfil funciona ademas como lista de autorizacion del modulo.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NTceB3VF7V3KyFngJuJc2T
EOF
)"
```

---

## Task 2: Dependencia y configuración OIDC de Google

**Files:**
- Modify: `requirements.txt`
- Modify: `cesfam_chatbot/settings.py`
- Modify: `.env.example`

**Interfaces:**
- Produces: settings `OIDC_RP_CLIENT_ID`, `OIDC_RP_CLIENT_SECRET`, `OIDC_RP_SIGN_ALGO`, `OIDC_RP_SCOPES`, `OIDC_OP_AUTHORIZATION_ENDPOINT`, `OIDC_OP_TOKEN_ENDPOINT`, `OIDC_OP_USER_ENDPOINT`, `OIDC_OP_JWKS_ENDPOINT`, `OIDC_CREATE_USER`, `OIDC_AUTH_REQUEST_EXTRA_PARAMS`, `GOOGLE_WORKSPACE_DOMAIN`, `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGIN_REDIRECT_URL_FAILURE`, `LOGOUT_REDIRECT_URL`. Task 3 los consume.
- Nota: `AUTHENTICATION_BACKENDS` se define en Task 3, junto con el backend que referencia.

- [ ] **Step 1: Agregar la dependencia**

En `requirements.txt`, agregar al final:

```
mozilla-django-oidc==5.0.2
```

- [ ] **Step 2: Instalarla**

Run: `.venv/bin/pip install -r requirements.txt`
Expected: instala `mozilla-django-oidc-5.0.2` junto con `pyjwt` y `requests`.

- [ ] **Step 3: Registrar la app**

En `cesfam_chatbot/settings.py`, dentro de `INSTALLED_APPS` (líneas 42-51), agregar `"mozilla_django_oidc",` después de `"django.contrib.staticfiles",`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "mozilla_django_oidc",
    "solicitudes",
    "gestion",
]
```

- [ ] **Step 4: Agregar el bloque de configuración OIDC**

En `cesfam_chatbot/settings.py`, al final del archivo (después de `DEFAULT_AUTO_FIELD`, línea 122), agregar:

```python
# --- Autenticacion OIDC con Google Workspace -------------------------------
# El modulo de gestion se entra solo con cuenta institucional de Google. La
# identidad la da Google; el rol y el centro los da gestion.PerfilUsuario.

# Dominio institucional. Se valida contra el claim "hd" del ID token, no
# contra el parametro de la request: el parametro es solo una pista de UI.
GOOGLE_WORKSPACE_DOMAIN = os.getenv("GOOGLE_WORKSPACE_DOMAIN", "cmvalparaiso.cl")

OIDC_RP_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")

# Endpoints publicos de Google (estables, documentados en su discovery doc:
# https://accounts.google.com/.well-known/openid-configuration).
OIDC_OP_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
OIDC_OP_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
OIDC_OP_USER_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"
OIDC_OP_JWKS_ENDPOINT = "https://www.googleapis.com/oauth2/v3/certs"
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_SCOPES = "openid email profile"

# Nunca crear cuentas al vuelo: el alta la hace un ADMIN dando de alta el
# perfil. Un correo del dominio sin perfil queda rechazado.
OIDC_CREATE_USER = False

# "hd" acota el selector de cuentas de Google al dominio institucional;
# "prompt" evita quedar pegado en la ultima cuenta usada.
OIDC_AUTH_REQUEST_EXTRA_PARAMS = {
    "hd": GOOGLE_WORKSPACE_DOMAIN,
    "prompt": "select_account",
}

LOGIN_URL = "oidc_authentication_init"
LOGIN_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL_FAILURE = "/sin-acceso/"
LOGOUT_REDIRECT_URL = "/sin-acceso/"
```

- [ ] **Step 5: Verificar que el proyecto sigue levantando**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py check`
Expected: `System check identified no issues`.

- [ ] **Step 6: Correr la suite completa (regresión)**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test`
Expected: PASS — 22 tests (10 de `solicitudes` + 12 de `gestion`).

- [ ] **Step 7: Documentar las variables en `.env.example`**

En `.env.example`, después de la línea 8 (el comentario de `CSRF_TRUSTED_ORIGINS`) y antes de la línea en blanco que precede a `DB_ENGINE`, agregar:

```
# --- Login con Google Workspace (solo modulo de gestion) ---
# Credenciales de un OAuth 2.0 Client ID tipo "Web application" creado en
# Google Cloud Console. NO comitear valores reales.
# Redirect URI autorizado en la consola:
#   Local:      http://gestion.localhost:8000/oidc/callback/
#   Produccion: https://gestion.cmvalparaiso.cl/oidc/callback/
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
# Dominio institucional aceptado (claim hd del ID token).
GOOGLE_WORKSPACE_DOMAIN=cmvalparaiso.cl
```

- [ ] **Step 8: Commit**

```bash
git add requirements.txt cesfam_chatbot/settings.py .env.example
git commit -m "$(cat <<'EOF'
Configura mozilla-django-oidc contra Google Workspace

Agrega la dependencia pinneada y el bloque de settings OIDC con los
endpoints de Google. Las credenciales se leen de .env y nunca viven en el
repo. OIDC_CREATE_USER queda en False: no se crean cuentas al vuelo.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NTceB3VF7V3KyFngJuJc2T
EOF
)"
```

---

## Task 3: Backend de autenticación con las dos reglas de acceso

**Files:**
- Create: `gestion/auth.py`
- Modify: `cesfam_chatbot/settings.py` (agregar `AUTHENTICATION_BACKENDS`)
- Test: `gestion/tests.py`

**Interfaces:**
- Consumes: `gestion.models.PerfilUsuario` (Task 1); settings OIDC (Task 2).
- Produces: `gestion.auth.OIDCAuthenticationBackendGestion`, con `get_userinfo(access_token, id_token, payload) -> dict`, `verify_claims(claims) -> bool` y `filter_users_by_claims(claims) -> QuerySet[User]`.

**Contexto para quien implementa:** `mozilla_django_oidc` llama a estos hooks desde `get_or_create_user()` en este orden: `get_userinfo()` → `verify_claims()` → `filter_users_by_claims()`. Si `verify_claims` devuelve `False`, lanza `SuspiciousOperation`. Si `filter_users_by_claims` no devuelve exactamente un usuario y `OIDC_CREATE_USER` es `False`, el login falla y redirige a `LOGIN_REDIRECT_URL_FAILURE`.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `gestion/tests.py` (después de `HostRoutingTests`):

```python
OIDC_TEST_SETTINGS = {
    "GOOGLE_WORKSPACE_DOMAIN": "cmvalparaiso.cl",
    "OIDC_RP_CLIENT_ID": "test-client-id",
    "OIDC_RP_CLIENT_SECRET": "test-client-secret",
}


@override_settings(**OIDC_TEST_SETTINGS)
class BackendVerifyClaimsTests(TestCase):
    def setUp(self):
        from gestion.auth import OIDCAuthenticationBackendGestion

        self.backend = OIDCAuthenticationBackendGestion()

    def _claims(self, **overrides):
        base = {
            "email": "funcionario@cmvalparaiso.cl",
            "email_verified": True,
            "hd": "cmvalparaiso.cl",
        }
        base.update(overrides)
        return base

    def test_acepta_cuenta_del_dominio_institucional(self):
        self.assertTrue(self.backend.verify_claims(self._claims()))

    def test_rechaza_dominio_distinto(self):
        self.assertFalse(self.backend.verify_claims(self._claims(hd="otrodominio.cl")))

    def test_rechaza_cuenta_sin_claim_hd(self):
        claims = self._claims()
        del claims["hd"]
        self.assertFalse(self.backend.verify_claims(claims))

    def test_rechaza_correo_no_verificado(self):
        self.assertFalse(self.backend.verify_claims(self._claims(email_verified=False)))

    def test_rechaza_claims_sin_correo(self):
        claims = self._claims()
        del claims["email"]
        self.assertFalse(self.backend.verify_claims(claims))

    def test_combinar_claims_prioriza_los_del_id_token(self):
        # El endpoint de userinfo no siempre trae "hd"; el ID token si, y viene
        # firmado por Google, asi que manda por sobre la respuesta de userinfo.
        combinados = self.backend._combinar_claims(
            {"email": "funcionario@cmvalparaiso.cl"},
            {"hd": "cmvalparaiso.cl", "email": "suplantado@otro.cl"},
        )
        self.assertEqual(combinados["hd"], "cmvalparaiso.cl")
        self.assertEqual(combinados["email"], "suplantado@otro.cl")


@override_settings(**OIDC_TEST_SETTINGS)
class BackendFiltroDePerfilTests(TestCase):
    def setUp(self):
        from gestion.auth import OIDCAuthenticationBackendGestion

        self.backend = OIDCAuthenticationBackendGestion()
        self.centro = Centro.objects.get(pk=620)
        self.claims = {
            "email": "funcionario@cmvalparaiso.cl",
            "email_verified": True,
            "hd": "cmvalparaiso.cl",
        }

    def _usuario(self, correo="funcionario@cmvalparaiso.cl"):
        return User.objects.create_user(correo, email=correo)

    def test_usuario_con_perfil_activo_entra(self):
        usuario = self._usuario()
        PerfilUsuario.objects.create(
            usuario=usuario, rol=PerfilUsuario.Rol.SELECTOR, centro=self.centro
        )
        self.assertEqual(list(self.backend.filter_users_by_claims(self.claims)), [usuario])

    def test_usuario_sin_perfil_no_entra(self):
        self._usuario()
        self.assertEqual(list(self.backend.filter_users_by_claims(self.claims)), [])

    def test_usuario_con_perfil_inactivo_no_entra(self):
        usuario = self._usuario()
        PerfilUsuario.objects.create(
            usuario=usuario,
            rol=PerfilUsuario.Rol.SELECTOR,
            centro=self.centro,
            activo=False,
        )
        self.assertEqual(list(self.backend.filter_users_by_claims(self.claims)), [])

    def test_correo_desconocido_no_entra(self):
        usuario = self._usuario("otro@cmvalparaiso.cl")
        PerfilUsuario.objects.create(
            usuario=usuario, rol=PerfilUsuario.Rol.SELECTOR, centro=self.centro
        )
        self.assertEqual(list(self.backend.filter_users_by_claims(self.claims)), [])

    def test_claims_sin_correo_no_entra(self):
        self.assertEqual(list(self.backend.filter_users_by_claims({})), [])
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test gestion.tests.BackendVerifyClaimsTests gestion.tests.BackendFiltroDePerfilTests -v 2`
Expected: FAIL con `ModuleNotFoundError: No module named 'gestion.auth'`.

- [ ] **Step 3: Escribir el backend**

Crear `gestion/auth.py`:

```python
import logging

from django.conf import settings
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackendGestion(OIDCAuthenticationBackend):
    """Backend OIDC con las dos reglas de acceso del modulo de gestion:

    1. La cuenta debe pertenecer al dominio institucional (claim "hd").
    2. El usuario debe tener un PerfilUsuario activo dado de alta antes.

    No se crean cuentas al vuelo (OIDC_CREATE_USER = False en settings).
    """

    @staticmethod
    def _combinar_claims(userinfo, payload):
        """Combina la respuesta del endpoint userinfo con los claims del ID
        token. El ID token manda: es el que viene firmado por Google, y el
        endpoint de userinfo no siempre incluye "hd"."""
        combinados = dict(userinfo or {})
        combinados.update(payload or {})
        return combinados

    def get_userinfo(self, access_token, id_token, payload):
        userinfo = super().get_userinfo(access_token, id_token, payload)
        return self._combinar_claims(userinfo, payload)

    def verify_claims(self, claims):
        correo = claims.get("email")
        if not correo:
            logger.warning("Login rechazado: los claims no traen correo.")
            return False

        if not claims.get("email_verified", False):
            logger.warning("Login rechazado: correo no verificado (%s).", correo)
            return False

        dominio = settings.GOOGLE_WORKSPACE_DOMAIN
        if claims.get("hd") != dominio:
            logger.warning(
                "Login rechazado: %s no pertenece al dominio %s.", correo, dominio
            )
            return False

        return True

    def filter_users_by_claims(self, claims):
        """Solo entra quien tiene un perfil de gestion activo."""
        correo = claims.get("email")
        if not correo:
            return self.UserModel.objects.none()

        return self.UserModel.objects.filter(
            email__iexact=correo,
            perfil_gestion__activo=True,
        )
```

- [ ] **Step 4: Registrar el backend**

En `cesfam_chatbot/settings.py`, dentro del bloque OIDC agregado en Task 2, justo después de la línea `OIDC_RP_SCOPES = "openid email profile"`, agregar:

```python
AUTHENTICATION_BACKENDS = [
    "gestion.auth.OIDCAuthenticationBackendGestion",
    # Se mantiene el backend por password solo para superusuarios operando
    # el admin de Django; los funcionarios entran unicamente por Google.
    "django.contrib.auth.backends.ModelBackend",
]
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test gestion.tests.BackendVerifyClaimsTests gestion.tests.BackendFiltroDePerfilTests -v 2`
Expected: PASS (11 tests: 6 de claims + 5 de filtro).

- [ ] **Step 6: Correr la suite completa (regresión)**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test`
Expected: PASS — 33 tests (10 de `solicitudes` + 23 de `gestion`).

- [ ] **Step 7: Commit**

```bash
git add gestion/auth.py gestion/tests.py cesfam_chatbot/settings.py
git commit -m "$(cat <<'EOF'
Backend OIDC con validacion de dominio y de perfil activo

verify_claims exige correo verificado y claim hd igual al dominio
institucional; filter_users_by_claims deja pasar solo a quien tiene un
PerfilUsuario activo. El claim hd se toma del ID token firmado, no del
endpoint de userinfo, que no siempre lo incluye.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NTceB3VF7V3KyFngJuJc2T
EOF
)"
```

---

## Task 4: Rutas de login en el subdominio y gating del panel

**Files:**
- Modify: `cesfam_chatbot/urls_gestion.py`
- Modify: `cesfam_chatbot/urls.py`
- Modify: `gestion/views.py`
- Modify: `gestion/urls.py`
- Test: `gestion/tests.py`

**Interfaces:**
- Consumes: `gestion.auth.OIDCAuthenticationBackendGestion` (Task 3); settings `LOGIN_URL` y `LOGIN_REDIRECT_URL_FAILURE` (Task 2).
- Produces: `gestion.views.sin_acceso(request) -> HttpResponse` (status 200); rutas `oidc_authentication_init`, `oidc_authentication_callback` y `oidc_logout` bajo el prefijo `oidc/`, **solo** en el urlconf del subdominio de gestión; ruta `sin-acceso/` name `gestion:sin_acceso`.

**Contexto para quien implementa:** el admin de Django se mueve del host público (`morbilidad`) al subdominio de gestión. Hoy vive en `cesfam_chatbot/urls.py`, lo que deja un formulario de login por contraseña expuesto en el host público del chatbot — incoherente con "el login es solo por Google".

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `gestion/tests.py`:

```python
@override_settings(ALLOWED_HOSTS=["gestion.localhost", "testserver"], GESTION_HOST="gestion.localhost")
class RutasDeLoginTests(TestCase):
    def test_ruta_de_login_existe_en_el_subdominio(self):
        response = self.client.get("/oidc/authenticate/", HTTP_HOST="gestion.localhost")
        # Redirige al consentimiento de Google.
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])

    def test_ruta_de_login_no_existe_en_el_host_publico(self):
        response = self.client.get("/oidc/authenticate/", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, 404)

    def test_admin_no_existe_en_el_host_publico(self):
        response = self.client.get("/admin/", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, 404)

    def test_admin_existe_en_el_subdominio_de_gestion(self):
        response = self.client.get("/admin/", HTTP_HOST="gestion.localhost")
        # Sin sesion, el admin redirige a su propio login.
        self.assertEqual(response.status_code, 302)

    def test_sin_acceso_responde_200(self):
        response = self.client.get("/sin-acceso/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no tiene acceso", response.content.decode("utf-8").lower())


@override_settings(ALLOWED_HOSTS=["gestion.localhost", "testserver"], GESTION_HOST="gestion.localhost")
class PanelRequiereLoginTests(TestCase):
    def setUp(self):
        self.centro = Centro.objects.get(pk=620)

    def test_anonimo_es_redirigido_al_login(self):
        response = self.client.get("/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/oidc/authenticate/", response["Location"])

    def test_usuario_con_perfil_ve_el_panel(self):
        usuario = User.objects.create_user(
            "funcionario@cmvalparaiso.cl", email="funcionario@cmvalparaiso.cl"
        )
        PerfilUsuario.objects.create(
            usuario=usuario, rol=PerfilUsuario.Rol.SELECTOR, centro=self.centro
        )
        self.client.force_login(usuario)

        response = self.client.get("/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 200)
        self.assertIn("construcción", response.content.decode("utf-8"))

    def test_usuario_sin_perfil_no_ve_el_panel(self):
        usuario = User.objects.create_user(
            "colado@cmvalparaiso.cl", email="colado@cmvalparaiso.cl"
        )
        self.client.force_login(usuario)

        response = self.client.get("/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/sin-acceso/", response["Location"])
```

Además, `PanelPlaceholderTests` ya no aplica tal cual: llama a `panel(request)` con un `RequestFactory` sin usuario, y ahora la vista exige sesión. Reemplazar esa clase completa por:

```python
class PanelPlaceholderTests(TestCase):
    def test_panel_redirige_a_login_sin_sesion(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = panel(request)
        self.assertEqual(response.status_code, 302)
```

Y agregar `AnonymousUser` al import de auth al inicio del archivo, que queda:

```python
from django.contrib.auth.models import AnonymousUser, User
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test gestion.tests.RutasDeLoginTests gestion.tests.PanelRequiereLoginTests -v 2`
Expected: FAIL — `/oidc/authenticate/` da 404 en ambos hosts, `/admin/` sigue respondiendo en el host público, y el panel responde 200 sin sesión.

- [ ] **Step 3: Escribir las vistas**

Reemplazar el contenido de `gestion/views.py` por:

```python
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect


def _tiene_perfil_activo(usuario):
    perfil = getattr(usuario, "perfil_gestion", None)
    return perfil is not None and perfil.activo


@login_required
def panel(request):
    if not _tiene_perfil_activo(request.user):
        return redirect("gestion:sin_acceso")
    return HttpResponse("Módulo de gestión — en construcción")


def sin_acceso(request):
    return HttpResponse(
        "Su cuenta no tiene acceso al módulo de gestión. "
        "Solicite a la administración que le asigne un perfil.",
        status=200,
    )
```

- [ ] **Step 4: Agregar la ruta `sin-acceso/`**

Reemplazar el contenido de `gestion/urls.py` por:

```python
from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("sin-acceso/", views.sin_acceso, name="sin_acceso"),
]
```

- [ ] **Step 5: Exponer las rutas OIDC y el admin en el subdominio**

Reemplazar el contenido de `cesfam_chatbot/urls_gestion.py` por:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Login institucional con Google. Vive solo en este urlconf: el host
    # publico del chatbot no expone rutas de autenticacion.
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("admin/", admin.site.urls),
    path("", include("gestion.urls")),
]
```

- [ ] **Step 6: Sacar el admin del host público**

En `cesfam_chatbot/urls.py`, eliminar la línea del admin y su import. El archivo queda:

```python
from django.urls import path

from solicitudes import views


urlpatterns = [
    path("", views.saludbot, name="home"),
    path("chatbot/", views.chatbot, name="chatbot"),
    path("saludbot/", views.saludbot, name="saludbot"),
    path("terminos/", views.terminos, name="terminos"),
    path("api/solicitudes/", views.crear_solicitud, name="crear_solicitud"),
]
```

- [ ] **Step 7: Correr los tests y verificar que pasan**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test gestion.tests.RutasDeLoginTests gestion.tests.PanelRequiereLoginTests -v 2`
Expected: PASS (8 tests: 5 de rutas + 3 de panel).

- [ ] **Step 8: Correr la suite completa (regresión)**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py test`
Expected: PASS — 40 tests (10 de `solicitudes` + 30 de `gestion`). Ojo: `PanelPlaceholderTests` pasa de 2 tests a 1 en el Step 1, por eso el total sube en 7 y no en 8.

- [ ] **Step 9: Verificar el proyecto**

Run: `DB_ENGINE=sqlite .venv/bin/python manage.py check`
Expected: `System check identified no issues`.

- [ ] **Step 10: Commit**

```bash
git add cesfam_chatbot/urls_gestion.py cesfam_chatbot/urls.py gestion/views.py gestion/urls.py gestion/tests.py
git commit -m "$(cat <<'EOF'
Expone el login de Google y cierra el panel de gestion

Las rutas OIDC viven solo en el urlconf del subdominio de gestion. El panel
queda detras de login_required mas la verificacion de perfil activo; quien
entra sin perfil cae en una pagina de sin acceso.

Mueve el admin de Django al subdominio de gestion: estaba en el host publico
del chatbot, dejando un login por password expuesto donde no corresponde.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NTceB3VF7V3KyFngJuJc2T
EOF
)"
```

---

## Task 5: Documentación de puesta en marcha

**Files:**
- Modify: `docs/arquitectura-modulo-gestion.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: todo lo anterior. No produce código.

- [ ] **Step 1: Marcar el estado en el doc de arquitectura**

En `docs/arquitectura-modulo-gestion.md`, en la sección `## Estado`, reemplazar el párrafo que empieza con `Decisión de arquitectura **aprobada, sin implementar**.` por:

```markdown
Decisión de arquitectura **aprobada**. Autenticación y perfiles
**implementados** (ver `docs/superpowers/plans/2026-07-27-login-google-perfiles.md`).
Pendientes: modelo `Gestion` con Etapas 1 y 2, vistas worklist, deep-link de
WhatsApp y ventana horaria.
```

- [ ] **Step 2: Documentar el alta de usuarios en el README**

En `README.md`, al final del archivo, agregar:

```markdown
## Modulo de gestion: alta de usuarios

El acceso a `gestion.cmvalparaiso.cl` es solo con cuenta de Google Workspace
institucional, y ademas exige un perfil dado de alta. Un correo del dominio
sin perfil **no entra**: no se crean cuentas al vuelo.

Para dar de alta a alguien, desde el admin en el subdominio de gestion
(`/admin/`, con una cuenta superusuario):

1. Crear el `User` con el **correo institucional exacto** en el campo email.
   La contrasena es irrelevante (el login es por Google); dejar una aleatoria.
2. Crear su `Perfil de usuario` asignando rol, centro y, si corresponde,
   centro satelite.

Para revocar el acceso, desmarcar `activo` en el perfil. No borrar el usuario:
se pierde el historial de acciones.

### Configuracion de Google Cloud Console

Se necesita un **OAuth 2.0 Client ID** tipo *Web application*. Redirect URIs
autorizados:

- Local: `http://gestion.localhost:8000/oidc/callback/`
- Produccion: `https://gestion.cmvalparaiso.cl/oidc/callback/`

El `client_id` y el `client_secret` van en `.env` (ver `.env.example`); en
produccion, dentro del secret `ENV_PROD` del workflow de deploy.
```

- [ ] **Step 3: Commit**

```bash
git add docs/arquitectura-modulo-gestion.md README.md
git commit -m "$(cat <<'EOF'
Documenta el alta de usuarios del modulo de gestion

Explica en el README como dar de alta y revocar accesos, y que configuracion
necesita el OAuth Client ID en Google Cloud Console.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NTceB3VF7V3KyFngJuJc2T
EOF
)"
```

---

## Verificación manual (después de Task 5)

Estos pasos no son automatizables y requieren credenciales reales de Google.
Hacerlos antes de mergear a `main`.

- [ ] Crear el OAuth Client ID en Google Cloud Console con el redirect URI local.
- [ ] Poner `GOOGLE_OAUTH_CLIENT_ID` y `GOOGLE_OAUTH_CLIENT_SECRET` en `.env`.
- [ ] Levantar: `DB_ENGINE=sqlite .venv/bin/python manage.py runserver`.
- [ ] Crear un superusuario y darse de alta a uno mismo (User + PerfilUsuario).
- [ ] Entrar a `http://gestion.localhost:8000/` — debe redirigir a Google.
- [ ] Autenticarse con la cuenta institucional — debe llegar al panel.
- [ ] Repetir con una cuenta Gmail personal — debe quedar fuera.
- [ ] Desmarcar `activo` en el propio perfil, cerrar sesión y reintentar — debe caer en `/sin-acceso/`.
- [ ] Confirmar que `http://localhost:8000/admin/` responde 404 (el admin se movió).

**Nota para el deploy:** antes del primer push a `main` con estos cambios,
sumar `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` y
`GOOGLE_WORKSPACE_DOMAIN` al secret `ENV_PROD` del repositorio, y agregar
`https://gestion.cmvalparaiso.cl` a `CSRF_TRUSTED_ORIGINS`. Si el subdominio
todavía no tiene DNS ni certificado, eso es prerrequisito del deploy, no de
este plan.

---

## Self-Review

**1. Spec coverage** (contra `docs/arquitectura-modulo-gestion.md`):

- "el único mecanismo de login es OAuth con Google" → Task 2 (config) + Task 4 (rutas solo en gestión). ✓
- "La identidad la provee Google y vive en el `User`" → Task 3, `filter_users_by_claims` busca por email; no se duplican campos. ✓
- "Se restringe el `hd` al dominio institucional; un correo Gmail personal no puede entrar" → Task 3, `verify_claims`, con tests de dominio distinto y de claim ausente. ✓
- "La autorización (rol y centro) vive en una tabla propia" → Task 1. ✓
- "no tiene fila en la tabla de perfiles queda rechazado... No se crean cuentas automáticamente" → Task 2 (`OIDC_CREATE_USER = False`) + Task 3 (`filter_users_by_claims`) + Task 4 (gating del panel). ✓
- "`PerfilUsuario` con `OneToOne → User`" → Task 1. ✓
- "`rol` — exactamente uno por usuario (campo con choices, no M2M)" → Task 1, con test que fija los siete valores. ✓
- "`centro` FK, `centro_satelite` FK opcional" → Task 1. ✓
- "`activo` — permite revocar el acceso sin borrar el historial" → Task 1 + test de perfil inactivo en Task 3 + README en Task 5. ✓
- "`correo` y `nombre` no se duplican acá" → Task 1, el modelo no los tiene. ✓
- Tabla de roles y alcances → Task 1, `ROLES_TODOS_LOS_CENTROS` y `centros_permitidos()`, con tests por rol. ✓
- "OAuth de Google: `client_id` y `client_secret` por `.env`, nunca en el repo" → Task 2 Steps 4 y 7. ✓
- "El admin de Django queda solo para superusuarios" → Task 4 Steps 5-6 lo mueve al subdominio; el gating por superusuario es el propio del admin. ✓

**2. Placeholder scan:** sin TBD/TODO. Todo paso que toca código trae el código completo. 

**3. Type consistency:**
- `PerfilUsuario` define `related_name="perfil_gestion"` en Task 1; Task 3 lo usa en `perfil_gestion__activo` y Task 4 en `getattr(usuario, "perfil_gestion", None)`. Coinciden.
- `PerfilUsuario.Rol.SELECTOR` usado igual en Tasks 1, 3 y 4.
- `_combinar_claims(userinfo, payload)` definido en Task 3 Step 3 y usado en el test del Step 1 con el mismo orden de argumentos.
- `GOOGLE_WORKSPACE_DOMAIN` definido en Task 2 Step 4 y consumido en Task 3 Step 3.
- `gestion:sin_acceso` nombrado en `gestion/urls.py` (Task 4 Step 4) y usado en `views.panel` (Step 3) y en el test (Step 1).
- `LOGIN_REDIRECT_URL_FAILURE = "/sin-acceso/"` (Task 2) coincide con la ruta `sin-acceso/` de Task 4.

**4. Supuestos que conviene confirmar antes de ejecutar:**
- `PerfilUsuario.centro` es **obligatorio** para todos los roles, incluidos `ADMIN` y `SUPERVISOR_DAS`, para quienes es informativo y no limita lo que ven. Si el personal del DAS no pertenece a ningún CESFAM, el campo debería pasar a `null=True` y ajustarse `centros_permitidos()` — es un cambio de una línea más la migración.
- El conteo de tests esperado en cada tarea supone que la suite de `solicitudes` se mantiene en 10.
