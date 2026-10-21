# H3REQ1 — diagnóstico por fases y lectura CI: preparación

## Actualización vigente — paquetes de subpasos y bootstrap CI — 2026-10-08

Esta sección actualiza el estado; el resto del documento conserva la evidencia y el corte
histórico del diagnóstico anterior. No se repitió F2d ni el diagnóstico de fase.

El nuevo paquete
[peer-substep](../operaciones/jit_h3req1_peer_substep_diag_once_2026-10-08.md) separa
creación/configuración/conexión, lectura/decodificación de SO_PEERCRED, lecturas stat,
comm, ejecutable, UID y namespaces, y revalidaciones del socket. Solo registra fase y
código sanitizado. F1 se lee en la misma invocación únicamente después de identidad
peer-identity-verified|OK. El usuario aprobó su ID/SHA exacto, pero luego confirmó Docker
Desktop para Windows con WSL integration. El runner de ese JIT se ejecutó después una vez
desde Ubuntu WSL como root y devolvió `phase=peer-identity|error_code=IDENTITY_MISMATCH`;
queda consumido, no se repite y no leyó F1. Docker documenta que el Engine corre en la distro
aislada `docker-desktop`; ese resultado no identifica qué condición del predicado difirió ni
demuestra que Docker esté mal. Se preparó una alternativa WSL de menor garantía,
[JIT endpoint + F1](../operaciones/jit_h3req1_docker_desktop_wsl_attestation_once_2026-10-08.md),
SHA `9327c0ea163e47aa35c798442fec4230341b97fda1c19dfa811c492e3416fe4d`, y
[decisión consolidada](../operaciones/h3req1_cierre_dependencias_wsl_y_ci_2026-10-08.md).
No prueba PID/UID/ejecutable/namespace. El usuario aprobó una invocación y aceptó el residual
MEDIUM; informó que la ejecutó, pero la terminal se cerró antes de compartir su salida. La
invocación queda consumida y no hay evidencia runtime disponible. El usuario planteó preferencia por reconstruir imágenes, pero el
alcance aprobado conserva digests fijados y valida el WIP mediante copia aislada; no se ha hecho
rebuild/pull ni limpieza de recursos. Sus tests sintéticos están escritos, no ejecutados, con
revisión estática manual.

El bootstrap CI
[V3](../operaciones/h3req1_ci_bootstrap_package_2026-10-08.md) conserva un patch aislado
de cuatro rutas desde la base 4eb4d877a50b012bb630a129bd0c74482c33be9. SHA-256 del patch:
4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b. Según el registro
del paquete, git apply --check y git diff --check pasaron sobre un snapshot aislado.
La revisión independiente recomienda hold_for_evidence y no confirmó bypass de código.
Pytest, actionlint, Docker y workflow remoto no se ejecutaron. El usuario confirmó cuenta
personal (owner `type=User`), no Enterprise, Policies vacío y Policy Insights Enterprise-only.
La policy pública predeterminada para pull_request_target está en evaluate hoy, runs continúan,
con enforcement anunciado para 2026-11-02; no se vuelve a pedir scope ni capturas. Cloudflare
Production `main`, watch include `*`, exclude vacío y resto del build config están confirmados.
El usuario compartió Deployments con un Preview histórico en
`feat/h3req1-development-remote-tests`; esto no revela el modo actual Preview branch control.
Faltan merge queue por rama, un run real de PWI asociado al SHA vigente
y comprobar reevaluación ante avance de base con head estable. Las capturas ya recibidas
confirman PR, una approval, stale dismissal, up-to-date y únicamente security-audit
requerido en las tres ramas; no volver a pedir esos datos.

