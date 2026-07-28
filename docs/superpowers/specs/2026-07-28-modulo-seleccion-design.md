# Módulo de selección: etapas del selector y del comunicador — Diseño

Fecha: 2026-07-28
Relacionado: `docs/arquitectura-modulo-gestion.md`,
`docs/superpowers/specs/2026-07-27-login-google-perfiles-design.md`

> Documento para validar con el equipo antes de escribir código. Las secciones
> "Qué hace el sistema" están escritas para el equipo de salud; las de "Modelo
> de datos" y "Verificación", para quien lo implemente.

## Objetivo

Que las solicitudes que hoy crea el chatbot dejen de ser una lista muerta en la
base de datos y pasen por un flujo de trabajo con dos etapas y un responsable
en cada una: un **selector**, que es profesional clínico y decide si la
solicitud procede, y un **comunicador**, que contacta al paciente y registra el
resultado.

## Nombre del módulo

El equipo lo llama **módulo de selección** y se accede por
`seleccion.cmvalparaiso.cl`. En el código la app se llama `gestion`, nombre que
**no se cambia**: renombrarla implica renombrar tablas y reescribir migraciones
ya aplicadas en producción, sin ganancia funcional. En este documento, "módulo
de selección" y "app `gestion`" son lo mismo.

## Alcance

**Dentro de alcance:**

- Modelo `Gestion` con el ciclo de vida completo de una solicitud.
- Catálogo editable de motivos de rechazo, con el mensaje que recibe el paciente.
- Pantalla de cola del selector, con las tres decisiones.
- Pantalla de tabla del comunicador, con registro de contacto y enlace de WhatsApp.
- Cierre automático de los rechazados a las 24 horas.
- Filtrado por centro y por rol en todas las consultas.

**Fuera de alcance:**

- Ventana horaria del chatbot (L-V 08:00–08:20). Es trabajo del chatbot.
- Reportes, estadísticas y tableros.
- Administración de cupos o agenda propia.
- UI de gestión de perfiles para el rol `SOME`; sigue siendo el admin de Django.
- Integración con la API de WhatsApp. Acá solo hay enlaces `wa.me`.

## Las dos prioridades

El sistema maneja dos prioridades distintas que **comparten la misma escala**
(`URGENTE`, `ALTA`, `MEDIA`, `BAJA`) y no se sobrescriben entre sí. Es la
confusión más probable al leer este documento, así que conviene fijarla primero:

| | Prioridad administrativa | Prioridad clínica |
| --- | --- | --- |
| Quién la asigna | El chatbot, automáticamente | El selector, a mano |
| Con qué criterio | Palabras clave del motivo, edad, condiciones declaradas (`solicitudes/priorizacion.py`) | Criterio profesional del selector |
| Para qué sirve | Ordenar la cola del **selector** | Ordenar la tabla del **comunicador** |
| Cuándo existe | Desde que se crea la solicitud | Solo si el selector acepta |

Ambas quedan guardadas. Con el tiempo, comparar una con otra permite medir qué
tan bien acierta el cálculo automático y calibrarlo con datos reales.

## Ciclo de vida de una solicitud

```
        chatbot
           │
           ▼
       PENDIENTE ───────────────── cola del SELECTOR
           │                       orden: prioridad administrativa, luego mas antigua
           │
    ┌──────┼──────────────┐
    ▼      ▼              ▼
ACEPTADA  RECHAZADA    NO_APLICA
    │      │              │
    │      │              └──► fin del flujo. No llega al comunicador.
    │      │                   Se conserva para conteo, no se borra.
    │      │
    └──────┴───────────────── tabla del COMUNICADOR
           │                  orden: aceptadas primero por prioridad clinica,
           │                         rechazadas al final
           ▼
        CIERRE
   (no cambia la decision: una rechazada
    cerrada sigue siendo una rechazada)
```

`decision` (la decisión del selector) y el cierre son **dos datos separados**.
Una solicitud rechazada que igual recibe citación conserva su rechazo y su
motivo, y además guarda la fecha y hora de la cita. Con un único campo de
estado ese caso sería imposible de representar.

## Etapa 1 — El selector

Ve una cola con las solicitudes **pendientes de su centro**, ordenadas por
prioridad administrativa (urgente primero) y, dentro de cada nivel, la más
antigua primero. Al abrir una solicitud ve los datos del paciente y lo que
escribió en el chat, y toma una de tres decisiones:

