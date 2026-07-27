from django.contrib.auth.models import AnonymousUser, User
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from gestion.models import PerfilUsuario
from gestion.views import panel
from solicitudes.models import Centro


class PanelPlaceholderTests(TestCase):
    def test_panel_redirige_a_login_sin_sesion(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = panel(request)
        self.assertEqual(response.status_code, 302)


class PerfilUsuarioTests(TestCase):
    def setUp(self):
        self.centro = Centro.objects.get(pk=620)
        self.satelite = Centro.objects.get(pk=626)

    def _perfil(self, rol, correo, satelite=None):
        usuario = User.objects.create_user(correo, email=correo)
        return PerfilUsuario.objects.create(
            usuario=usuario,
            rol=rol,
            centro=self.centro,
            centro_satelite=satelite,
        )

    def test_perfil_arranca_activo(self):
        perfil = self._perfil(PerfilUsuario.Rol.SELECTOR, "selector@example.com")
        self.assertTrue(perfil.activo)
        self.assertEqual(perfil.usuario.perfil_gestion, perfil)

    def test_rol_de_centro_solo_ve_su_centro(self):
        perfil = self._perfil(PerfilUsuario.Rol.SELECTOR, "selector@example.com")
        self.assertFalse(perfil.ve_todos_los_centros)
        self.assertEqual([c.pk for c in perfil.centros_permitidos()], [620])

    def test_rol_de_centro_con_satelite_ve_ambos(self):
        perfil = self._perfil(
            PerfilUsuario.Rol.COMUNICADOR, "comunicador@example.com", satelite=self.satelite
        )
        self.assertEqual(sorted(c.pk for c in perfil.centros_permitidos()), [620, 626])

    def test_admin_y_supervisor_das_ven_todos_los_centros(self):
        admin = self._perfil(PerfilUsuario.Rol.ADMIN, "admin@example.com")
        das = self._perfil(PerfilUsuario.Rol.SUPERVISOR_DAS, "das@example.com")

        total = Centro.objects.count()
        for perfil in (admin, das):
            self.assertTrue(perfil.ve_todos_los_centros)
            self.assertEqual(perfil.centros_permitidos().count(), total)

    def test_supervisor_centro_no_ve_todos(self):
        perfil = self._perfil(PerfilUsuario.Rol.SUPERVISOR_CENTRO, "supervisor@example.com")
        self.assertFalse(perfil.ve_todos_los_centros)

    def test_un_usuario_no_puede_tener_dos_perfiles(self):
        perfil = self._perfil(PerfilUsuario.Rol.SELECTOR, "selector@example.com")
        # transaction.atomic es necesario: sin el, la IntegrityError deja la
        # transaccion del TestCase rota y falla el teardown.
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilUsuario.objects.create(
                usuario=perfil.usuario,
                rol=PerfilUsuario.Rol.COMUNICADOR,
                centro=self.centro,
            )

    def test_los_siete_roles_estan_definidos(self):
        self.assertEqual(
            [rol.value for rol in PerfilUsuario.Rol],
            [
                "ADMIN",
                "SUPERVISOR_DAS",
                "SUPERVISOR_CENTRO",
                "SOME",
                "FULL",
                "SELECTOR",
                "COMUNICADOR",
            ],
        )


@override_settings(ALLOWED_HOSTS=["gestion.localhost", "testserver"], GESTION_HOST="gestion.localhost")
class HostRoutingTests(TestCase):
    def test_subdominio_gestion_resuelve_placeholder(self):
        response = self.client.get("/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 200)
        self.assertIn("construcción", response.content.decode("utf-8"))

    def test_host_default_resuelve_chatbot(self):
        response = self.client.get("/", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("construcción", response.content.decode("utf-8"))

    def test_url_del_chatbot_no_existe_en_subdominio_gestion(self):
        response = self.client.get("/terminos/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 404)


OIDC_TEST_SETTINGS = {
    "GOOGLE_WORKSPACE_DOMAIN": "cmvalparaiso.cl",
    "OIDC_RP_CLIENT_ID": "test-client-id",
    "OIDC_RP_CLIENT_SECRET": "test-client-secret",
}


@override_settings(**OIDC_TEST_SETTINGS)
class BackendVerifyClaimsTests(TestCase):
    def setUp(self):
        from gestion.auth import OIDCAuthenticationBackendGestion

        self.backend = OIDCAuthenticationBackendGestion()

    def _claims(self, **overrides):
        base = {
            "email": "funcionario@cmvalparaiso.cl",
            "email_verified": True,
            "hd": "cmvalparaiso.cl",
        }
        base.update(overrides)
        return base

    def test_acepta_cuenta_del_dominio_institucional(self):
        self.assertTrue(self.backend.verify_claims(self._claims()))

    def test_rechaza_dominio_distinto(self):
        self.assertFalse(self.backend.verify_claims(self._claims(hd="otrodominio.cl")))

    def test_rechaza_cuenta_sin_claim_hd(self):
        claims = self._claims()
        del claims["hd"]
        self.assertFalse(self.backend.verify_claims(claims))

    def test_rechaza_correo_no_verificado(self):
        self.assertFalse(self.backend.verify_claims(self._claims(email_verified=False)))

    def test_rechaza_claims_sin_correo(self):
        claims = self._claims()
        del claims["email"]
        self.assertFalse(self.backend.verify_claims(claims))

    def test_combinar_claims_prioriza_los_del_id_token(self):
        # El endpoint de userinfo no siempre trae "hd"; el ID token si, y viene
        # firmado por Google, asi que manda por sobre la respuesta de userinfo.
        combinados = self.backend._combinar_claims(
            {"email": "funcionario@cmvalparaiso.cl"},
            {"hd": "cmvalparaiso.cl", "email": "suplantado@otro.cl"},
        )
        self.assertEqual(combinados["hd"], "cmvalparaiso.cl")
        self.assertEqual(combinados["email"], "suplantado@otro.cl")


@override_settings(**OIDC_TEST_SETTINGS)
class BackendFiltroDePerfilTests(TestCase):
    def setUp(self):
        from gestion.auth import OIDCAuthenticationBackendGestion

        self.backend = OIDCAuthenticationBackendGestion()
        self.centro = Centro.objects.get(pk=620)
        self.claims = {
            "email": "funcionario@cmvalparaiso.cl",
            "email_verified": True,
            "hd": "cmvalparaiso.cl",
        }

    def _usuario(self, correo="funcionario@cmvalparaiso.cl"):
        return User.objects.create_user(correo, email=correo)

    def test_usuario_con_perfil_activo_entra(self):
        usuario = self._usuario()
        PerfilUsuario.objects.create(
            usuario=usuario, rol=PerfilUsuario.Rol.SELECTOR, centro=self.centro
        )
        self.assertEqual(list(self.backend.filter_users_by_claims(self.claims)), [usuario])

    def test_usuario_sin_perfil_no_entra(self):
        self._usuario()
        self.assertEqual(list(self.backend.filter_users_by_claims(self.claims)), [])

    def test_usuario_con_perfil_inactivo_no_entra(self):
        usuario = self._usuario()
        PerfilUsuario.objects.create(
            usuario=usuario,
            rol=PerfilUsuario.Rol.SELECTOR,
            centro=self.centro,
            activo=False,
        )
        self.assertEqual(list(self.backend.filter_users_by_claims(self.claims)), [])

    def test_correo_desconocido_no_entra(self):
        usuario = self._usuario("otro@cmvalparaiso.cl")
        PerfilUsuario.objects.create(
            usuario=usuario, rol=PerfilUsuario.Rol.SELECTOR, centro=self.centro
        )
        self.assertEqual(list(self.backend.filter_users_by_claims(self.claims)), [])

    def test_claims_sin_correo_no_entra(self):
        self.assertEqual(list(self.backend.filter_users_by_claims({})), [])


@override_settings(ALLOWED_HOSTS=["gestion.localhost", "testserver"], GESTION_HOST="gestion.localhost")
class RutasDeLoginTests(TestCase):
    def test_ruta_de_login_existe_en_el_subdominio(self):
        response = self.client.get("/oidc/authenticate/", HTTP_HOST="gestion.localhost")
        # Redirige al consentimiento de Google.
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])

    def test_ruta_de_login_no_existe_en_el_host_publico(self):
        response = self.client.get("/oidc/authenticate/", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, 404)

    def test_admin_no_existe_en_el_host_publico(self):
        response = self.client.get("/admin/", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, 404)

    def test_admin_existe_en_el_subdominio_de_gestion(self):
        response = self.client.get("/admin/", HTTP_HOST="gestion.localhost")
        # Sin sesion, el admin redirige a su propio login.
        self.assertEqual(response.status_code, 302)

    def test_sin_acceso_responde_200(self):
        response = self.client.get("/sin-acceso/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no tiene acceso", response.content.decode("utf-8").lower())


@override_settings(ALLOWED_HOSTS=["gestion.localhost", "testserver"], GESTION_HOST="gestion.localhost")
class PanelRequiereLoginTests(TestCase):
    def setUp(self):
        self.centro = Centro.objects.get(pk=620)

    def test_anonimo_es_redirigido_al_login(self):
        response = self.client.get("/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/oidc/authenticate/", response["Location"])

    def test_usuario_con_perfil_ve_el_panel(self):
        usuario = User.objects.create_user(
            "funcionario@cmvalparaiso.cl", email="funcionario@cmvalparaiso.cl"
        )
        PerfilUsuario.objects.create(
            usuario=usuario, rol=PerfilUsuario.Rol.SELECTOR, centro=self.centro
        )
        self.client.force_login(usuario)

        response = self.client.get("/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 200)
        self.assertIn("construcción", response.content.decode("utf-8"))

    def test_usuario_sin_perfil_no_ve_el_panel(self):
        usuario = User.objects.create_user(
            "colado@cmvalparaiso.cl", email="colado@cmvalparaiso.cl"
        )
        self.client.force_login(usuario)

        response = self.client.get("/", HTTP_HOST="gestion.localhost")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/sin-acceso/", response["Location"])
