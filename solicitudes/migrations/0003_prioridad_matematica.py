from django.db import migrations, models


PRIORIDAD_CHOICES = [
    ("URGENTE", "Urgente"),
    ("ALTA", "Alta"),
    ("MEDIA", "Media"),
    ("BAJA", "Baja"),
]


def migrar_prioridades(apps, schema_editor):
    Solicitud = apps.get_model("solicitudes", "Solicitud")
    mapping = {
        "P1": ("URGENTE", 6),
        "P2": ("ALTA", 4),
        "P3": ("MEDIA", 2),
        "P4": ("BAJA", 0),
    }

    for solicitud in Solicitud.objects.all():
        prioridad, puntaje = mapping.get(solicitud.priorizacion_solicitud, ("BAJA", 0))
        solicitud.priorizacion_solicitud = prioridad
        solicitud.puntaje_prioridad = puntaje
        solicitud.save(update_fields=["priorizacion_solicitud", "puntaje_prioridad"])


class Migration(migrations.Migration):
    dependencies = [
        ("solicitudes", "0002_normalize_rut_and_centro_choices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="solicitud",
            name="priorizacion_solicitud",
            field=models.CharField(choices=PRIORIDAD_CHOICES, default="BAJA", max_length=8),
        ),
        migrations.AddField(
            model_name="solicitud",
            name="puntaje_prioridad",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.RunPython(migrar_prioridades, migrations.RunPython.noop),
    ]
