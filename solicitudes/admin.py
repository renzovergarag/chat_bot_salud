from django.contrib import admin

from .models import Solicitud


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = (
        "id_solicitud",
        "rut",
        "edad",
        "sexo",
        "telefono",
        "centro_salud",
        "priorizacion_solicitud",
        "puntaje_prioridad",
        "date_solicitud",
    )
    list_filter = (
        "priorizacion_solicitud",
        "sexo",
        "credendencial_cuidador_discapacidad",
        "Neurodivergente_prais_gestante",
        "centro_salud",
    )
    search_fields = ("rut", "telefono", "motivo", "detalle_motivo")
    readonly_fields = ("date_solicitud",)
