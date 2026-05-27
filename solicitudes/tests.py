import json

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Solicitud
from .priorizacion import calcular_prioridad
from .validators import validar_rut_chileno, validar_telefono_chileno


class SolicitudTests(TestCase):
    def valid_payload(self):
        return {
            "rut": "25.747.311-2",
            "edad": 34,
            "sexo": "F",
            "telefono": "+56985881767",
            "centro_salud": "620",
            "credendencial_cuidador_discapacidad": False,
            "Neurodivergente_prais_gestante": False,
            "motivo": "consulta medica",
            "detalle_motivo": "dolor de garganta hace tres dias",
        }

    def test_creacion_solicitud_valida(self):
        payload = self.valid_payload()
        prioridad = calcular_prioridad(payload)
        payload["priorizacion_solicitud"] = prioridad["clasificacion"]
        payload["puntaje_prioridad"] = prioridad["puntaje"]
        solicitud = Solicitud(**payload)
        solicitud.full_clean()
        solicitud.save()

        self.assertEqual(solicitud.id_solicitud, 1)
        self.assertEqual(solicitud.priorizacion_solicitud, "BAJA")
        self.assertEqual(solicitud.puntaje_prioridad, 0)
        self.assertEqual(solicitud.rut, "25747311-2")
        self.assertEqual(solicitud.centro_salud, "620")

    def test_rechaza_rut_invalido(self):
        with self.assertRaises(ValidationError):
            validar_rut_chileno("20.112.654-8")

    def test_rechaza_telefono_invalido(self):
        with self.assertRaises(ValidationError):
            validar_telefono_chileno("85881767")

    def test_prioridad_por_reglas(self):
        self.assertEqual(calcular_prioridad({"detalle_motivo": "control", "edad": 5})["clasificacion"], "MEDIA")
        self.assertEqual(calcular_prioridad({"detalle_motivo": "control", "edad": 65})["clasificacion"], "MEDIA")
        self.assertEqual(
            calcular_prioridad(
                {
                    "detalle_motivo": "control",
                    "edad": 40,
                    "credendencial_cuidador_discapacidad": True,
                }
            )["clasificacion"],
            "MEDIA",
        )
        self.assertEqual(
            calcular_prioridad(
                {
                    "detalle_motivo": "control",
                    "edad": 40,
                    "Neurodivergente_prais_gestante": True,
                }
            )["clasificacion"],
            "MEDIA",
        )
        self.assertEqual(
            calcular_prioridad(
                {
                    "detalle_motivo": "control",
                    "edad": 65,
                    "credendencial_cuidador_discapacidad": True,
                }
            )["clasificacion"],
            "ALTA",
        )
        self.assertEqual(
            calcular_prioridad({"detalle_motivo": "dolor pecho intenso", "edad": 65})["clasificacion"],
            "URGENTE",
        )
        self.assertEqual(calcular_prioridad({"detalle_motivo": "control", "edad": 40})["clasificacion"], "BAJA")

    def test_endpoint_crea_solicitud(self):
        response = self.client.post(
            reverse("crear_solicitud"),
            data=json.dumps(self.valid_payload()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["id_solicitud"], 1)
        self.assertEqual(body["priorizacion_solicitud"], "BAJA")
        self.assertEqual(body["puntaje_prioridad"], 0)
        self.assertEqual(body["resumen"]["rut"], "25747311-2")
        self.assertEqual(body["resumen"]["centro_salud"], "620")

    def test_endpoint_acepta_payload_saludbot(self):
        response = self.client.post(
            reverse("crear_solicitud"),
            data=json.dumps(
                {
                    "rut": "25.747.311-2",
                    "edad": 34,
                    "telefono": "+56985881767",
                    "centro_salud": "620",
                    "motivo": "Tengo fiebre",
                    "detalle_motivo": "Fiebre desde ayer con dolor de cuerpo",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        solicitud = Solicitud.objects.get()
        self.assertEqual(solicitud.rut, "25747311-2")
        self.assertEqual(solicitud.centro_salud, "620")
        self.assertEqual(solicitud.sexo, "N")
        self.assertEqual(solicitud.puntaje_prioridad, 1)
        self.assertEqual(solicitud.priorizacion_solicitud, "BAJA")
