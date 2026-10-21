# H3REQ1: Development existente y cierre del candidato ajustado

Fecha: 2026-10-08. Sesión analizada: `01a11de1-1403-7133-b10e-6fd9f8543905`,
incluida su continuación local `01a11e41-806e-7581-8bd0-d84b4fb32956`.
Autoridad: [estado vigente](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md)
y [tablero](../operaciones/h3req1_avance_por_gates_y_prompt_luna_2026-10-08.md).

## Ficha de impacto y límites

Objetivo: explicar qué ya estaba desplegado/probado y qué falta después de los ajustes.
Dominio DOC/K14; consumidores: responsable, estado y siguiente ejecutor.
Cambio solo documental: esta nota y su enlace en el índice. Sin cambio de contratos,
SQL, código, recursos ni permisos. Preservar ambos checkouts, WIP, evidencia y JIT
consumidos. Transición funcional existente expand -> compatibilidad -> deploy -> contract
no ejecutada por esta revisión. Rollback: retirar únicamente estas adiciones documentales.
Pilares: claridad y mantenimiento de evidencia; sin mediciones nuevas de runtime,
seguridad global, rendimiento o escalabilidad. No se ejecutaron suites ni consultas remotas.

Candidato confirmado: `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. El WIP adicional no se identifica solo con HEAD.

## Lo anterior sí existe; no debe tratarse como trabajo desde cero

El [corte histórico del estado](../estado_del_proyecto.md) registra PR #500 mergeado,
`desarrollo@4eb4d877a50b012bb630a129bd0c74482c33be9c` y checks consultados verdes.
Es evidencia histórica, no una nueva consulta del despliegue o rama remota.

El registro del 2026-09-27 acredita login, MFA (doble factor de autenticación),
challenge/verify HTTP 200 y operaciones protegidas de cola HTTP 200.
También registra la invitación real Admin: Edge v9, POST 200, cuenta invitada,
correo enviado y auditoría sin duplicados. Ese envío no acredita aceptación del enlace,
onboarding completo ni toda la matriz remota. Las notas de septiembre todavía
declaraban pendientes de aceptación global. No equivale a que H3REQ1 no estuviera implementado.

La [atestación de octubre](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md)
introdujo ajustes posteriores: completar/corregir campos editoriales y conservar
ownership/auditoría, disponibilidad con evidencia vigente de máximo 90 días,
correo visible en encabezado y traslado de sesión/operaciones Admin al BFF.
BFF significa servidor intermedio para el frontend. La cookie HttpOnly impide que
JavaScript del navegador lea la sesión. Se conservan roles y MFA existentes.
La transición aceptada exige limpiar sesión antigua y volver a iniciar sesión con
la misma cuenta; no resetearla ni reinvitarla.

El cierre de ese transporte incorpora pruebas de gateway firmado, cuotas y
suspensión/recuperación. Un cambio de encabezado no reabre todo Auth; cambiar el
transporte de sesión sí requiere comprobar que acceso, renovación, cierre de sesión,
MFA e invitación siguen funcionando por la nueva ruta.

| Dimensión | Evidencia preservada | Qué falta para este candidato |
|---|---|---|
| Implementación e integración anteriores | PR #500 y baseline desarrollo históricos | Inventario completo del WIP posterior; integración protegida del delta |
| Pruebas remotas anteriores | Login/MFA/operación sensible; invitación enviada | No regresión y transición al BFF; aceptación del nuevo artefacto |
| SQL/gateway/cuotas locales | C02 v4 SQL/wire histórico aplicable | Validar deltas BFF/workflow; no repetir SQL intacto sin causa |
| Suspensión SQL local | C03 SQL v3, 41/41 inputs en la última revalidación | Ensayo integrado con Pages, Edge, PG17 y PostgREST |
| Pruebas locales parciales | Pytest focal 20/20, scanner r7, BFF r2 60 checks/10 casos | Tooling y checks finales, UAT visual final y revisión |
| Despliegue del candidato nuevo | No acreditado por este corte | SHA integrado, host y versiones/configuración identificados antes de D01–D14 |

La [revalidación](h3req1_revalidacion_hashes_2026-10-08.md) terminó en C02 70/72
por cambios BFF/workflow; no afirmar 72/72 actual. Se conserva su alcance SQL/wire
intacto; los dos deltas requieren cobertura propia. C03 SQL 41/41 no demuestra
por sí mismo el ensayo integrado.

## Qué explica el estancamiento de la sesión

1. El diagnóstico inicial requería identificar directamente el proceso del motor
   Docker desde Linux. El entorno confirmado es Docker Desktop Windows con integración
   WSL (subsistema de Linux de Windows). Ese requisito no era adecuado al entorno
   confirmado: Ubuntu no expone directamente el proceso del motor de la distro interna.
   Esto explica la incompatibilidad del método; no identifica todos los errores previos
   ni la discrepancia exacta de los controles F1.
2. La ejecución elevada registró `peer-identity/EACCES`. Después el usuario ejecutó
   el runner antiguo de administrador y obtuvo `IDENTITY_MISMATCH`. No se debe repetir
   ninguno de esos métodos consumidos ni recomendar más sudo como solución.
3. La alternativa WSL fue aprobada y ejecutada, pero el bloque terminaba en `exec`:
   reemplazó la shell y pudo cerrar la terminal. El runner no persistió resultados.
   El usuario no recuperó salida; no puede deducirse éxito ni fallo de Docker/F1.
4. Existe una [solicitud pendiente con captura y pausa](../operaciones/jit_h3req1_docker_desktop_wsl_output_capture_once_2026-10-08.md).
   Es una repetición acotada de lecturas, no una reconstrucción. Necesita aprobación
   nueva porque la anterior ya se invocó. Sus resultados deben conservarse como
   evidencia sanitizada en cuanto se reciban; leer F1 correctamente no equivale a
   que sus controles hayan pasado.
5. El control independiente de CI (integración continua: checks automáticos de cambios)
   sigue sin instalar y demostrar enforcement. El patch V3 está preparado, no operativo.
   El control actual security-audit y la revisión humana existen; la brecha es proteger
   el propio workflow requerido frente a modificaciones en el cambio que evalúa.
   Resolverlo exige operaciones protegidas separadas; no es un nuevo requisito de negocio.
   Pages tiene main con despliegue automático: preparar aislamiento de CI antes de
   publicar/promocionar bootstrap para evitar un despliegue de producto incidental.

No hay evidencia que justifique reinstalar Docker, borrar todos los contenedores o
rehacer H3REQ1. Un fixture nuevo aislado permite validar sin alterar recursos históricos.
Si se demuestra que falta una imagen/dependencia o es necesaria limpieza, presentar
lista exacta y aprobación por objetivo antes de pull, rebuild o eliminación.

## Porcentaje y siguiente secuencia

La métrica actual usa diez gates con peso igual, diez puntos cada uno. Es porcentaje
de controles de cierre completos del candidato actualizado, no de producto implementado,
tiempo transcurrido ni esfuerzo restante. Mantener denominador para comparar sesiones.

| Gates | Puntos actuales | Pendiente |
|---|---:|---|
| G01 SQL/wire; G02 suspensión SQL | 20/20 | Preservar alcance aplicable |
| G03 tooling; G04 diagnóstico suficiente/F1 | 0/20 | Captura WSL y disposición F1; completar tooling/revisión |
| G05 copia; G06 arranque; G07 integración | 0/30 | Snapshot completo -> healthz real -> C03 integrado |
| G08 checks/revisión; G09 aceptación final | 0/20 | Candidato exacto, UAT visual 144 y onboarding 10, cliente/pilares |
| G10 CI efectivo/paquete PR/review | 0/10 | Bootstrap protegido, evidencia real y revisión humana |
| Total | **20/100; delta 0** | Ocho controles completos abiertos con parciales conservados |

D01–D14 0/14 se refiere al artefacto nuevo de este ciclo. No borra pruebas remotas
anteriores. No existe aquí inventario suficiente para calcular porcentaje de implementación
total del producto; inventarlo sería engañoso.

La siguiente acción manual ya concreta es aprobar el JIT de captura vigente y ejecutar
su bloque exacto en Ubuntu WSL como romel, sin sudo, desde terminal interactiva;
compartir solo las líneas sanitizadas antes de salir de la pausa. Si el ejecutor automatizado
puede hacerlo bajo el mismo alcance, no delegar innecesariamente al usuario; el paquete
actual define al usuario y terminal interactiva, por lo que no cambiarlo implícitamente.
Tras los resultados exigidos, seguir r9 y etapas no consumidas del paquete consolidado;
no solicitar otra aprobación por cada comando que ya está dentro de ese alcance.

Cerrar tooling y corregir la discrepancia F1 demostrada. Luego probar copia, arranque
y ensayo integrado por etapas: si falla el arranque, corregir solo ese arranque antes
de añadir DB/Edge. Completar checks/UAT y aceptación del candidato. Preparar CI en
trabajo independiente de esos resultados locales, con autorización protegida separada.
Tras GO_LOCAL_PR e instrucciones de integración/despliegue, probar Development.
GO_LOCAL_PR no es GO_DEVELOPMENT_REAL. Certification/Production de producto quedan fuera.

## Prompt actualizado para Luna 6 Max

```text
continua H3REQ1 en esta misma sesión; si se abre una nueva, recupera estado y
autorizaciones desde evidencia explícita. Objetivo: cerrar el candidato ajustado
hasta GO_LOCAL_PR y preparar su integración/despliegue Development, sin rehacer
H3REQ1 anterior ni declarar GO sin resultados.

