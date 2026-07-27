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
