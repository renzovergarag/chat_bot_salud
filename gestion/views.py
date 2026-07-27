from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect


def _tiene_perfil_activo(usuario):
    # mozilla_django_oidc sobreescribe get_user() sin llamar a
    # user_can_authenticate() (a diferencia de ModelBackend), asi que
    # desmarcar User.is_active en el admin no revoca por si solo una sesion
    # ya iniciada. Lo chequeamos aca ademas de en el perfil.
    if not usuario.is_active:
        return False
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
        "Solicite a la administración que le asigne un perfil."
    )
