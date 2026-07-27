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

        if claims.get("email_verified") is not True:
            logger.warning("Login rechazado: correo no verificado (%s).", correo)
            return False

        dominio = settings.GOOGLE_WORKSPACE_DOMAIN
        hd = claims.get("hd")
        if not hd or hd.lower() != dominio.lower():
            logger.warning(
                "Login rechazado: %s no pertenece al dominio %s.", correo, dominio
            )
            return False

        return True

    def filter_users_by_claims(self, claims):
        """Solo entra quien tiene un perfil de gestion activo y cuya cuenta
        de Django siga activa (User.is_active). Esto solo se ejecuta al
        momento del login: mozilla_django_oidc no vuelve a llamarlo para
        recargar la sesion, por eso gestion/views.py::_tiene_perfil_activo
        chequea is_active de nuevo en cada request."""
        correo = claims.get("email")
        if not correo:
            return self.UserModel.objects.none()

        return self.UserModel.objects.filter(
            email__iexact=correo,
            is_active=True,
            perfil_gestion__activo=True,
        )

    def update_user(self, user, claims):
        """Sincroniza nombre y apellido desde los claims de Google en cada
        login. El correo NO se toca aca: es la clave con la que se dio de
        alta al usuario y con la que filter_users_by_claims hace el match;
        sobrescribirlo desde los claims podria romper ese vinculo."""
        cambios = False

        nombre = claims.get("given_name")
        if nombre and user.first_name != nombre:
            user.first_name = nombre
            cambios = True

        apellido = claims.get("family_name")
        if apellido and user.last_name != apellido:
            user.last_name = apellido
            cambios = True

        if cambios:
            user.save()

        return user
