from django.db import migrations, models
import django.core.validators
import django.utils.timezone
import solicitudes.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Solicitud",
            fields=[
                ("id_solicitud", models.BigAutoField(primary_key=True, serialize=False)),
                ("rut", models.CharField(max_length=12, validators=[solicitudes.validators.validar_rut_chileno])),
                (
                    "edad",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(120),
                        ]
                    ),
                ),
                (
                    "sexo",
                    models.CharField(
                        choices=[
                            ("F", "Femenino"),
                            ("M", "Masculino"),
                            ("O", "Otro"),
                            ("N", "Prefiere no decir"),
                        ],
                        max_length=1,
                    ),
                ),
                ("telefono", models.CharField(max_length=12, validators=[solicitudes.validators.validar_telefono_chileno])),
                ("centro_salud", models.CharField(max_length=160)),
                ("credendencial_cuidador_discapacidad", models.BooleanField(default=False)),
                ("Neurodivergente_prais_gestante", models.BooleanField(default=False)),
                ("motivo", models.CharField(max_length=160)),
                ("detalle_motivo", models.TextField()),
                ("fecha_solicitud", models.DateField(default=django.utils.timezone.localdate)),
                ("date_solicitud", models.DateTimeField(auto_now_add=True)),
                (
                    "priorizacion_solicitud",
                    models.CharField(
                        choices=[("P1", "P1"), ("P2", "P2"), ("P3", "P3"), ("P4", "P4")],
                        default="P4",
                        max_length=2,
                    ),
                ),
            ],
            options={
                "verbose_name": "solicitud",
                "verbose_name_plural": "solicitudes",
                "ordering": ["-date_solicitud"],
            },
        ),
    ]
