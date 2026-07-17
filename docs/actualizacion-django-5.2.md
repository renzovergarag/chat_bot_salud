# Actualización de Django 5.0.8 a 5.2.8 (LTS)

## Resumen

Se actualizó Django de `5.0.8` a `5.2.8` (LTS) en `requirements.txt`. El
cambio es requisito para poder desplegar el proyecto en el servidor de
producción.

## Motivo

El servidor de producción corre **Ubuntu 26.04**, cuyo único intérprete
disponible es **Python 3.14** (no hay Python 3.10–3.13 en los repositorios
ni está instalado pyenv). Django 5.0 soporta oficialmente solo Python
3.10–3.12, por lo que **no puede ejecutarse sobre Python 3.14**.

La solución es subir Django a una versión compatible con 3.14, en lugar de
instalar un intérprete más antiguo (opción no viable en ese servidor).

## Por qué 5.2 LTS y no 6.0

| Versión        | Python soportado | Sirve en producción (3.14) | Sirve en local (3.11) |
| -------------- | ---------------- | -------------------------- | --------------------- |
| 5.0.8 (previa) | 3.10 – 3.12      | No                         | Sí                    |
| **5.2.8 (LTS)**| **3.10 – 3.14**  | **Sí**                     | **Sí**                |
| 6.0.7          | 3.12 – 3.14      | Sí                         | No (dropea 3.11)      |

Se eligió **5.2.8 LTS** porque:

- Cubre producción (3.14) y el entorno de desarrollo local (3.11) con el
  mismo pin, sin obligar a cambiar el Python de las máquinas de desarrollo.
- Es una versión **LTS**, con soporte extendido.
- Es un salto menor desde 5.0 (menos riesgo de cambios incompatibles que 6.0).

## Verificación realizada

El upgrade se probó en local (Python 3.11) contra MySQL 8.4 en Docker antes
de aplicarlo:

- `python manage.py check` — sin issues.
- Suite de tests: **9/9 OK**.
- `python manage.py makemigrations --check --dry-run` — **sin migraciones
  nuevas** por el cambio de versión.
- Flujo end-to-end del chatbot (`POST /api/solicitudes/`) — solicitud creada
  y persistida correctamente en la base de datos.

## Impacto

- No requiere cambios de código ni migraciones de base de datos.
- Compatible con el entorno de desarrollo local (Python 3.11) y con el de
  producción (Python 3.14).

## Referencias

- Django 5.2 release notes: https://docs.djangoproject.com/en/5.2/releases/5.2/
- Django deprecation timeline: https://docs.djangoproject.com/en/5.2/internals/deprecation/