Candidato /home/romel/src/studiamatch-h3req1-sync-20261002,
feat/h3req1-sync-20261002, HEAD baseline
4eb4d877a50b012bb630a129bd0c74482c33be9c. Preserva todo WIP y el checkout original
/home/romel/src/studiamatch. No inspecciones .deno excluido ni valores de .env/secretos.

Lee AGENTS aplicables, encabezado vigente de .context/estado_del_proyecto.md,
.context/indice.md, protocolo constructor y esta nota:
.context/evidencia/h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md.
Usa plan_cierre_integral_h3req1_2026-10-04.md y tablero de avance como referencias,
y los paquetes vigentes solo para las dependencias actuales. Empieza con tareas,
gates, rama/HEAD/WIP y ficha de impacto. No hagas otro levantamiento general.

CONSERVA: implementación remota anterior, PR #500/baseline histórico, Auth+MFA
real y cuenta existente; C02 SQL/wire aplicable, C03 SQL v3; pruebas parciales.
Los ajustes posteriores cambian transporte de sesión mediante BFF/HttpOnly,
gateway/cuotas y recuperación. Comprueba sus efectos, no reinicies cuentas ni
repitas onboarding de la cuenta existente. Onboarding tiene escenario separado.
No afirmes C02 72/72: última comparación 70/72 por BFF/workflow; SQL intacto se
conserva y ambos deltas se validan específicamente. Revalida inputs si hay delta.

