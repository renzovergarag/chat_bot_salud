from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("sin-acceso/", views.sin_acceso, name="sin_acceso"),
]
