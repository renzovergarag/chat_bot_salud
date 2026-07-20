from django.test import TestCase, override_settings
from django.test.client import RequestFactory

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