BLOQUEO ACTUAL: Docker Desktop Windows + WSL integration. No vuelvas a exigir
/proc del motor dentro de Ubuntu, más sudo, reinstalación ni runners consumidos.
La alternativa WSL se ejecutó, pero exec cerró la terminal y se perdió stdout.
No inventes resultado. La solicitud pendiente está en
.context/operaciones/jit_h3req1_docker_desktop_wsl_output_capture_once_2026-10-08.md,
ID H3REQ1-C03-DOCKER-DESKTOP-WSL-OUTPUT-CAPTURE-ONCE-20261008-V1,
SHA bbaa2242bf026f252864b4e476a60e9de2a8e327c0456d2b343b612402c61c92.
Comprueba estado y pin antes de solicitarla: esta nota no la aprueba.
No cambies el bloque fijado ni vuelvas a aprobar una invocación consumida.
Explica al usuario en lenguaje simple la única acción manual del paquete:
terminal Ubuntu WSL como romel, sin sudo, bloque exacto con pausa, copiar solo
phase/error_code. Al recibir salida, consérvala sanitizada en evidencia local.
Si falla, explica fase y causa demostrada; corrige el método o componente antes
de solicitar un ensayo nuevo. No ocultes errores, aumentes retries o borres checks.

Solo con resultados exigidos habilita r9 y etapas A/B no consumidas del paquete
consolidado autorizado, con límites existentes. Lectura F1 OK no es controles
F1 PASS: registra campos discrepantes y demuestra su corrección. No pidas permisos
por cada comando ya autorizado; método nuevo, cambio de alcance o recurso fuera
del paquete requiere JIT separado por objetivo concreto.

