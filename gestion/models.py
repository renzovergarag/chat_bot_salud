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
