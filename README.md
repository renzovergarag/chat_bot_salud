# SaludBot

SaludBot es una aplicacion web Django para registrar solicitudes de morbilidad mediante una interfaz tipo chatbot. Valida RUT chileno, recopila datos basicos del paciente, guarda el CESFAM como ID y calcula una prioridad interna para el equipo de salud.

## Stack

- Python 3.12
- Django 5
- MySQL local
- PyMySQL
- HTML, CSS y JavaScript simple

## Estructura

```text
cesfam_chatbot/       Configuracion Django
solicitudes/          Modelo, API, admin, validadores y reglas de prioridad
templates/chat/       Template principal de SaludBot
static/css/           Estilos del chatbot
static/js/            Flujo conversacional frontend
sql/                  Script SQL para MySQL Workbench
```

## Preparar El Proyecto

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Crear el archivo local de variables:

```powershell
Copy-Item .env.example .env
notepad .env
```

Configura `.env` con tus credenciales MySQL:

```env
DB_ENGINE=mysql
DB_NAME=cesfam_chatbot
DB_USER=root
DB_PASSWORD=tu_password
DB_HOST=127.0.0.1
DB_PORT=3306
```



## Crear Base De Datos MySQL

En MySQL Workbench abre y ejecuta:

[sql/crear_mysql_saludbot.sql](sql/crear_mysql_saludbot.sql)

Luego prepara Django para usar esa tabla:

```powershell
.\check_mysql_connection.ps1
.\prepare_mysql.ps1
```

`prepare_mysql.ps1` marca como aplicadas las migraciones de `solicitudes` si la tabla fue creada manualmente desde Workbench, y crea las tablas internas de Django para admin, auth y sesiones.

## Ejecutar En Desarrollo

Con MySQL:

```powershell
.\run_local_mysql.ps1
```

Abrir:

```text
http://127.0.0.1:8000/
```

Admin Django:

```text
http://127.0.0.1:8000/admin/
```

Para crear usuario administrador:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

## Pruebas Rápidas Con SQLite

Solo para desarrollo local sin MySQL:

```powershell
.\run_local_sqlite.ps1
```

Si usas OneDrive y SQLite falla con `disk I/O error`, el script usa una base temporal fuera de la carpeta sincronizada.

## Tests

```powershell
$env:DB_ENGINE="sqlite"
.\.venv\Scripts\python.exe manage.py test
```

## Datos Guardados

La tabla principal es:

```text
solicitudes_solicitud
```

Campos relevantes:

- `rut`: se guarda sin puntos y con guion, por ejemplo `25747311-2`.
- `centro_salud`: se guarda como ID, por ejemplo `635`.
- `priorizacion_solicitud`: `URGENTE`, `ALTA`, `MEDIA` o `BAJA`.
- `puntaje_prioridad`: puntaje interno calculado por reglas.
- `credencial_cuidador_discapacidad_foto`: adjunto de foto en base64 cuando el paciente decide tomarla.
- `Neurodivergente_prais_gestante_tipo`: especificacion interna cuando declara neurodivergente, cuidador neurodivergente, PRAIS, gestante u otro.
- `Neurodivergente_prais_gestante_otro`: texto maximo de 50 caracteres para la opcion `OTRO`.
- `acepta_terminos`: debe quedar en `True` para permitir el registro desde el chatbot.

Pagina de terminos:

```text
http://127.0.0.1:8000/terminos/
```

## Comandos Útiles

Verificar conexion MySQL:

```powershell
.\check_mysql_connection.ps1
```

Preparar migraciones MySQL:

```powershell
.\prepare_mysql.ps1
```

Consultar en Workbench:

```sql
SELECT *
FROM cesfam_chatbot.solicitudes_solicitud
ORDER BY id_solicitud DESC;
```

## Subir A Git

Inicializar repo si aun no existe:

```powershell
git init
git add .
git status
git commit -m "Initial SaludBot Django project"
```

Antes de hacer `git add .`, confirma que no aparezcan:

```text
.env
.venv/
db.sqlite3
staticfiles/
```

## Despliegue En Render

Render debe instalar dependencias, recopilar archivos estaticos y luego arrancar Gunicorn.

```text
Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput
Start Command: gunicorn cesfam_chatbot.wsgi:application
```

Variables de entorno recomendadas:

```env
DEBUG=False
SECRET_KEY=una_clave_larga_y_segura
ALLOWED_HOSTS=chat-bot-salud.onrender.com
DB_ENGINE=mysql
DB_NAME=nombre_base_datos
DB_USER=usuario_base_datos
DB_PASSWORD=password_base_datos
DB_HOST=host_real_de_mysql
DB_PORT=3306
```

`DB_HOST=127.0.0.1` solo funciona para MySQL local. En Render debe apuntar al host real de la base de datos.
