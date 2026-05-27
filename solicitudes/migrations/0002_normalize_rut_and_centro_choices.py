from django.db import migrations, models


CENTROS = [
    ("600", "Centro De Salud Familiar Laguna Verde"),
    ("605", "Centro De Salud Familiar Placilla (Valparaiso)"),
    ("610", "Centro De Salud Familiar Placeres"),
    ("615", "Centro De Salud Familiar Baron"),
    ("620", "Centro De Salud Familiar Rodelillo"),
    ("621", "Centro De Salud Familiar Padre Damian Molokai"),
    ("625", "Centro De Salud Familiar Quebrada Verde"),
    ("630", "Centro De Salud Familiar Las Canas"),
    ("635", "Centro De Salud Familiar Mena"),
    ("640", "Centro De Salud Familiar Puertas Negras"),
    ("645", "Centro De Salud Familiar Cordillera"),
    ("650", "Centro De Salud Familiar Esperanza"),
    ("655", "Centro De Salud Familiar Reina Isabel II"),
]


def normalize_existing_rows(apps, schema_editor):
    Solicitud = apps.get_model("solicitudes", "Solicitud")
    for solicitud in Solicitud.objects.all():
        if solicitud.rut:
            clean = solicitud.rut.replace(".", "").replace("-", "").upper()
            solicitud.rut = f"{clean[:-1]}-{clean[-1]}"

        if not str(solicitud.centro_salud).isdigit():
            solicitud.centro_salud = "620"

        solicitud.save(update_fields=["rut", "centro_salud"])


class Migration(migrations.Migration):
    dependencies = [
        ("solicitudes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(normalize_existing_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="solicitud",
            name="centro_salud",
            field=models.CharField(choices=CENTROS, max_length=3),
        ),
    ]
