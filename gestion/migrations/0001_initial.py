from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("solicitudes", "0005_centros_y_fk_solicitud"),
    ]

    operations = [
        migrations.CreateModel(
            name="UsuarioGestion",
            fields=[
                ("id_usuario", models.BigAutoField(primary_key=True, serialize=False)),
                ("id_rol", models.CharField(max_length=8)),
                (
                    "rol",
                    models.CharField(
                        choices=[
                            ("Administrador/a", "Administrador/a"),
                            ("Selector", "Selector"),
                            ("Comunicador", "Comunicador"),
                        ],
                        max_length=16,
                    ),
                ),
                ("correo", models.EmailField(max_length=150)),
                ("nombre_completo", models.CharField(max_length=150)),
                ("anexo_telefono", models.CharField(blank=True, max_length=20, null=True)),
                ("activo", models.BooleanField(default=True)),
                (
                    "centro",
                    models.ForeignKey(
                        db_column="id_centro",
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="usuarios_gestion",
                        to="solicitudes.centro",
                    ),
                ),
                (
                    "centro_satelite",
                    models.ForeignKey(
                        blank=True,
                        db_column="id_centro_satelite",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="usuarios_gestion_satelite",
                        to="solicitudes.centro",
                    ),
                ),
            ],
            options={
                "verbose_name": "usuario de gestion",
                "verbose_name_plural": "usuarios de gestion",
                "db_table": "usuarios",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("rol__in", ["Administrador/a", "Selector", "Comunicador"])),
                        name="chk_usuarios_rol",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="SelectorDemanda",
            fields=[
                ("id_seleccion", models.BigAutoField(primary_key=True, serialize=False)),
                ("rut_selector", models.CharField(blank=True, max_length=12, null=True)),
                ("fecha_accion", models.DateTimeField(auto_now_add=True)),
                ("clasificacion", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "prioridad",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("URGENTE", "Urgente"),
                            ("ALTA", "Alta"),
                            ("MEDIA", "Media"),
                            ("BAJA", "Baja"),
                        ],
                        max_length=8,
                        null=True,
                    ),
                ),
                ("suma_prioridad", models.PositiveSmallIntegerField(default=0)),
                ("observacion", models.TextField(blank=True, null=True)),
                (
                    "solicitud",
                    models.ForeignKey(
                        db_column="id_solicitud",
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="selecciones_demanda",
                        to="solicitudes.solicitud",
                    ),
                ),
                (
                    "usuario_selector",
                    models.ForeignKey(
                        blank=True,
                        db_column="id_usuario_selector",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="selecciones_realizadas",
                        to="gestion.usuariogestion",
                    ),
                ),
            ],
            options={
                "verbose_name": "seleccion de demanda",
                "verbose_name_plural": "selecciones de demanda",
                "db_table": "selector_demanda",
                "ordering": ["-fecha_accion"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("prioridad__isnull", True), ("prioridad__in", ["URGENTE", "ALTA", "MEDIA", "BAJA"]), _connector="OR"),
                        name="chk_selector_prioridad",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ComunicadorSeleccion",
            fields=[
                ("id_comunicador", models.BigAutoField(primary_key=True, serialize=False)),
                ("rut_comunicador", models.CharField(blank=True, max_length=12, null=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente"),
                            ("CONTACTADO", "Contactado"),
                            ("AGENDADO", "Agendado"),
                            ("NO_CONTACTADO", "No contactado"),
                            ("RECHAZADO", "Rechazado"),
                            ("FINALIZADO", "Finalizado"),
                        ],
                        default="PENDIENTE",
                        max_length=16,
                    ),
                ),
                ("fecha_hora_agendamiento", models.DateTimeField(blank=True, null=True)),
                ("enviado", models.BooleanField(default=False)),
                (
                    "seleccion",
                    models.ForeignKey(
                        db_column="id_seleccion",
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="comunicaciones",
                        to="gestion.selectordemanda",
                    ),
                ),
                (
                    "usuario_comunicador",
                    models.ForeignKey(
                        blank=True,
                        db_column="id_usuario_comunicador",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="comunicaciones_realizadas",
                        to="gestion.usuariogestion",
                    ),
                ),
            ],
            options={
                "verbose_name": "comunicacion de seleccion",
                "verbose_name_plural": "comunicaciones de seleccion",
                "db_table": "comunicador_seleccion",
                "ordering": ["-id_comunicador"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("estado__in", ["PENDIENTE", "CONTACTADO", "AGENDADO", "NO_CONTACTADO", "RECHAZADO", "FINALIZADO"])),
                        name="chk_comunicador_estado",
                    )
                ],
            },
        ),
        migrations.AddIndex(
            model_name="usuariogestion",
            index=models.Index(fields=["correo"], name="idx_usuarios_correo"),
        ),
        migrations.AddIndex(
            model_name="usuariogestion",
            index=models.Index(fields=["rol"], name="idx_usuarios_rol"),
        ),
        migrations.AddIndex(
            model_name="usuariogestion",
            index=models.Index(fields=["centro"], name="idx_usuarios_centro"),
        ),
        migrations.AddIndex(
            model_name="usuariogestion",
            index=models.Index(fields=["centro_satelite"], name="idx_usuarios_centro_satelite"),
        ),
        migrations.AddIndex(
            model_name="selectordemanda",
            index=models.Index(fields=["solicitud"], name="idx_selector_solicitud"),
        ),
        migrations.AddIndex(
            model_name="selectordemanda",
            index=models.Index(fields=["usuario_selector"], name="idx_selector_usuario"),
        ),
        migrations.AddIndex(
            model_name="selectordemanda",
            index=models.Index(fields=["fecha_accion"], name="idx_selector_fecha"),
        ),
        migrations.AddIndex(
            model_name="selectordemanda",
            index=models.Index(fields=["prioridad"], name="idx_selector_prioridad"),
        ),
        migrations.AddIndex(
            model_name="comunicadorseleccion",
            index=models.Index(fields=["seleccion"], name="idx_comunicador_seleccion"),
        ),
        migrations.AddIndex(
            model_name="comunicadorseleccion",
            index=models.Index(fields=["usuario_comunicador"], name="idx_comunicador_usuario"),
        ),
        migrations.AddIndex(
            model_name="comunicadorseleccion",
            index=models.Index(fields=["estado"], name="idx_comunicador_estado"),
        ),
        migrations.AddIndex(
            model_name="comunicadorseleccion",
            index=models.Index(fields=["fecha_hora_agendamiento"], name="idx_comunicador_agendamiento"),
        ),
    ]