**Aceptar.** Registra la **prioridad clínica** con su criterio profesional. La
solicitud avanza al comunicador.

**Rechazar.** Elige un **motivo del catálogo**. La solicitud avanza igual al
comunicador, porque al paciente hay que avisarle.

**No aplica.** Pruebas del sistema o personas simulando. La solicitud sale del
flujo y no llega al comunicador. No se borra: queda contable.

### Corrección de una decisión

Cualquier selector del centro puede cambiar una decisión ya tomada **mientras
el comunicador no haya registrado ningún intento sobre ese caso**. Después
queda bloqueada. Cada cambio guarda quién y cuándo.

La regla equilibra dos riesgos reales: que un error de clic deje un caso mal
clasificado para siempre, y que un caso que ya se conversó con el paciente
cambie de estado por debajo del comunicador.

## Etapa 2 — El comunicador

Ve **una sola tabla** con todo lo que le llegó, en este orden:

1. Las **aceptadas**, de `URGENTE` a `BAJA` según prioridad clínica.
2. Las **rechazadas**, al final.

Cada fila muestra nombre, teléfono, prioridad, cantidad de intentos y fecha del
último; en las rechazadas, además, el motivo del rechazo. Las aceptadas son la
prioridad real de su trabajo: se contactan **por teléfono** para ofrecer la
citación. Los casos cerrados salen de la tabla.

Sobre cada caso puede registrar:

| Acción | Qué pide | Efecto |
| --- | --- | --- |
| Agendada | fecha y hora acordadas | cierra el caso |
| El paciente no acepta la citación | nada | cierra el caso |
| No contesta | nada | suma un intento, el caso sigue abierto |
| No se logró contactar | nada | cierra el caso, dándolo por agotado |
| Clic en el enlace de WhatsApp | nada | suma un intento, **no** cierra |

"No acepta" es el paciente rechazando la hora ofrecida, y no tiene relación con
que el selector haya rechazado la solicitud.

**Los aceptados no se cierran solos nunca.** Requieren gestión real hasta que
alguien registre un desenlace.

### El enlace de WhatsApp

Los rechazados no son urgentes, pero el paciente está en su casa sin saber que
su solicitud no procedió. Llamarlos uno por uno es trabajo que compite con los
casos aceptados, que sí son prioritarios.

La solución es un botón que abre WhatsApp Web con el chat del paciente y un
**mensaje ya escrito**, tomado del motivo de rechazo. El comunicador solo
revisa y envía. El backend arma la URL `https://wa.me/<telefono>?text=<mensaje>`;
el teléfono ya se guarda con código de país.

El clic **registra un intento, no un contacto**. Abrir una ventana no prueba
que el mensaje se haya enviado ni que el paciente lo haya leído. Lo que sí
resuelve es que el comunicador sepa a quién ya le escribió sin tener que
acordarse.

El botón aparece también en los casos aceptados, como respaldo cuando no
contestan el teléfono. El flujo esperado ahí sigue siendo la llamada.

### Cierre automático de los rechazados

Un rechazado se cierra solo **24 horas después de haber sido rechazado** —el
reloj corre desde `fecha_decision`—, sin intervención del comunicador. Evita que la tabla acumule casos que ya no
requieren acción y que el comunicador tenga que cerrarlos a mano uno por uno.

El cierre guarda **por qué** se cerró, y esa distinción es lo que hace útil al
dato:

- **`AVISADO_WHATSAPP`** — se usó el enlace. El paciente probablemente se enteró.
- **`SIN_AVISO`** — nunca se abrió el enlace ni se registró contacto. **Este
  paciente no supo que su solicitud fue rechazada.**

Contar los `SIN_AVISO` mide un problema real de servicio. Si el cierre fuera un
único estado "cerrado", ese número sería imposible de obtener.

El reloj corre en `America/Santiago`, la zona ya configurada en el proyecto.

## Roles y permisos

Se derivan del rol del `PerfilUsuario`, definido en la spec del login. No hay
permisos por pantalla ni por usuario.

