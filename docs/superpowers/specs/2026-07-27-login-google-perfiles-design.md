# Login con Google Workspace y perfiles de usuario — Diseño

Fecha: 2026-07-27
Relacionado: `docs/arquitectura-modulo-gestion.md`, `docs/superpowers/plans/2026-07-27-login-google-perfiles.md`

> Este documento **registra decisiones ya tomadas**, no explora alternativas
> abiertas. El marco (login solo con Google, tabla complementaria de perfiles,
> los siete roles) lo definió el equipo; el resto de las decisiones técnicas se
> tomaron en la sesión del 2026-07-27 y quedan aquí con su justificación.

## Objetivo

Que un funcionario entre a `gestion.cmvalparaiso.cl` autenticándose con su
cuenta de Google Workspace institucional, y que el sistema sepa **quién es**
(identidad, vía Google) y **qué puede ver** (rol y centro, vía una tabla
propia). Quien no tenga perfil dado de alta no entra, aunque su login con
Google sea válido.

## Alcance

**Dentro de alcance:**

- Modelo `PerfilUsuario` (`OneToOne → User`) con rol, centro, centro satélite,
  anexo y flag de activo.
- Flujo OIDC completo contra Google, expuesto solo en el subdominio de gestión.
- Las dos reglas de acceso: dominio institucional y perfil activo.
- Gating del panel de gestión y página de "sin acceso".
- Alta de usuarios por el admin de Django.

**Fuera de alcance (etapas siguientes):**

- Modelo `Gestion` con las Etapas 1 y 2, y sus vistas worklist.
- Deep-link de WhatsApp (Etapa 2).
- Ventana horaria del chatbot.
- UI de administración de perfiles para el rol `SOME` (por ahora, admin de Django).
- Permisos finos por rol en las vistas de operación: este spec deja el *dato*
  (rol y centros permitidos), no las reglas de cada pantalla.
- DNS y certificado del subdominio: prerrequisito del deploy, no de este trabajo.

## Decisiones tomadas

### 1. Librería: `mozilla-django-oidc`

Descartadas:

- **`django-allauth`** — la opción estándar, y en dependencias es casi empate
  (`allauth[socialaccount]` suma oauthlib + requests + pyjwt; mozilla suma pyjwt
  + requests). Se descarta por **superficie**: al incluir `allauth.urls` quedan
  expuestas rutas de signup, reset de contraseña, verificación de correo y
  gestión de cuenta, que hay que apagar activamente por settings. Para un módulo
  interno con datos de salud se prefiere que la funcionalidad no exista a que
  esté configurada en off. Además agrega modelos y migraciones propias.
- **Flujo OAuth escrito a mano** (~150 líneas con `requests`). Da control total
  y cero dependencias nuevas, pero obliga a hacerse cargo de `state`, `nonce`,
  verificación de firma y rotación de claves. No se justifica el riesgo.

A favor de mozilla-django-oidc: hace exactamente una cosa, y sus hooks
`verify_claims` y `filter_users_by_claims` son justo los dos puntos donde
entran las dos reglas de acceso definidas por el equipo. Se pinnea a `5.0.2`.

Contra, asumido: cadencia de releases más lenta (5.0.2 es de diciembre 2025,
allauth 65.18.0 es de mayo 2026), y si algún día se necesita MFA o un segundo
proveedor de identidad, allauth ya lo trae y acá habría que construirlo.

### 2. La identidad vive en `User`; el perfil solo agrega autorización

`PerfilUsuario` **no** guarda correo ni nombre: los puebla Google en el `User`
de `django.contrib.auth`. Guarda únicamente lo que Google no sabe: rol, centro,
centro satélite, anexo y `activo`.

Descartado: la tabla `usuarios` autónoma que proponía el PR #5, con `correo`,
`nombre_completo` e `id_rol` propios y sin relación con `django.contrib.auth`.
Duplicaba la identidad y dejaba dos fuentes de verdad para el mismo dato.

### 3. Sin alta automática al primer login

`OIDC_CREATE_USER = False`. Un correo del dominio que autentica bien pero no
tiene perfil **no entra**: la tabla de perfiles es la lista de autorización.

Descartado: crear el usuario al vuelo con rol pendiente y mostrarle una
pantalla de espera. Es más cómodo para el alta masiva inicial, pero deja
cuentas a medio crear y convierte "cualquier funcionario del municipio" en
"usuario del sistema esperando rol". Con datos de salud, la lista blanca
explícita es preferible.

Consecuencia operativa: el alta es un acto deliberado (crear `User` + perfil),
y la baja es desmarcar `activo`, nunca borrar — para no perder el historial de
acciones.

### 4. El dominio se valida contra el claim `hd` del ID token

El parámetro `hd` de la request de autorización es **solo una pista de UI**:
acota el selector de cuentas de Google, pero no es una garantía y no debe
tratarse como control de acceso. La verificación real se hace sobre el claim
`hd` del ID token, que viene firmado por Google.

Detalle de implementación: `mozilla_django_oidc` le pasa a `verify_claims()`
la respuesta del *endpoint de userinfo*, que no siempre incluye `hd`. Por eso
se sobrescribe `get_userinfo()` para combinarla con los claims del ID token,
dándole prioridad a estos últimos por venir firmados.

Se valida además `email_verified`.

### 5. Un rol por usuario, no acumulables

Campo `rol` con choices. Se descarta una M2M a una tabla de roles porque los
roles compuestos que definió el equipo (`FULL` = selección + comunicación;
`SOME` = eso más gestión de perfiles) ya son las combinaciones necesarias: si
los roles se pudieran acumular, esos dos no existirían.

