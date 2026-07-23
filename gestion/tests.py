from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from solicitudes.models import Centro, Solicitud
from gestion.models import ComunicadorSeleccion, SelectorDemanda, UsuarioGestion
from gestion.views import panel


class PanelPlaceholderTests(TestCase):
    def test_panel_responde_200(self):
        request = RequestFactory().get("/")
        response = panel(request)
        self.assertEqual(response.status_code, 200)

    def test_panel_muestra_texto_en_construccion(self):
        request = RequestFactory().get("/")
        response = panel(request)
        self.assertIn("construcción", response.content.decode("utf-8"))


class ModelosGestionTests(TestCase):
    def setUp(self):
        self.centro = Centro.objects.get(pk=620)
        self.usuario = UsuarioGestion.objects.create(
            id_rol="SEL",
            rol=UsuarioGestion.Rol.SELECTOR,
            correo="selector@example.com",
            nombre_completo="Selector Prueba",
            centro=self.centro,
        )
        self.solicitud = Solicitud.objects.create(
            rut="25747311-2",
            nombre_completo="Paciente Prueba",
            edad=34,
            sexo=Solicitud.Sexo.PREFIERE_NO_DECIR,
            telefono="+56949106239",
            centro_salud=self.centro,
            acepta_terminos=True,
            motivo="consulta medica",
            detalle_motivo="dolor de garganta hace tres dias",
        )

    def test_usuario_gestion_usa_tabla_usuarios_y_centros(self):
        self.assertEqual(UsuarioGestion._meta.db_table, "usuarios")
        self.assertEqual(self.usuario.centro_id, 620)
        self.assertIsNone(self.usuario.centro_satelite)
        self.assertTrue(self.usuario.activo)

    def test_selector_demanda_relaciona_solicitud_y_usuario(self):
        seleccion = SelectorDemanda.objects.create(
            solicitud=self.solicitud,
            usuario_selector=self.usuario,
            rut_selector="25747311-2",
            clasificacion="Morbilidad",
            prioridad=Solicitud.Prioridad.ALTA,
            suma_prioridad=4,
            observacion="Evaluacion inicial",
        )

        self.assertEqual(SelectorDemanda._meta.db_table, "selector_demanda")
        self.assertEqual(seleccion.solicitud_id, self.solicitud.id_solicitud)
        self.assertEqual(seleccion.usuario_selector_id, self.usuario.id_usuario)

    def test_comunicador_seleccion_relaciona_seleccion_y_usuario(self):
        comunicador = UsuarioGestion.objects.create(
            id_rol="COM",
            rol=UsuarioGestion.Rol.COMUNICADOR,
            correo="comunicador@example.com",
            nombre_completo="Comunicador Prueba",
            centro=self.centro,
        )
        seleccion = SelectorDemanda.objects.create(solicitud=self.solicitud)
        comunicacion = ComunicadorSeleccion.objects.create(
            seleccion=seleccion,
            usuario_comunicador=comunicador,
            rut_comunicador="25747311-2",
            estado=ComunicadorSeleccion.Estado.AGENDADO,
            enviado=True,
        )

        self.assertEqual(ComunicadorSeleccion._meta.db_table, "comunicador_seleccion")
        self.assertEqual(comunicacion.seleccion_id, seleccion.id_seleccion)
        self.assertEqual(comunicacion.usuario_comunicador_id, comunicador.id_usuario)


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