| Rol | Cola del selector | Tabla del comunicador | Casos `NO_APLICA` |
| --- | --- | --- | --- |
| `SELECTOR` | decide | — | ve los de su centro |
| `COMUNICADOR` | — | registra contacto | — |
| `FULL` | decide | registra contacto | ve los de su centro |
| `SOME` | decide | registra contacto | ve los de su centro |
| `SUPERVISOR_CENTRO` | solo lectura | solo lectura | ve los de su centro |
| `SUPERVISOR_DAS` | solo lectura | solo lectura | ve todos |
| `ADMIN` | solo lectura | solo lectura | ve todos |

Toda consulta se filtra además por los centros del perfil (`centro` y
`centro_satelite`), usando el helper `centros_permitidos()` que ya existe.
`ADMIN` y `SUPERVISOR_DAS` ven todos los centros.

Un usuario que intente abrir un caso fuera de su alcance recibe **404**, no un
error de permisos: no se confirma siquiera que el caso existe.

## Modelo de datos

Una tabla nueva con relación uno a uno a `Solicitud`. **El chatbot no se
toca**: `solicitudes` sigue siendo la única app que crea `Solicitud`, y todo el
ciclo administrativo vive en `gestion`.

```
Gestion  (tabla gestion_solicitud)
├── solicitud              OneToOne → solicitudes.Solicitud, CASCADE
│   ── etapa del selector ──
├── decision               PENDIENTE | ACEPTADA | RECHAZADA | NO_APLICA
├── prioridad_clinica      URGENTE | ALTA | MEDIA | BAJA   (vacio salvo ACEPTADA)
├── motivo_rechazo         FK → MotivoRechazo, RESTRICT    (nulo salvo RECHAZADA)
├── decidido_por           FK → auth.User, SET_NULL
├── fecha_decision         DateTime, nulo
│   ── etapa del comunicador ──
├── fecha_hora_citacion    DateTime, nulo    (solo si el cierre es AGENDADA)
├── intentos_contacto      entero, default 0
├── fecha_ultimo_intento   DateTime, nulo
├── aviso_whatsapp_en      DateTime, nulo    (primer clic al enlace)
├── contactado_por         FK → auth.User, SET_NULL
│   ── cierre ──
├── cerrada_en             DateTime, nulo
└── motivo_cierre          AGENDADA | NO_ACEPTA | NO_CONTACTADO
                           | AVISADO_WHATSAPP | SIN_AVISO
```

```
MotivoRechazo  (tabla gestion_motivo_rechazo)
├── nombre              lo que ve el selector en el select
├── mensaje_paciente    texto que se envia por WhatsApp; admite {nombre}
├── activo              desactivar sin romper el historial
└── orden               posicion en el select
```

Notas de modelado:

- **No existe un campo `resultado_contacto`.** "No contesta" no es un estado
  que persista: incrementa el contador y deja el caso abierto. Los desenlaces
  que sí persisten son exactamente los valores de `motivo_cierre`. Un campo
  aparte duplicaría esa información y permitiría que las dos versiones se
  contradijeran.
- **El mensaje al paciente vive en el motivo, no en el código.** Ajustar la
  redacción después del piloto es editar una fila, no desplegar. Usa `{nombre}`,
  el campo del paciente agregado en el PR #10.
- **Un `MotivoRechazo` no se borra**, se desactiva: hay solicitudes apuntando a
  él (de ahí el `RESTRICT`).
- **Índices** para las dos consultas de las colas: por `decision` y por
  `cerrada_en`, ambos combinados con el centro de la solicitud.
- **Orden de `prioridad_clinica`**: alfabéticamente daría *alta, baja, media,
  urgente*. El orden correcto se resuelve una sola vez en un método del
  queryset, no en cada vista.

### Cómo entra una solicitud al módulo

Al crearse una `Solicitud`, se crea su fila de `Gestion` en `PENDIENTE`
mediante una señal `post_save` que vive **en la app `gestion`**. Es el único
punto de integración y va en una sola dirección: el código del chatbot no
cambia.

Se descartó la alternativa de no crear fila hasta que el selector decida (la
cola serían las solicitudes sin fila asociada). Evita la señal, pero obliga a
un `LEFT JOIN` en cada consulta y deja sin lugar donde registrar cualquier dato
previo a la decisión.

## Implementación del cierre a 24 horas

Enfoque híbrido, en dos capas:

1. **La tabla del comunicador filtra en vivo** por la regla de las 24 horas. La
   vista del operador es correcta aunque no corra ningún proceso.
2. **Un comando `manage.py cerrar_rechazados`**, programado por cron cada hora,
   materializa el cierre: escribe `cerrada_en` y `motivo_cierre`.

