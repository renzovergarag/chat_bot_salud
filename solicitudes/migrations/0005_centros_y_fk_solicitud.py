from django.db import migrations, models
import django.db.models.deletion


CENTROS = [
    (600, "Centro De Salud Familiar Laguna Verde"),
    (605, "Centro De Salud Familiar Placilla (Valparaiso)"),
    (610, "Centro De Salud Familiar Placeres"),
    (615, "Centro De Salud Familiar Baron"),
    (620, "Centro De Salud Familiar Rodelillo"),
    (621, "Centro De Salud Familiar Padre Damian Molokai"),
    (625, "Centro De Salud Familiar Quebrada Verde"),
    (626, "Centro Comunitario De Salud Familiar Porvenir Bajo"),
    (627, "Centro Comunitario De Salud Familiar Juan Pablo II"),
    (630, "Centro De Salud Familiar Las Canas"),
    (635, "Centro De Salud Familiar Mena"),
    (640, "Centro De Salud Familiar Puertas Negras"),
    (645, "Centro De Salud Familiar Cordillera"),
    (650, "Centro De Salud Familiar Esperanza"),
    (655, "Centro De Salud Familiar Reina Isabel II"),
]


def cargar_centros(apps, schema_editor):
    Centro = apps.get_model("solicitudes", "Centro")
    for id_centro, centro in CENTROS:
        Centro.objects.update_or_create(id_centro=id_centro, defaults={"centro": centro})


class Migration(migrations.Migration):
    dependencies = [
        ("solicitudes", "0004_condiciones_adjuntos_terminos"),
    ]

    operations = [
        migrations.CreateModel(
            name="Centro",
            fields=[
                ("id_centro", models.IntegerField(primary_key=True, serialize=False)),
                ("centro", models.CharField(max_length=150, unique=True)),
            ],
            options={
                "verbose_name": "centro",
                "verbose_name_plural": "centros",
                "db_table": "centros",
                "ordering": ["id_centro"],
            },
        ),
        migrations.RunPython(cargar_centros, migrations.RunPython.noop),
        migrations.AddField(
            model_name="solicitud",
            name="nombre_completo",
            field=models.CharField(blank=True, default="", max_length=150),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="solicitud",
            name="centro_salud",
            field=models.ForeignKey(
                db_column="id_centro",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="solicitudes",
                to="solicitudes.centro",
            ),
        ),
    ]
