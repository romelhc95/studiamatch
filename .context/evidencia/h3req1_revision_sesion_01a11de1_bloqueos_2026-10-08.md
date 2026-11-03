# Revisión de sesión 01a11de1 — causa pendiente de identidad y acceso CI

Sesión: `01a11de1-1403-7133-b10e-6fd9f8543905`. Fecha del análisis: 2026-10-08.
El cierre del registro ocurrió 2026-10-09 00:02:27 UTC. Autoridad:
[estado vivo](../estado_del_proyecto.md) y [AGENTS](../../AGENTS.md).
Contraste: [resultado del ciclo aprobado](h3req1_cierre_local_iterativo_2026-10-08.md),
[F2d](h3req1_c03_f1_daemon_diagnostic_f2d_2026-10-08.md) y fuentes actuales del helper.

## Alcance de esta revisión

Solo lectura de registro, evidencia y código; adición documental solicitada por análisis
de avance. Dominio DOC/K14, consumidores estado/traspaso. Ningún contrato/runtime/SQL cambió,
ninguna conexión Docker ni lectura remota fue ejecutada. Preservar todos los resultados y
aprobaciones históricas; esta nota no autoriza reintentar F2d. Rollback solo de adiciones
documentales. No acredita pilares/runtime por prosa ni sustituye revisión independiente.

## Hechos nuevos localizados en el registro

La invocación F2d de 2026-10-08 23:44:06.049 UTC usó `tools.exec_command` sin parámetro
`sandbox_permissions: require_escalated`. El usuario sí había aprobado el alcance, pero
el registro de esa llamada no muestra solicitud explícita de ejecución fuera del sandbox.
Esto difiere de la ejecución BFF r2, cuyo acceso elevado sí formaba parte de la operación
documentada tras el rechazo del socket en r1.

El helper `tests/h3req1_c03_docker_daemon_identity_f2d.py` ejecuta en un mismo bloque try:
creación de socket Unix, connect, getsockopt SO_PEERCRED y unpack. Captura conjuntamente
OSError/struct.error y emite `direct-peer-credentials-unavailable`, descartando el punto
de fallo y errno. El resultado no distingue permiso denegado, restricción de ejecución,
conexión fallida ni interfaz de credenciales no disponible.

No se ha demostrado cuál de esas causas ocurrió. La falta de escalación explícita es
evidencia del modo solicitado, no prueba definitiva del motivo. No concluir daemon remoto,
proxy, engine inválido o necesidad de reinstalar Docker a partir de ese resultado.

## Qué ocurrió y qué no avanzó

La aprobación consolidada llegó; no es ya un bloqueo genérico de "falta aprobar el paquete".
F2d falló y el paquete exigía detener todas las fases Docker dependientes. No hubo r9,
snapshot, arranque, C03 integrado, SQL ni pruebas de aplicación nuevas. GitHub read-only
devolvió 403 de branch protection: el conector no acreditó required checks/reviews.
Una nueva revisión estática 51/51 no resuelve esas dos dependencias.

G01–G02 conservados, G03–G10 abiertos: 20% -> 20%, sin gate completo nuevo. La sesión
produjo evidencia de fallo y límite de acceso, no avance de validación de aplicación.
Cambiar el porcentaje para reflejar trabajo documental ocultaría la detención real.

## Corrección de rumbo necesaria

1. Preparar una revisión diagnóstica mínima del helper que separe socket/connect/getsockopt/
   unpack y conserve códigos allowlisted de fase/errno, sin paths crudos, Env, secretos ni
   inspect completo. Pruebas sintéticas de cada error por fase; revisión previa.
2. Presentar una autorización nueva y concreta para ese diagnóstico con acceso elevado del
   entorno solicitado explícitamente. Una ejecución acotada, sin Docker API y sin instalar/
   cambiar el motor durante esa prueba. El F2d anterior está consumido y se preserva.
3. Si se demuestra identidad, habilitar las etapas locales del paquete actualizado;
   primero r9 con preflight permisos/UID/ancestros/mounts, luego copia/smoke/C03.
   Si el sistema realmente no expone identidad, presentar alternativa local específica con
   alcance y aprobación, usando la causa demostrada; no ensayar métodos equivalentes a ciegas.
4. CI en paralelo: usar una identidad existente con lectura administrativa suficiente del
   mismo repo, sin mostrar token, o evidencia administrativa sanitizada desde GitHub. No
   pedir permisos amplios de escritura para resolver una lectura 403. Si falta control,
   concretar bootstrap/patch/rollback y review humano antes de cambios protegidos.

El paquete consolidado previo fue insuficiente para estas alternativas: autorizaba F2d
exacto y excluía continuar al fallar identidad; C era lectura sin garantizar permisos del
conector. Ese comportamiento explica la parada y debe corregirse expresamente. Ninguna
nota nueva debe prometer GO con una aprobación si los accesos externos siguen sin resolver.

No hace falta otro levantamiento completo ni repetir scans intactos. Hace falta diagnóstico
accionable del error de sistema y acceso real a la configuración CI. Esta revisión no
modifica permisos, ejecuta el nuevo diagnóstico ni suma puntos al tablero.
