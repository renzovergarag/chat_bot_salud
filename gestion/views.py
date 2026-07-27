from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect


def _tiene_perfil_activo(usuario):
    perfil = getattr(usuario, "perfil_gestion", None)
    return perfil is not None and perfil.activo


@login_required
def panel(request):
    if not _tiene_perfil_activo(request.user):
        return redirect("gestion:sin_acceso")
    return HttpResponse("Módulo de gestión — en construcción")


def sin_acceso(request):
    return HttpResponse(
        "Su cuenta no tiene acceso al módulo de gestión. "
        "Solicite a la administración que le asigne un perfil.",
        status=200,
    )