Ejecuta ciclos analizar -> corregir -> validar -> revisar -> tareas -> revalidar.
Primero tooling completo; luego snapshot íntegro sin secretos/dependencias
históricas, smoke Pages/workerd hasta healthz, luego C03 integrado real con Edge,
PG17 desechable y PostgREST. No avanzar tras FAIL; diagnostica la fase fallida.
No recrees imágenes ni elimines recursos por intuición: si es necesario, presenta
inventario exacto, pins, efecto, recuperación y autorización antes de hacerlo.

Sobre el candidato exacto: checks pertinentes en Docker, regresiones afectadas,
scanner, scope, build normal/mock, revisión independiente, UAT visual vigente
48 casos x 3 viewports = 144 ejecuciones/capturas sin retries y onboarding 10/10.
Renueva pruebas según inputs/contratos. Cierra aceptación cliente y seis pilares,
documenta límites/owners, compatibilidad y rollback. No conviertas seguimiento
braces/priceMin en waiver ni inventes disposición de skips/warnings.

Prepara CI independiente desde base confiable usando paquete bootstrap vigente
y patch V3; no repidas capturas GitHub ya acreditadas. Falta evidencia real de
check requerido sobre SHA y revisión humana. Antes de operaciones protegidas,
presenta paquete completo de bootstrap con PR/ramas, checks, límites/rollback y
efecto Pages: main tiene despliegue automático. No des por probado el mecanismo
CF-Pages-Skip ni dispares producción incidentalmente. Solicita instrucción
humana separada para push/PR/merge/configuración; continua no la sustituye.

Mantén total 20% como controles de cierre acreditados, no implementación de H3.
Reporta puntos solo al completar gates G01–G10; muestra también parciales sin
inflar porcentaje. Cada cierre entrega resultado/evidencia, permiso consumido,
delta porcentual y siguiente gate. No termina en otro prompt si una ejecución
ya autorizada puede realizarse. Si falta aprobación, prepara todo lo independiente
y espera hasta 30 minutos en intervalos que permitan comunicar/recibir respuesta;
el silencio no es autorización. Tras esa ventana deja solicitud pendiente.