GitHub identifica el repositorio como público. Su policy predeterminada para
pull_request_target actualmente está en evaluate y permite que los runs continúen; si no
existe una Actions event policy aplicable a nivel organización/enterprise, pasará a bloquear
ese evento el 2026-11-02. Falta comprobar el scope efectivo en Policy insights antes de usar
el workflow. Referencias oficiales: [pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)
y [workflow execution policies](https://docs.github.com/en/actions/how-tos/administer/control-workflow-execution).

El ruleset owner-only-protected-branch-updates continúa activo; identidad del bypass
redactada. No se escribieron branch rules, Actions policy ni settings de Pages, y el patch
no está instalado. G01–G02 permanecen 10/10, G03–G10 0/10, total 20%; no GO. Los PASS
parciales anteriores se conservan por separado en
[tablero](../operaciones/h3req1_avance_por_gates_y_prompt_luna_2026-10-08.md).

Fecha: 2026-10-08. Continuación del análisis de sesión
`01a11de1-1403-7133-b10e-6fd9f8543905`.  
Autoridad: [.context/estado_del_proyecto.md](../estado_del_proyecto.md),
[AGENTS.md](../../AGENTS.md), [revisión de bloqueos](h3req1_revision_sesion_01a11de1_bloqueos_2026-10-08.md)
y [paquete consolidado aprobado](../operaciones/h3req1_paquete_consolidado_cierre_local_luna_2026-10-08.md).

## Ficha constructor

- Objetivo/criterio: distinguir la fase del error local y, si se completan las
  comprobaciones existentes de K14, acreditar la identidad del peer Docker sin exponer
  metadata cruda. No cierra por sí sola G04.
- Archivos/dominios: helper y fixture nuevos en
  `tests/h3req1_docker_peer_phase_diag/`; JIT, evidencia, estado y tablero. Se dejan intactos
  el helper/runner/reporte consumidos F2d, el código producto y los otros WIP.
- Contrato: K14 (runtime Linux/Docker y errores sanitizados), QA y DOC/REL. No se cambia
  K01–K13, wire, DB, UI, BFF, Edge ni workflows.
- Dependencias directas: Python existente, `docker context show/inspect` local, socket Unix
  seleccionado y `/proc`. Consumidores posteriores condicionados: preflight r9, copia
  completa, startup Pages/workerd y C03 integrado. Arista inversa: el check local Docker
  decide si se puede iniciar el tooling del ciclo; no configura el daemon.
- Comportamiento preservado: endpoint no Unix y overrides se rechazan; la prueba no manda
  bytes de aplicación, no consulta Docker API, no lee datos del contenedor ni muta recursos.
  F2d/F1 y evidencia histórica permanecen intactos.
- Pruebas: 14 escenarios sintéticos escritos; ejecución pendiente en Docker después de
  acreditar identidad. Las suites previas se clasifican abajo por alcance y no se invalidan.
- Transición/rollback: expand/compatibilidad/deploy/contract no aplica a tooling sin efecto
  funcional ni despliegue de producto. Rollback local: retirar solo helper/test nuevos y
  revertir las líneas documentales de este corte; conservar resultados históricos.
- Permisos: autoría B local/documental ya aprobada; la invocación diagnóstica elevada requiere
  aprobación exacta nueva. r9 y fases posteriores permanecen condicionales a identidad y a
  sus límites ya aprobados. C sigue siendo GET solamente; ningún JIT autoriza writes CI.
- Desconocidos: fase y código reales del socket; reglas administrativas CI/required checks;
  enforcement remoto. No inferir daemon/motor inválido, `main` ausente ni protección ausente.
- Seis pilares: no aplicables al producto porque no se modificó su runtime/contrato. Para la
  herramienta, seguridad se revisó estáticamente; calidad de tests/runtime está pendiente;
  escala, rendimiento y disponibilidad del producto no se midieron ni se atribuyen.
- Gate: G04 sigue 0/10 hasta evidencia fresca de diagnóstico y la disposición del F1 dentro
  de autorización vigente. Si falla, stop; no cambiar el motor ni repetir sin decisión nueva.

## Diagnóstico local: solicitud lista, no ejecutada

El F2d previo permanece consumido. No se vuelve a llamar su runner ni se presume una causa
del NO-GO anterior. Se preparó una herramienta separada que lee solo la configuración local
del contexto Docker y separa las fases `socket-create`, `socket-configure`, `connect`,
`identity-read` (`SO_PEERCRED`), `decode` y `peer-identity`. Endpoint no Unix, variables de
override o contexto inaccesible terminan antes de crear el socket.

La salida del diagnóstico está limitada a `phase=<fase>|error_code=<código>`. Los errores
del sistema se convierten a nombres simbólicos; excepciones, ruta de socket, PID, UID/GID,
ejecutable, bytes de credenciales, `Env` e inspect no se imprimen ni se guardan. El helper
no manda bytes de aplicación, no consulta la Docker API y no muta archivos, Docker ni
recursos. La identidad se decide con credenciales del kernel y metadatos del proceso; el
binario no se verifica mediante hash/firma, por lo que no se atestigua integridad frente a
un root comprometido.

El JIT de una sola invocación quedó preparado en
[solicitud](../operaciones/jit_h3req1_peer_phase_diagnostic_once_2026-10-08.md), SHA-256
`70764727e392ebb612ca44d9ffadc0bec4b1bb2ef38158d20489b99200c396df`. Requiere la llamada
del entorno con `sandbox_permissions=require_escalated`, timeout externo de 30 s y cero
retry. El usuario aprobó el ID/SHA y el comando. La única invocación elevada terminó en exit 1
con la salida exacta `phase=peer-identity|error_code=EACCES`; no se hizo retry y el JIT quedó
consumido. Según el flujo estático, se superaron creación/configuración, conexión, lectura
`SO_PEERCRED` y decodificación. La fase `peer-identity` puede reportar EACCES al leer metadata
del proceso del peer o al volver a inspeccionar el socket; la salida sanitizada no identifica
cuál subpaso originó el error. Esto prueba el punto de fallo observable, no una causa raíz del
daemon. No se cambió Docker ni se instaló otro motor.

Los fixtures sintéticos contienen 14 escenarios previstos: endpoint local, rechazo de
endpoint remoto y override, éxito, creación/configuración/conexión/lectura/decodificación,
errores OS no mapeados, discrepancia de credenciales y tres discrepancias de metadatos.
Están escritos, no ejecutados. AGENTS exige correr pruebas de Python dentro de Docker y el
gate de Docker aún no tiene identidad acreditada. La revisión estática independiente
@security-auditor encontró primero una ruta de importación incorrecta en el test; se corrigió
y el segundo pase no encontró findings dentro de los dos archivos. No se atribuye PASS de
runtime ni de tests. El criterio de identidad conserva una limitación documentada: no hace
hash/firma del binario.

El Codex Security diff-scan no inició: la herramienta rechazó alcance de subdirectorio y
exigió la raíz Git completa con `scope="."`. No se inició para evitar un scan que incluyera
WIP ajeno; tampoco se repitió un scan completo del repositorio.

## GitHub: reglas confirmadas y candidato CI validado

La cuenta GitHub conectada tiene rol `admin` en `romelhc95/studiamatch`; el conector puede
leer archivos de rama, aunque no expone endpoints para reglas. Las capturas aportadas por el
usuario confirman las reglas clásicas de `desarrollo`, `certificacion` y `main`:

| Ajuste clásico | desarrollo | certificacion | main |
|---|---:|---:|---:|
| Require pull request | Sí | Sí | Sí |
| Required approvals | 1 | 1 | 1 |
| Dismiss stale approvals | Sí | Sí | Sí |
| Aprobar último push revisable | Sí | Sí | No |
| Required status checks | `security-audit` | `security-audit` | `security-audit` |
| Branches up to date | Sí | Sí | Sí |
| Do not allow bypassing classic settings | Sí | Sí | Sí |
| Force-push / deletion | Desactivados | Desactivados | Desactivados |
| Code Owners / conversation resolution / signed commits / linear history / deployments / lock | No | No | No |

El listado capturado muestra un solo ruleset: `owner-only-protected-branch-updates`, Active y
targeteando las tres ramas. Su detalle muestra como única regla activa `Restrict updates` y un
actor de tipo User con bypass `Always allow`. Su identidad no se copia. El bypass del ruleset
y el no-bypass de las reglas clásicas se registran por separado; no se afirma una precedencia
que no se comprobó.

La lectura read-only del conector confirmó además en cada rama que `.github/workflows/`
contiene `security-audit.yml`, sin `protected-workflow-integrity.yml`. Los tres workflows
remotos se disparan con `pull_request`; el agregado `security-audit` depende de las otras
validaciones declaradas en el mismo workflow, no de `Protected Workflow Integrity`. El check
independiente no aparece entre los required checks de las capturas. Se preserva la diferencia
del archivo local WIP: que exista localmente no acredita que esté instalado en ramas remotas.

Por tanto, se resolvió el 403 de lectura mediante la vía suficiente: capturas sanitizadas de
Settings y lecturas de contenido con el GitHub MCP autenticado. El candidato diferido
`candidate-500f085f897ba6f7` queda validado como brecha de integridad CI MEDIUM. Un PR necesita
la aprobación humana configurada, pero el único status requerido puede redefinirse junto con
el workflow que lo emite. No se probó un bypass, no se modificaron settings y no se repitió el
scan sellado. El informe de validación está guardado como artefacto complementario Codex
Security bajo `findings/candidate-500f085f897ba6f7/validation_report.md` (SHA-256
`8a7a6e0682424a307d7a60c3c0bbff8210f9ddb4737008f8266677cd402ce230`).

## Solicitud consolidada pendiente: cerrar G10 de integridad CI

**Objetivo único:** que cada rama protegida exija un status independiente de integridad
trusted, además de `security-audit`. Las capturas ya resuelven la lectura; no se necesita
otra captura, hash por archivo ni permiso de lectura.

El candidato local WIP relevante está agrupado en `.github/workflows/protected-workflow-integrity.yml`,
`.github/workflows/security-audit.yml`, `scripts/security/protected_workflow_review.py` y
`tests/test_protected_workflow_review.py`. El workflow trusted emite el job
`Protected Workflow Integrity` desde el SHA base del PR; el aggregator local falla cerrado
si no confirma ese job para el head del PR. Estos archivos no están instalados en refs remotas.

**Dependencia previa:** completar validación local y revisión del paquete en el entorno Docker.
Hoy está bloqueada porque la única invocación autorizada terminó en
`phase=peer-identity|error_code=EACCES`; no se repetirá ni se cambiará el motor sin causa
demostrada y autorización nueva. Los tests de este paquete no se declaran PASS por estar
escritos o revisados estáticamente.

Cuando la dependencia esté resuelta, la autorización debe agrupar el objetivo y sus fases:
(1) validación local del candidato existente; (2) autorización explícita para publicar el
cambio como PR a `desarrollo` y revisión/merge humano según el flujo protegido; (3) después de
que el workflow exista y emita su status en cada base, autorización para configurar en las
tres reglas clásicas el check exacto `Protected Workflow Integrity`, conservando
`security-audit`. No se cambia el actor bypass del ruleset ni se modifica la política distinta
de aprobación del último push en `main`. La aprobación inicial de A/B/C cubre CI solo en
lectura, no estos writes protegidos. La solicitud se presentará como un objetivo consolidado,
no por archivo o digest. Hasta entonces, no se abre PR ni se guardan cambios en Settings.

## Reconciliación de autorizaciones y gates

Se revalidó el SHA aprobado del paquete consolidado y los pins de r9: JIT r9
`49502617f2bb788b2e9664e659c3f9dd4fe3dc84188ee0b5d86e2909c3dadedf`, inputs
`6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee` (71/71 verificados),
wrapper `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`, paquete
`b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`, herramientas
`4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa` (checks de SHA sin
ejecución de binarios). No hay rutas `.env*` ni `node_modules/.deno` en el manifiesto r9.

- Consumido: una invocación F2d, terminó NO-GO; y una única invocación del nuevo diagnóstico
  elevada, `peer-identity/EACCES`. Ninguno se repite.
- Pendiente condicional: r9 y fases locales A/B (copia completa, smoke, C03 integrado) siguen
  dentro del paquete aprobado, después de identidad y preflight, con sus límites originales.
- No ejecutado: inspección de F1; no forma parte del nuevo diagnóstico y no se asume permiso
  operativo separado del F2d consumido. No se inspeccionará F1 por esta solicitud.
- CI C sigue siendo solo GET/read. Ya se acreditaron required checks/reviews. No hay
  autorización para configurar branch protection ni realizar otros writes protegidos.
- Condición no cumplida: el peer no quedó acreditado. No se habilitan r9, copia, startup ni
  C03 integrado hasta resolver la causa y obtener una identidad verificable dentro del alcance.

### G01–G10 al corte

| Gate | Estado | Evidencia/pendiente |
|---|---:|---|
| G01 | 10/10 | SQL/wire C02 histórico PASS. |
| G02 | 10/10 | SQL C03 suspensión/resume PASS; 41/41 inputs. |
| G03 | 0/10 | pytest/proyector/scope/scanner parciales aprobados; faltan linters y cierre de revisión. |
| G04 | 0/10 | Nuevo diagnóstico elevado: `peer-identity/EACCES`; identidad no acreditada. |
| G05 | 0/10 | Falta copia completa aislada verificada. |
| G06 | 0/10 | Falta healthz Pages/workerd real. |
| G07 | 0/10 | Falta C03 integrado real. |
| G08 | 0/10 | UAT BFF parcial; faltan checks/revisión final. |
| G09 | 0/10 | Falta UAT final, aceptación, pilares y trazabilidad completa. |
| G10 | 0/10 | PR/review y `security-audit` requeridos confirmados; falta que el check de integridad confiable exista y sea requerido. Hay 1 actor User de bypass en el ruleset; identidad redactada. |
| Total | **20%** | G01–G02 completos; G03–G10 abiertos. No hay incremento por preparación. |

### Pruebas previas aprobadas, separadas por alcance

| Evidencia | Resultado | Gate completo |
|---|---|---|
| SQL/wire C02 | PASS histórico | G01, 10/10 |
| SQL suspensión/resume C03 | PASS v3; inputs 41/41 | G02, 10/10 |
| r4 pytest seleccionado (incluye fixture peer sintético) | 20/20 | Ninguno adicional; G03/G04 siguen abiertos |
| r4 proyector de metadata | PASS | Ninguno; G03 sigue abierto |
| r4 scope guard | PASS en los casos del paquete | Ninguno; G03 sigue abierto |
| r7 regresión scanner | PASS, 3/3, exit 0 | Ninguno; G03 sigue abierto |
| BFF r2 UAT | PASS, 60 verificaciones y 10 casos de cuota | Ninguno; G08 sigue abierto |
| Nuevo diagnóstico elevado | `peer-identity/EACCES`, exit 1; una invocación | G04 sigue abierto |

## Addendum vigente — ubicación Docker y estado administrativo — 2026-10-08

El usuario aclaró Docker Desktop para Windows con WSL integration. El Engine corre en la
distro WSL interna `docker-desktop`, aislada de Ubuntu; el checkout fijado está en Ubuntu y
`sudo` allí no da acceso al `/proc` aislado del Engine. El JIT peer-substep aprobado
(`e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173`) permanece no consumido
y no se debe pegar en Ubuntu ni en un contenedor. No hay un ID de contenedor correcto para
ese diagnóstico de host.

Se preparó el [JIT de alternativa WSL](../operaciones/jit_h3req1_docker_desktop_wsl_attestation_once_2026-10-08.md)
y [solicitud consolidada](../operaciones/h3req1_cierre_dependencias_wsl_y_ci_2026-10-08.md).
No prueba PID/UID del daemon; la salida es una atestación de endpoint WSL y respuesta Linux
del Engine, con lectura F1 posterior condicionada. El usuario aprobó una invocación y aceptó
el residual MEDIUM; informó que ejecutó el bloque, pero no recibió/compartió las líneas phase/error_code
antes de cerrarse el terminal. La invocación queda consumida. Tests sintéticos escritos/no
ejecutados y revisión estática manual no sustituyen runtime.

El usuario expresó preferencia por reconstruir las imágenes para tener un ambiente limpio.
Eso no está incluido en la aprobación: el código candidato se toma desde copia aislada y los
runtimes mantienen digests fijados; no se reconstruyen imágenes ni se limpian recursos históricos.

GitHub: el owner `type=User` y el usuario confirma cuenta personal no Enterprise, sin policies
de Actions creadas; Policy insights es Enterprise-only. La policy predeterminada de GitHub para
PRT en repos públicos está hoy en `evaluate` (runs continúan), con enforcement anunciado
2026-11-02. No hace falta nueva intervención de policy para el primer bootstrap ahora; antes
de esa fecha habrá que autorizar PRT mediante event policy del repo si el control aún lo usa.
No se repiten capturas. Cloudflare settings confirmados incluyen Production `main`, automático,
watch include `*`/exclude vacío, root `web`, build/output declarados, cache off, v3 y sin hooks.
Deployments muestra un Preview histórico de `feat/h3req1-development-remote-tests`; esto no
establece el modo Preview branch control. El MCP `cf-builds` no está habilitado en las herramientas
de esta sesión. Falta además confirmar merge queue por rama. El patch CI permanece aislado,
sin aplicar/publicar, y su ruta de Pages sigue necesitando verificación/decisión protegida.

G04 no cambia hasta que endpoint/Linux y F1 queden acreditados; G10 no cambia. Total 20%; no GO.

## Addendum vigente — salida de la invocación alternativa no recuperable

El usuario confirmó que no puede recuperar el scrollback y no vio ninguna línea de resultado.
El JIT Docker Desktop WSL V1 queda consumido sin PASS/FAIL inferible; no habilita r9. Se
preparó, sin ejecutar, un nuevo JIT de captura que conserva el runner/pins, valida que cada
línea mostrada cumpla `phase=…|error_code=…` y mantiene la terminal interactiva en pausa:
[solicitud](../operaciones/jit_h3req1_docker_desktop_wsl_output_capture_once_2026-10-08.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-OUTPUT-CAPTURE-ONCE-20261008-V1`, SHA-256
`bbaa2242bf026f252864b4e476a60e9de2a8e327c0456d2b343b612402c61c92`. Requiere aprobación
nueva y como máximo repite las lecturas allowlisted de endpoint, imagen y F1. No se ejecutó
runner, Docker ni prueba sintética. G04 permanece 0/10 y total 20%.
| Sus 14 escenarios sintéticos | Preparados, no ejecutados | Ninguno |

Esta preparación no cambia el total 20%, no acredita un runtime y no declara GO.
