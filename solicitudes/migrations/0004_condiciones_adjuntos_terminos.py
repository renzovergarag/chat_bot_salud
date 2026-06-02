from django.db import migrations, models


TIPO_CONDICION_CHOICES = [
    ("NEURODIVERGENTE", "Neurodivergente"),
    ("CUIDADOR_NEURODIVERGENTE", "Cuidador neurodivergente"),
    ("PRAIS", "PRAIS"),
    ("GESTANTE", "Gestante"),
    ("OTRO", "Otro"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("solicitudes", "0003_prioridad_matematica"),
    ]

    operations = [
        migrations.AddField(
            model_name="solicitud",
            name="credencial_cuidador_discapacidad_foto",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="solicitud",
            name="Neurodivergente_prais_gestante_tipo",
            field=models.CharField(blank=True, choices=TIPO_CONDICION_CHOICES, max_length=32),
        ),
        migrations.AddField(
            model_name="solicitud",
            name="Neurodivergente_prais_gestante_otro",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="solicitud",
            name="acepta_terminos",
            field=models.BooleanField(default=False),
        ),
    ]