Si el cron se detiene, la operación no se ve afectada; solo se atrasa el dato
histórico. Se descartaron las dos versiones puras: solo el filtro en vivo deja
el cierre sin fecha real y obliga a recalcular la regla en cada reporte; solo
el cron hace que una caída silenciosa le muestre casos vencidos al comunicador.

## Casos borde resueltos

- **Solicitudes anteriores al despliegue.** No tienen fila de `Gestion`. La
  migración las crea en `PENDIENTE`, de modo que el selector encontrará la cola
  cargada con el histórico el primer día. **Si el equipo prefiere partir de
  cero, se crean como `NO_APLICA`; hay que decidirlo antes de desplegar.**
- **Teléfono inválido o vacío.** No se arma el enlace de WhatsApp y la fila lo
  indica. El caso se sigue gestionando por teléfono.
- **Un rechazado que se cierra solo mientras el comunicador lo tenía abierto.**
  Al guardar recibe un aviso de que el caso ya se había cerrado, y su registro
  se aplica igual. No se pierde trabajo.
- **Doble envío** al registrar un resultado: la acción es idempotente, no suma
  dos intentos.
- **Dos selectores sobre el mismo caso.** No hay bloqueo: gana el último en
  guardar y queda registro de ambos. Formalizar un bloqueo sería
  sobre-ingeniería para el volumen actual.

## Verificación

Con el test runner de Django contra MySQL, como el resto del proyecto.

- Transiciones inválidas: aceptar sin prioridad clínica, rechazar sin motivo,
  decidir una solicitud de otro centro.
- La corrección se bloquea una vez que el comunicador registró un intento.
- Orden de las dos colas, incluido que `prioridad_clinica` no se ordene
  alfabéticamente.
- Filtrado por centro y por rol: que un `SELECTOR` no alcance la pantalla del
  comunicador y viceversa, y que un supervisor no pueda escribir.
- Cierre a 24 horas, con sus dos motivos, controlando el reloj en el test.
- Armado del enlace `wa.me` con el teléfono normalizado y el `{nombre}`
  reemplazado.
- La señal crea exactamente una fila de `Gestion` por solicitud.

No automatizable: que WhatsApp Web abra el chat correcto en el equipo del
comunicador.

## Decisiones que faltan confirmar con el equipo

Ninguna bloquea el diseño; todas tienen un valor propuesto. Conviene cerrarlas
en la reunión de validación.

**1. La lista inicial de motivos de rechazo.** Propuesta de partida, a corregir
por el equipo clínico:

| Motivo | Mensaje al paciente (borrador) |
| --- | --- |
| No corresponde a morbilidad | Hola {nombre}, su solicitud no corresponde a atención de morbilidad. Para controles o enfermedades crónicas debe agendar por el canal habitual de su centro. |
| Requiere atención de urgencia | Hola {nombre}, por lo que describe necesita atención inmediata. Acuda al SAPU o servicio de urgencia más cercano. |
| No pertenece al centro | Hola {nombre}, no figura inscrito/a en el centro indicado. Contacte al centro donde está inscrito/a. |
| Datos insuficientes | Hola {nombre}, su solicitud no incluye información suficiente para evaluarla. Puede volver a ingresarla detallando su motivo de consulta. |
| Sin cupos disponibles | Hola {nombre}, no quedan cupos disponibles para hoy. Puede volver a solicitar atención mañana. |
| Solicitud duplicada | Hola {nombre}, ya recibimos una solicitud suya para esta fecha y está siendo gestionada. |

**2. Qué hacer con el histórico** de solicitudes al desplegar: cargarlas como
`PENDIENTE` (propuesto) o descartarlas como `NO_APLICA`.

**3. Si 24 horas es el plazo correcto** para el cierre automático de rechazados,
o el equipo prefiere otro.

## Referencias

- `solicitudes/models.py` — modelo `Solicitud`, dueño de los datos del paciente.
- `solicitudes/priorizacion.py` — cálculo de la prioridad administrativa.
- `gestion/models.py` — `PerfilUsuario`, roles y `centros_permitidos()`.
- `docs/superpowers/specs/2026-07-27-login-google-perfiles-design.md` — roles y alcance por centro.
- `docs/arquitectura-modulo-gestion.md` — decisión de un solo proyecto y routing por subdominio.
