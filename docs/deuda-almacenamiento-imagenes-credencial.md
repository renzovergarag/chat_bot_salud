# Deuda técnica: almacenamiento de fotos de credencial de discapacidad

## Resumen

La foto de la credencial de cuidador/discapacidad **no se guarda como
archivo**, sino como un string **base64 inline dentro de la base de datos**,
en la misma fila de la solicitud. Es una solución válida para el MVP, pero no
escala ni envejece bien, y tiene al menos un bug presente que hace fallar las
fotos reales.

## Cómo funciona hoy

1. **Frontend** (`static/js/saludbot.js:626`): `reader.readAsDataURL(file)`
   convierte la foto a un data-URI base64 (`data:image/jpeg;base64,...`).
2. Ese string viaja como un campo más del JSON del POST
   (`static/js/saludbot.js:518`).
3. **Backend** (`solicitudes/views.py:99-101`): el valor entra directo al
   modelo y se persiste en `credencial_cuidador_discapacidad_foto`, definido
   como `models.TextField(blank=True)` (`solicitudes/models.py:56`). En MySQL,
   Django mapea `TextField` a `LONGTEXT`.

Resultado: la imagen vive como base64 en la tabla `solicitud`, en MySQL (o
SQLite en local según `DB_ENGINE`). No existe `MEDIA_ROOT`, `MEDIA_URL`,
`ImageField`/`FileField`, ni almacenamiento externo (S3).

## Problemas identificados

### 1. Bug presente: las fotos reales probablemente ya fallan

`settings.py` no define `DATA_UPLOAD_MAX_MEMORY_SIZE`, así que aplica el
default de Django: **2.5 MB para todo el body del request**. Una foto de
celular de ~2 MB pesa ~2.7 MB en base64 → Django rechaza el POST con
`RequestDataTooBig` (HTTP 400). Además **no hay validación de tamaño** ni en
frontend ni en backend, por lo que el usuario no recibe una explicación clara.

### 2. Overhead de almacenamiento (+33%)

La codificación base64 infla los bytes un tercio; cada certificado ocupa más
que el archivo original.

### 3. La tabla principal se vuelve pesada y lenta

Django hace `SELECT *` por defecto. El admin, la priorización y cualquier
listado o export arrastran el blob base64 completo aunque no lo necesiten. No
se usa `.defer()` / `.only()`. Con miles de solicitudes, listar en el admin se
degrada.

### 4. Backups inflados

Un `mysqldump` con `LONGTEXT` inline crece mucho y se vuelve lento —
problema que se suma al de despliegue/backup de producción.

### 5. Dato sensible sin ciclo de vida

Es un **certificado de discapacidad = dato de salud / PII**. Hoy queda
permanente en la DB y en todos los backups, **sin cifrado en reposo ni
política de retención/borrado**. Además el frontend muestra al usuario "La
foto se adjunta solo a esta solicitud" (`static/js/saludbot.js:360`), lo cual
es engañoso: la imagen se persiste de forma permanente.

## Recomendación

Sacar la imagen de la fila y guardarla como archivo, dejando en la tabla solo
una referencia:

- Cambiar `credencial_cuidador_discapacidad_foto: TextField` →
  `FileField(upload_to="credenciales/%Y/%m/", blank=True)`.
- Configurar `MEDIA_ROOT` / `MEDIA_URL`; en producción servir con nginx o
  mover a S3/compatible (django-storages) para escalar sin depender del disco
  del servidor.
- Recibir la foto como `multipart/form-data` (subida real), no base64 en JSON.
- Validar tamaño y tipo (p. ej. máx 5 MB, solo imágenes) en frontend **y**
  backend.
- Definir política de retención (borrar la imagen tras cierto tiempo o tras
  procesar la solicitud) y alinear el texto que ve el usuario con lo que
  realmente ocurre.
- Considerar la migración de los base64 ya guardados a archivos.

Con esto la tabla queda liviana, los backups no se inflan, escala a
almacenamiento externo y el dato sensible pasa a tener control de acceso y
ciclo de vida.

## Estado

Deuda **documentada, sin resolver**. Pendiente de priorizar. El fix mínimo y
urgente es subir `DATA_UPLOAD_MAX_MEMORY_SIZE` y validar tamaño para que las
fotos dejen de fallar silenciosamente; el fix estructural es migrar a
`FileField` + almacenamiento externo.

## Referencias

- `solicitudes/models.py:56` — definición del campo `TextField`.
- `solicitudes/views.py:99-101` — persistencia del payload.
- `static/js/saludbot.js:613-627` — captura y conversión a base64.
- Django file uploads: https://docs.djangoproject.com/en/5.2/topics/http/file-uploads/
- `DATA_UPLOAD_MAX_MEMORY_SIZE`: https://docs.djangoproject.com/en/5.2/ref/settings/#data-upload-max-memory-size
