from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .validators import formatear_rut_sin_puntos, validar_rut_chileno, validar_telefono_chileno


class Solicitud(models.Model):
    class Sexo(models.TextChoices):
        FEMENINO = "F", "Femenino"
        MASCULINO = "M", "Masculino"
        OTRO = "O", "Otro"
        PREFIERE_NO_DECIR = "N", "Prefiere no decir"

    class Prioridad(models.TextChoices):
        URGENTE = "URGENTE", "Urgente"
        ALTA = "ALTA", "Alta"
        MEDIA = "MEDIA", "Media"
        BAJA = "BAJA", "Baja"

    class CentroSalud(models.TextChoices):
        LAGUNA_VERDE = "600", "Centro De Salud Familiar Laguna Verde"
        PLACILLA = "605", "Centro De Salud Familiar Placilla (Valparaiso)"
        PLACERES = "610", "Centro De Salud Familiar Placeres"
        BARON = "615", "Centro De Salud Familiar Baron"
        RODELILLO = "620", "Centro De Salud Familiar Rodelillo"
        PADRE_DAMIAN = "621", "Centro De Salud Familiar Padre Damian Molokai"
        QUEBRADA_VERDE = "625", "Centro De Salud Familiar Quebrada Verde"
        LAS_CANAS = "630", "Centro De Salud Familiar Las Canas"
        MENA = "635", "Centro De Salud Familiar Mena"
        PUERTAS_NEGRAS = "640", "Centro De Salud Familiar Puertas Negras"
        CORDILLERA = "645", "Centro De Salud Familiar Cordillera"
        ESPERANZA = "650", "Centro De Salud Familiar Esperanza"
        REINA_ISABEL = "655", "Centro De Salud Familiar Reina Isabel II"

    class TipoCondicion(models.TextChoices):
        NEURODIVERGENTE = "NEURODIVERGENTE", "Neurodivergente"
        CUIDADOR_NEURODIVERGENTE = "CUIDADOR_NEURODIVERGENTE", "Cuidador neurodivergente"
        PRAIS = "PRAIS", "PRAIS"
        GESTANTE = "GESTANTE", "Gestante"
        OTRO = "OTRO", "Otro"

    id_solicitud = models.BigAutoField(primary_key=True)
    rut = models.CharField(max_length=12, validators=[validar_rut_chileno])
    edad = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    telefono = models.CharField(max_length=12, validators=[validar_telefono_chileno])
    centro_salud = models.CharField(max_length=3, choices=CentroSalud.choices)
    credendencial_cuidador_discapacidad = models.BooleanField(default=False)
    credencial_cuidador_discapacidad_foto = models.TextField(blank=True)
    Neurodivergente_prais_gestante = models.BooleanField(default=False)
    Neurodivergente_prais_gestante_tipo = models.CharField(
        max_length=32,
        choices=TipoCondicion.choices,
        blank=True,
    )
    Neurodivergente_prais_gestante_otro = models.CharField(max_length=50, blank=True)
    acepta_terminos = models.BooleanField(default=False)
    motivo = models.CharField(max_length=160)
    detalle_motivo = models.TextField()
    fecha_solicitud = models.DateField(default=timezone.localdate)
    date_solicitud = models.DateTimeField(auto_now_add=True)
    priorizacion_solicitud = models.CharField(max_length=8, choices=Prioridad.choices, default=Prioridad.BAJA)
    puntaje_prioridad = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-date_solicitud"]
        verbose_name = "solicitud"
        verbose_name_plural = "solicitudes"

    def __str__(self):
        return f"Solicitud #{self.id_solicitud} - {self.rut} - {self.priorizacion_solicitud}"

    def clean(self):
        super().clean()
        if self.rut:
            self.rut = formatear_rut_sin_puntos(self.rut)

        if not self.acepta_terminos:
            raise ValidationError({"acepta_terminos": "Debes aceptar los terminos y condiciones."})

        if not self.credendencial_cuidador_discapacidad:
            self.credencial_cuidador_discapacidad_foto = ""

        if not self.Neurodivergente_prais_gestante:
            self.Neurodivergente_prais_gestante_tipo = ""
            self.Neurodivergente_prais_gestante_otro = ""
            return

        if self.Neurodivergente_prais_gestante and not self.Neurodivergente_prais_gestante_tipo:
            raise ValidationError(
                {"Neurodivergente_prais_gestante_tipo": "Debes especificar la condicion declarada."}
            )

        if self.Neurodivergente_prais_gestante_tipo == self.TipoCondicion.OTRO and not self.Neurodivergente_prais_gestante_otro.strip():
            raise ValidationError(
                {"Neurodivergente_prais_gestante_otro": "Debes especificar la opcion otro."}
            )

        if self.Neurodivergente_prais_gestante_tipo != self.TipoCondicion.OTRO:
            self.Neurodivergente_prais_gestante_otro = ""