GO_LOCAL_PR requiere sus diez gates; después, solo con instrucciones separadas,
integración protegida y despliegue Development Free aqrldlmlszjtgpqiegaa, versiones
y hostname aprobados, transición compatible sin activar gateway antes del BFF,
y D01–D14 sobre el artefacto nuevo. Pro xwhtiqmboljkshrtviyw sigue baseline;
no modificar Pro ni datos operativos. GO_DEVELOPMENT_REAL exige aceptación real.
No prometas GO mediante una aprobación ilimitada ni rebajes controles para darlo.
```

## Verificación de esta revisión

Lectura de los dos registros de la sesión, estado vigente, atestación, tablero,
revalidación de inputs y JIT pendiente. Sin ejecución Docker, SQL, Git remoto,
instalación ni modificaciones de producto. Revisión documental de enlaces y
`git diff --check`; esto no suma puntos ni acredita ejecución del proyecto.

## Aclaración solicitada: origen BFF y ruta para los cuatro ajustes

El [diseño histórico BFF](../operaciones/borrador_bff_httponly_admin_h3req1_2026-10-01.md)
documenta que una revisión read-only clasificó HIGH la exposición de sesión Admin
en sessionStorage/localStorage, accesibles desde JavaScript. Este registro acredita
el hallazgo histórico y la motivación; no prueba inyección XSS explotable ni robo
efectivo de sesión. El BFF es la solución aprobada, no una vulnerabilidad nueva.
No afirmar que el HIGH original siga abierto en el código actual sin verificarlo:
el candidato ya incorporó HttpOnly y tiene regresiones parciales satisfactorias.

BFF significa Backend for Frontend, servidor intermedio de la interfaz. El navegador
llama al BFF del mismo sitio; el servidor procesa la sesión y operaciones allowlisted
contra Supabase con identidad de usuario. El navegador sí almacena/envía cookies;
HttpOnly impide leerlas desde JavaScript. No implica eliminar todos los riesgos XSS:
código inyectado aún podría emitir solicitudes con la sesión existente, por lo que
se conservan autorización, controles de origen, límites y validaciones.
Referencia primaria: [MDN Set-Cookie, HttpOnly](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#httponly).

Los cuatro pedidos ya tienen evidencia inicial de implementación y validación local:
[editorial/auditoría/disponibilidad](h3_course_editorial_local_cycle_2026-10-01.md)
y [encabezado](h3_admin_email_header_local_cycle_2026-10-01.md).
El harness actual también contiene pruebas de límite de disponibilidad de 90 días,
auditoría y publicación; presencia del test no acredita ejecución actual.
Se conserva evidencia fechada, se comparan inputs y se renueva cobertura afectada.

### Ruta recomendada, usando el plan vinculante existente

| Paso | Acción y límite | Resultado verificable / siguiente gate |
|---|---|---|
| 1. Recuperar diagnóstico útil | Aprobar/ejecutar únicamente captura WSL pendiente; no sudo, no runner antiguo, conservar líneas sanitizadas | Endpoint e imagen/F1 leídos bajo condiciones; analizar discrepancias reales, no inferir controles PASS por lecturas OK |
| 2. Reparar tooling demostrado | Completar r9 y parser/scanner/scope/linters bajo alcance vigente; cambios mínimos y revisión | G03 y G04 completos, sin repetir todo el entorno |
| 3. Probar arranque aislado | Copia íntegra de fuentes; luego healthz Pages/workerd; solo después conectar fixtures Edge/PG17/PostgREST | G05 y G06; cada etapa detiene dependientes si falla |
| 4. Integración y recuperación | C03 completo: operación, reserva, suspensión, rechazo de nuevos iniciadores, finalización única, cookies, conservación de datos/auditoría, resume y recuperación | G07 con evidencia por fase; preservar SQL probado |
| 5. Aceptar cuatro ajustes y no regresión | Ejecutar checks afectados, casos siguientes, UAT 144 sin retries/onboarding 10 y revisión independiente sobre candidato identificado | G08/G09; distinguir checks parciales de aceptación completa |
| 6. Control independiente CI | Validar patch V3 en Docker; preparar paquete protegido e aislamiento frente a Pages Production; autorizar/publicar/verificar y requerir control, review humano SHA | G10; puede prepararse mientras se resuelve diagnóstico, no condicionar toda preparación a G04 |
| 7. Development | Con instrucciones separadas: integrar/deploy compatible, identificar artefacto y probar D01–D14; priorizar evidencia editorial D07–D11 y sesión D01–D02 sin excluir el resto | GO_LOCAL_PR antes de promoción del candidato y GO_DEVELOPMENT_REAL tras aceptación remota completa |

Aceptación explícita de los cuatro puntos:

- Edición: Admin autorizado guarda únicamente campos permitidos; recarga conserva cambios
  y procedencia; pipeline no pisa override; dos ediciones concurrentes muestran conflicto,
  sin sobrescritura silenciosa. Rol user mantiene exactamente permisos aprobados, no cero
  permisos editoriales por inferencia.
- Auditoría: cada modificación aceptada genera evento coherente con actor real, antes/después
  y fecha; un fallo no deja una modificación sin su evento; lectura protegida, sin editar/borrar
  historial desde UI. Preservar páginas públicas sin exponer auditoría privada.
- Disponibilidad: evidencia válida permite evaluar publicación junto a calidad y demás gates;
  ausencia/invalidez/vencimiento no habilita publicación nueva; límite inclusivo 90 días y
  rechazo >90; no forzar desaparición de toda cohorte legacy por el nuevo criterio. Tampoco
  inferir disponibilidad por texto ambiguo ni alterar datos operativos para fabricar PASS.
- Encabezado: correo de cuenta autenticada correcto, fallback si no disponible, legibilidad
  móvil/escritorio y permisos de rol conservados; no registrar correo real en evidencia pública.

### Matriz de aceptación sobre el candidato vigente

Los resultados iniciales siguientes pertenecen al ciclo fechado 2026-10-01. La evidencia
permanece preservada, pero no se reutiliza como PASS del candidato `4eb4d877a50b012bb630a129bd0c74482c33be9c`
sin comparar inputs. En este corte no se ejecutaron estas suites ni se demostró un defecto
funcional de los cuatro ajustes; por eso la acción es revalidar cobertura afectada, no alterar
implementación por anticipado.

| Ajuste | Fuentes/consumidores | Inputs de aceptación | Pruebas anteriores preservables | Cobertura a revalidar | Resultado actual | Siguiente acción |
|---|---|---|---|---|---|---|
| Edición Admin conserva procedencia | `db/migrations/20261001_h3_course_editorial_audit_availability.sql` (`admin_update_course`); `web/src/app/admin/edit/page.tsx`; Admin BFF RPC allowlist; lector de valores efectivos/base y versión | Admin activo, versión vigente, override de campo permitido distinto del valor pipeline; recargar; `null` restaura pipeline; guardar con versión obsoleta; user solo completa campos faltantes | PG17 editorial del ciclo 2026-10-01; contratos `tests/test_h3_admin_queue_ux_contract.py` y `tests/test_editorial_contract.py`; H3-CA4.2 y H3-CA4.5 de `tests/h3_local_uat.mjs` | Allowlist de campos; procedencia visible y estable al recargar; restauración; conflicto concurrente; límites admin/user | Implementación y pruebas iniciales PASS en el ciclo anterior; migration/UI/BFF sin digest histórico por archivo; ejecución actual pendiente | Comparar hashes actuales y renovar solo casos afectados en PG17/contrato/UAT dentro del runtime Docker autorizado; no sobrescribir procedencia ni silenciar conflicto. |
| Auditoría actor/fecha/antes/después | Mismo migration; tabla append-only `course_editorial_audit`; `admin_update_course`, disponibilidad y publicación; consulta paginada protegida de historial | Actor `auth.uid()` Admin; fila before conocida; mutación con razón; fila after; intento de lectura/modificación directa por rol sin permiso | PG17 inicial y asserts de `actor_user_id`, `created_at`, `old_values`, `new_values`; C03 SQL 41/41 es evidencia histórica separada | Evento atómico con actor/fecha/antes/después coherentes; fallo no deja mutación sin auditoría; historial protegido y append-only; sin PII en capturas públicas | El harness PG17 actual difiere por hash del corte que pasó 41/41; ese PASS no se reutiliza. No existe runtime actual ni prueba visual vigente del historial | Crear manifiesto de inputs de este candidato y revalidar casos de auditoría en PG17+C03 integrado, junto con editor y publicación. |
| Disponibilidad exige evidencia válida ≤90 días | Migration editorial/auditoría; campos URL/observed/valid-until/status; editor Admin; vista pública y regla de publicación | Evidencia HTTPS y observación válida; `valid_until` exactamente +90 días; >90 días; evidencia ausente, inválida o vencida; estado `unknown` legacy | PG17 inicial; `tests/test_h3_admin_queue_ux_contract.py` (fail-closed/límite); asserts de `tests/sql/h3_pg17_harness.sql` para borde inclusivo, >90, ausente/vencida y compatibilidad legacy | Límite inclusivo 90; rechazo >90; expiración vuelve al cálculo; ausencia/invalidez no habilita publicación; cohorte legacy `unknown` se conserva | El código actual contiene guards de 90 días y la evidencia inicial fue PASS; el harness cambió y no hay runtime que confirme el candidato | Comparar migration/UI/harness y renovar solo casos afectados en PG17+C03; no fabricar evidencia ni backfill para pasar. |
| Correo autenticado en encabezado | `web/src/lib/admin-auth.ts`; `web/src/app/admin/page.tsx`; endpoint de usuario del BFF; layout Admin | Admin/user con correo fixture de `auth.getUser()`; respuesta sin correo/error para fallback; viewports desktop/mobile; ninguna captura o log con correo real | Contrato de encabezado del ciclo inicial; `tests/test_h3_admin_queue_ux_contract.py`; H3-CA4.1 admin/user de `tests/h3_local_uat.mjs` | Email autenticado correcto; fallback; truncado/legible; roles/navegación no cambian; sin PII pública ni tokens JS | Implementación y TypeScript/contrato inicial PASS; hashes de auth/page/BFF no quedaron en evidencia de 2026-10-01; verificación visual actual pendiente | Comparar inputs del candidato y renovar casos visuales de ambos roles tras arranque/UAT, con fixture y capturas sanitizadas. |

Las regresiones compartidas de sesión HttpOnly, MFA/AAL2, roles, invitación y publicación
se cubren con `tests/test_mfa_compatibility_contract.py`, `tests/h3_admin_bff_mock_uat.mjs`,
`tests/h3_invitation_uat.mjs`, los casos H3-CA4.1/.5/.7/.8 de `tests/h3_local_uat.mjs` y los
harnesses PG17/C03 pertinentes. Son runners existentes; no se agrega framework. Su repetición
queda supeditada a cambios de inputs/cobertura y a las etapas Docker autorizadas. La UAT global
de 144 ejecuciones/capturas sin retries y onboarding 10/10 pertenecen al cierre final del
candidato: evidencia anterior solo queda como parcial hasta cotejar inputs; onboarding se
mantiene separado de la cuenta Admin existente.

**Reconciliación de inputs realizada:** `tests/test_h3_admin_queue_ux_contract.py` conserva el
SHA-256 `7586fd24b199791fcc72090150027dca7b1dfcb41bf3ef200d713fc9d2da23c8` del manifiesto
2026-10-04. El `tests/sql/h3_pg17_harness.sql` actual es `8d4ea8d0e55525b835f2e6220486860b685a9dff7e65cf1c0cb46efbf35adce5`, distinto del input
`e1525daa888895619b477402b688e0a3409d2eba9d53c1e2c60f674f03aa61d3` de ese mismo corte; por
tanto el PASS histórico C03 41/41 no se reutiliza para el harness actual. La evidencia del
ciclo 2026-10-01 no fijó digests por archivo de migration, páginas Admin, BFF ni runner visual;
sus PASS se conservan solo como iniciales hasta comparar contra un manifiesto/captura nueva.
El input del contrato Python coincide, pero los sources que valida y el harness integrado no
quedan acreditados por ese único digest. No se ejecutó suite durante esta reconciliación.

No hay decisión funcional nueva necesaria para esos criterios: están atestados. Retirar o
diferir BFF requeriría propuesta de alcance, revisión de riesgos y autorización expresa que
modifique la decisión existente. No es un permiso que pueda inferirse de pedir rapidez.
Una aceptación editorial parcial puede documentarse sin cerrar H3REQ1 integral; no renombrar
ese resultado como GO_LOCAL_PR para esquivar gates.

El defecto operativo adicional de captura se corrige con el wrapper pendiente, que evita exec
en shell interactiva y mantiene pausa. Conservar inmediatamente salida validada en evidencia.
Si la salida indica otro fallo, definir predicado exacto que falló y ensayo mínimo antes de
otro intento; no aumentar retries sin cambio demostrado. No prometer fecha ni esfuerzo en
porcentaje: los diez gates tienen pesos iguales, no duraciones iguales.

### Adición al prompt anterior para Luna

```text
La prioridad cliente son los cuatro ajustes: edición con procedencia, auditoría
actor/antes/después, disponibilidad con evidencia máxima 90 días y correo en header.
Ya están implementados con evidencia local inicial; no los recrees. Usa la sección
"Aclaración solicitada: origen BFF y ruta para los cuatro ajustes" de esta nota.

