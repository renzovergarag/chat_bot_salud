from django.contrib import admin

from .models import Centro, Solicitud


@admin.register(Centro)
class CentroAdmin(admin.ModelAdmin):
    list_display = ("id_centro", "centro")
    search_fields = ("centro",)


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = (
        "id_solicitud",
        "nombre",
        "rut",
        "edad",
        "sexo",
        "telefono",
        "centro_salud",
        "credendencial_cuidador_discapacidad",
        "Neurodivergente_prais_gestante",
        "Neurodivergente_prais_gestante_tipo",
        "acepta_terminos",
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
    search_fields = ("nombre", "rut", "telefono", "motivo", "detalle_motivo")
    readonly_fields = ("date_solicitud",)
