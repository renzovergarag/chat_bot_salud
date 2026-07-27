from django.contrib import admin

from .models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol", "centro", "centro_satelite", "activo")
    list_filter = ("rol", "activo", "centro")
    search_fields = ("usuario__email", "usuario__first_name", "usuario__last_name")
    autocomplete_fields = ("usuario",)
    list_select_related = ("usuario", "centro", "centro_satelite")
