from django.db import models

from solicitudes.models import Centro, Solicitud


class UsuarioGestion(models.Model):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "Administrador/a", "Administrador/a"
        SELECTOR = "Selector", "Selector"
        COMUNICADOR = "Comunicador", "Comunicador"

    id_usuario = models.BigAutoField(primary_key=True)
    id_rol = models.CharField(max_length=8)
    rol = models.CharField(max_length=16, choices=Rol.choices)
    correo = models.EmailField(max_length=150)
    nombre_completo = models.CharField(max_length=150)
    centro = models.ForeignKey(
        Centro,
        db_column="id_centro",
        on_delete=models.RESTRICT,
        related_name="usuarios_gestion",
    )
    centro_satelite = models.ForeignKey(
        Centro,
        db_column="id_centro_satelite",
        on_delete=models.SET_NULL,
        related_name="usuarios_gestion_satelite",
        blank=True,
        null=True,
    )
    anexo_telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "usuarios"
        indexes = [
            models.Index(fields=["correo"], name="idx_usuarios_correo"),
            models.Index(fields=["rol"], name="idx_usuarios_rol"),
            models.Index(fields=["centro"], name="idx_usuarios_centro"),
            models.Index(fields=["centro_satelite"], name="idx_usuarios_centro_satelite"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rol__in=["Administrador/a", "Selector", "Comunicador"]),
                name="chk_usuarios_rol",
            ),
        ]
        verbose_name = "usuario de gestion"
        verbose_name_plural = "usuarios de gestion"

    def __str__(self):
        return f"{self.nombre_completo} ({self.rol})"


class SelectorDemanda(models.Model):
    id_seleccion = models.BigAutoField(primary_key=True)
    solicitud = models.ForeignKey(
        Solicitud,
        db_column="id_solicitud",
        on_delete=models.RESTRICT,
        related_name="selecciones_demanda",
    )
    usuario_selector = models.ForeignKey(
        UsuarioGestion,
        db_column="id_usuario_selector",
        on_delete=models.SET_NULL,
        related_name="selecciones_realizadas",
        blank=True,
        null=True,
    )
    rut_selector = models.CharField(max_length=12, blank=True, null=True)
    fecha_accion = models.DateTimeField(auto_now_add=True)
    clasificacion = models.CharField(max_length=50, blank=True, null=True)
    prioridad = models.CharField(max_length=8, choices=Solicitud.Prioridad.choices, blank=True, null=True)
    suma_prioridad = models.PositiveSmallIntegerField(default=0)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "selector_demanda"
        indexes = [
            models.Index(fields=["solicitud"], name="idx_selector_solicitud"),
            models.Index(fields=["usuario_selector"], name="idx_selector_usuario"),
            models.Index(fields=["fecha_accion"], name="idx_selector_fecha"),
            models.Index(fields=["prioridad"], name="idx_selector_prioridad"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(prioridad__isnull=True)
                | models.Q(prioridad__in=["URGENTE", "ALTA", "MEDIA", "BAJA"]),
                name="chk_selector_prioridad",
            ),
        ]
        ordering = ["-fecha_accion"]
        verbose_name = "seleccion de demanda"
        verbose_name_plural = "selecciones de demanda"

    def __str__(self):
        return f"Seleccion #{self.id_seleccion} - Solicitud #{self.solicitud_id}"


class ComunicadorSeleccion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONTACTADO = "CONTACTADO", "Contactado"
        AGENDADO = "AGENDADO", "Agendado"
        NO_CONTACTADO = "NO_CONTACTADO", "No contactado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        FINALIZADO = "FINALIZADO", "Finalizado"

    id_comunicador = models.BigAutoField(primary_key=True)
    seleccion = models.ForeignKey(
        SelectorDemanda,
        db_column="id_seleccion",
        on_delete=models.RESTRICT,
        related_name="comunicaciones",
    )
    usuario_comunicador = models.ForeignKey(
        UsuarioGestion,
        db_column="id_usuario_comunicador",
        on_delete=models.SET_NULL,
        related_name="comunicaciones_realizadas",
        blank=True,
        null=True,
    )
    rut_comunicador = models.CharField(max_length=12, blank=True, null=True)
    estado = models.CharField(max_length=16, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_hora_agendamiento = models.DateTimeField(blank=True, null=True)
    enviado = models.BooleanField(default=False)

    class Meta:
        db_table = "comunicador_seleccion"
        indexes = [
            models.Index(fields=["seleccion"], name="idx_comunicador_seleccion"),
            models.Index(fields=["usuario_comunicador"], name="idx_comunicador_usuario"),
            models.Index(fields=["estado"], name="idx_comunicador_estado"),
            models.Index(fields=["fecha_hora_agendamiento"], name="idx_comunicador_agendamiento"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    estado__in=[
                        "PENDIENTE",
                        "CONTACTADO",
                        "AGENDADO",
                        "NO_CONTACTADO",
                        "RECHAZADO",
                        "FINALIZADO",
                    ]
                ),
                name="chk_comunicador_estado",
            ),
        ]
        ordering = ["-id_comunicador"]
        verbose_name = "comunicacion de seleccion"
        verbose_name_plural = "comunicaciones de seleccion"

    def __str__(self):
        return f"Comunicacion #{self.id_comunicador} - Seleccion #{self.seleccion_id}"