### 6. Alcance por rol, no por lista de centros

`centro` + `centro_satelite` opcional. `ADMIN` y `SUPERVISOR_DAS` ven todos los
centros; el resto ve su centro y su satélite.

Descartados:

- **M2M usuario ↔ centros**, que era lo que decía la versión anterior de
  `docs/arquitectura-modulo-gestion.md`. Existía para cubrir "perfiles de
  coordinación que ven varios centros" — necesidad que ahora resuelven los
  roles `ADMIN` y `SUPERVISOR_DAS`. Sin ese caso, la M2M solo agrega tabla
  puente, joins en cada queryset y UI de administración.
- **Un solo centro sin satélite.** Más simple, pero no modela el caso real:
  un CESFAM con su CECOSF asociado (626 Porvenir Bajo, 627 Juan Pablo II).

Supuesto asumido, conviene confirmarlo: `centro` es obligatorio para **todos**
los roles. Para `ADMIN` y `SUPERVISOR_DAS` es informativo y no limita lo que
ven. Si el personal del DAS no pertenece a ningún CESFAM, el campo debería
pasar a nullable — cambio de una línea más migración.

### 7. El admin de Django se muda al subdominio de gestión

Hoy `/admin/` vive en el urlconf del host público (`morbilidad.cmvalparaiso.cl`),
lo que deja un formulario de login por contraseña expuesto en el host del
chatbot público — incoherente con "el login es solo por Google". Se mueve a
`cesfam_chatbot/urls_gestion.py`.

Es un cambio de comportamiento en producción: quien use `morbilidad.../admin/`
hoy, deberá usar `gestion.../admin/`.

El backend por contraseña (`ModelBackend`) se conserva en
`AUTHENTICATION_BACKENDS` **solo** para superusuarios operando el admin; los
funcionarios entran únicamente por Google.

## Modelo de datos

```
PerfilUsuario (tabla gestion_perfil_usuario)
├── usuario          OneToOne → auth.User, related_name="perfil_gestion"
├── rol              CharField(20) choices: los 7 roles
├── centro           FK → solicitudes.Centro, RESTRICT
├── centro_satelite  FK → solicitudes.Centro, SET_NULL, opcional
├── anexo_telefono   CharField(20), opcional
└── activo           Boolean, default True
```

Helpers de alcance, consumidos después por los querysets de la operación:

- `ve_todos_los_centros` → `bool`, verdadero para `ADMIN` y `SUPERVISOR_DAS`.
- `centros_permitidos()` → `QuerySet[Centro]`.

### Roles

| Rol | Alcance | Qué hace |
| --- | --- | --- |
| `ADMIN` | Todos los centros | Todo |
| `SUPERVISOR_DAS` | Todos los centros | Vista administrativa |
| `SUPERVISOR_CENTRO` | Su centro (+ satélite) | Vista administrativa |
| `SOME` | Su centro (+ satélite) | Gestión de perfiles + Etapa 1 + Etapa 2 |
| `FULL` | Su centro (+ satélite) | Etapa 1 + Etapa 2 |
| `SELECTOR` | Su centro (+ satélite) | Etapa 1 (selección de demanda) |
| `COMUNICADOR` | Su centro (+ satélite) | Etapa 2 (contacto y agendamiento) |

## Flujo de login

1. Anónimo entra a `gestion.cmvalparaiso.cl/` → `login_required` redirige a
   `/oidc/authenticate/`.
2. `mozilla_django_oidc` redirige a Google con `hd` y `prompt=select_account`.
3. Google vuelve a `/oidc/callback/` con el code; la librería canjea el token.
4. `get_userinfo()` combina userinfo + claims del ID token.
5. `verify_claims()` exige `email`, `email_verified` y `hd == dominio`. Si
   falla, `SuspiciousOperation`.
6. `filter_users_by_claims()` busca un `User` con ese correo **y** perfil
   activo. Si no hay exactamente uno, y con `OIDC_CREATE_USER=False`, el login
   falla y redirige a `/sin-acceso/`.
7. Con sesión iniciada, `panel` revalida el perfil activo antes de responder.

El paso 7 es redundante con el 6 para quien entra por Google, y deliberado:
cubre las sesiones creadas por otra vía (un superusuario logueado por el admin,
o un perfil desactivado después de iniciar sesión).

## Verificación

Automatizable (ver el plan): tests de modelo y alcance por rol, de
`verify_claims` (dominio distinto, claim ausente, correo no verificado), de
`filter_users_by_claims` (sin perfil, perfil inactivo, correo desconocido), de
que las rutas OIDC existen solo en el subdominio, y de que el panel rechaza al
anónimo y al usuario sin perfil.

No automatizable, requiere credenciales reales: el ida y vuelta contra Google,
y que una cuenta Gmail personal quede efectivamente fuera.

## Notas de despliegue (fuera de alcance, para la etapa de deploy)

- Crear un **OAuth 2.0 Client ID** tipo *Web application* en Google Cloud
  Console. Redirect URIs: `http://gestion.localhost:8000/oidc/callback/` (local)
  y `https://gestion.cmvalparaiso.cl/oidc/callback/` (producción).
- Sumar `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` y
  `GOOGLE_WORKSPACE_DOMAIN` al secret `ENV_PROD` del workflow de deploy.
- Agregar `https://gestion.cmvalparaiso.cl` a `CSRF_TRUSTED_ORIGINS`.
- El subdominio necesita DNS y certificado antes del primer login real.