El BFF actual corrige el hallazgo histórico de sesión legible por JavaScript.
Conserva BFF/HttpOnly, MFA, roles, gateway y cuotas. No declares incidente XSS ni
HIGH actual por un reporte histórico; determina evidencia actual y límites.
No regreses a tokens accesibles desde JS ni diferir BFF sin decisión humana expresa.

Construye una matriz de estos cuatro criterios: componente/consumidores, inputs,
prueba previa preservable, prueba afectada a renovar, resultado actual y siguiente
acción ejecutable. Añade los casos de aceptación de esta nota a los runners
existentes solo si falta cobertura demostrada, sin segundo framework de pruebas.
No uses el fallo de diagnóstico Docker para marcar los cuatro como no implementados.

Tras aprobación del JIT WSL pendiente y resultado exigido, continúa fases ya
autorizadas sin pedir continua nuevamente: tooling, copia, arranque, integración,
aceptación del candidato. Prepara bootstrap CI mientras tanto; su publicación y
enforcement necesitan instrucción separada, y no deben desplegar Production.

Entrega avances por pruebas parciales y gates completos; 20% es cierre acreditado
del candidato, no implementación del producto. Al fallar entrega fase, exit,
predicado discrepante, evidencia, cambio necesario y caso mínimo de revalidación.
No repetir variantes de un mismo diagnóstico incompatible con WSL ni perder salida.
No terminar en otro plan cuando exista una ejecución autorizada pendiente.
La revisión y permisos protegidos siguen siendo necesarios para GO real.
```

Esta adición es plan/documentación: no aprueba el JIT pendiente ni ejecuta runtime.

### Adenda factual — atomicidad de auditoría editorial, 2026-10-09

La matriz anterior queda reconciliada hasta este corte. El archivo
`tests/sql/h3_pg17_harness.sql` cambió después del hash `8d4ea8d0e55525b835f2e6220486860b685a9dff7e65cf1c0cb46efbf35adce5` citado arriba; su hash actual es
`24868250cf598a42412394c9cc714e6826096865846d0e8c3a73cb2a02f8e355`. La comparación
identificó una falta específica de cobertura para el segundo criterio: no se forzaba el
fallo del append de auditoría mientras se comprobaba rollback completo del estado. Esto es
un gap de prueba, no un defecto de producto demostrado.

Se añadió al harness una restricción de prueba temporal `NOT VALID` que rechaza solo
`action='update'`; captura el nombre exacto del constraint fallido y luego exige que el row
completo de `course_editorial_state` y el conteo de auditoría coincidan con el snapshot
previo. La restricción se elimina antes del flujo positivo existente. Manifest transitivo:
36/36 archivos coinciden. Revisión estática, sintaxis Bash del runner y whitespace check
PASS; **el harness SQL no se ejecutó**. C03 safe-suspend v3 41/41 pertenece a otro manifest y
no cubre este caso.

### Adenda factual — ejecución PG17 de la cobertura editorial, 2026-10-09

El JIT de una invocación para `H3REQ1-EDITORIAL-ATOMICITY-PG17-ONCE-20261009-V1` se
ejecutó y consumió. El runner alcanzó `pg17-start=OK`, pero el predicado exacto de versión
17.11 produjo `pg17-version=VERSION_MISMATCH`; la limpieza del contenedor efímero pasó. El
harness SQL, incluida la nueva aserción atómica, no llegó a ejecutarse. La salida no conserva
la versión real, así que no se concluye qué versión contenía el digest ni se atribuye una causa
a Docker. El detalle sanitizado está en
[la evidencia de PG17 y npm V2](h3req1_pg17_and_npm_capture_execution_2026-10-09.md). No se
reutiliza 41/41 para esta cobertura ni se suma punto a G01.

La ejecución requiere el JIT
`operaciones/jit_h3req1_editorial_atomicity_pg17_once_2026-10-09.md`, SHA-256
`a795528ec0376ac64a88344a03380644eed5122da9f52ffd44cf19cd3b923ef7`. Se limita a una
instancia PG17 efímera con `network none`, sin volumen, `PGDATA` tmpfs y SQL allowlisted;
todavía no está aprobado ni consumido. El resultado actual de auditoría permanece
“implementación y pruebas iniciales históricas; cobertura atómica preparada; runtime
pendiente”. La métrica de cierre sigue en 10%, sin incremento por esta adenda.
