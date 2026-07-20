from django.urls import include, path

# TODO: agregar auth-gating (login_required) antes de exponer datos reales en este subdominio.

urlpatterns = [
    path("", include("gestion.urls")),
]
