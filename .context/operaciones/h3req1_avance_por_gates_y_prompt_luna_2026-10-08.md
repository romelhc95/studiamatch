# H3REQ1 — avance por gates, análisis de sesión y prompt Luna 6 Max

Fecha: 2026-10-08. Sesión evaluada: `01a11c04-d49d-7dc3-8201-0a03535a7508`.
Corte anterior: [análisis 01a11a7e](../evidencia/h3req1_analisis_sesion_01a11a7e_2026-10-08.md).
Autoridad: [estado vivo](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md),
[plan único](plan_cierre_integral_h3req1_2026-10-04.md) y
[ruta vigente en el corte 2026-10-08, ahora archivada](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md).
Esta métrica es seguimiento de cierre acreditado, no porcentaje de implementación,
esfuerzo restante, probabilidad de éxito ni sustituto de los gates vinculantes.

## Actualización de la continuación 01a11de1 — 2026-10-08

### Aclaración vigente tras confirmar Docker Desktop WSL — 2026-10-08

El usuario confirmó Docker Desktop de Windows con WSL integration. El Engine corre en la distro
interna `docker-desktop`, aislada; `sudo` en Ubuntu no da root ni `/proc` de esa distro. El JIT
peer-substep aprobado (SHA `e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173`)
se ejecutó desde Ubuntu WSL y quedó consumido con
`phase=peer-identity|error_code=IDENTITY_MISMATCH`; no repetir ni leer F1 por esa ruta.
El usuario aprobó una invocación de la alternativa WSL y aceptó el residual MEDIUM; informó que
la ejecutó, pero la terminal cerró antes de que compartiera las líneas phase/error_code. La
invocación queda consumida sin resultado utilizable. La alternativa acotada está en
[paquete WSL + CI](h3req1_cierre_dependencias_wsl_y_ci_2026-10-08.md) y
[JIT Docker Desktop WSL](jit_h3req1_docker_desktop_wsl_attestation_once_2026-10-08.md),
SHA `9327c0ea163e47aa35c798442fec4230341b97fda1c19dfa811c492e3416fe4d`.
No prueba identidad PID-level. La aprobación no incluye rebuild/pull ni limpieza de recursos;
el ciclo usa digests fijados y copia aislada del WIP. El usuario manifestó preferencia por una
imagen reconstruida; se explicó que eso cambiaría los pins y no incorpora por sí solo el código
fuente actual. No se reconstruyó ni retiró recurso alguno.

GitHub MCP confirma owner `User`; el usuario confirmó cuenta personal no Enterprise, sin
Actions policies propias. Policy Insights Enterprise-only. La policy pública predeterminada
de `pull_request_target` está en `evaluate` hoy (runs continúan); enforcement anunciado
2026-11-02. No falta intervención inmediata de policy para probar bootstrap; sí una política
de evento repo antes de esa fecha si PRT sigue siendo necesario. Cloudflare Production `main`,
auto deployments, include `*`/exclude vacío y configuración de build están confirmados. El
usuario compartió Deployments con un Preview histórico de
`feat/h3req1-development-remote-tests`; no acredita el modo exacto Preview branches ni el
bootstrap. El merge queue por rama sigue sin confirmarse. No repetir capturas ni pedir otro
acceso a `cf-builds` mientras no esté habilitado en esta sesión.

### Estrategia vigente para superar las dependencias y cerrar

Esta estrategia se solicita tras revisar la continuación; no es autorización ni nuevo
resultado. Alcance de la actualización: DOC/K14/REL, consumidores estado/ruta/ejecutor;
sin cambios de código, contrato o runtime. Preservar notas/pins/JIT consumidos, fuentes y
ambos checkouts. Rollback solo de estas adiciones. El paquete A/B vigente conserva sus
fases condicionales; no pedir otra autorización para las mismas operaciones no consumidas.
Los métodos diagnósticos consumidos y CI write no se reactivan por ese permiso.

Dos frentes, con preparación independiente y ejecución condicionada:

1. **Acceso e identidad local:** el último resultado ya prueba socket/configuración,
   conexión, SO_PEERCRED y decodificación alcanzadas. No volver a investigar esas fases.
   `peer-identity/EACCES` deja sin distinguir lectura de `/proc` y revalidación del socket;
   separar todos los subpasos en un solo diagnóstico (stat inicial/final, comm, exe-readlink,
   exe-stat, UID y namespaces), códigos sanitizados, sin PID/ruta/Env crudos. Preflight debe
   demostrar que el contexto de ejecución dispone de permiso real para esas lecturas;
   solicitar acceso elevado del sandbox no acredita por sí solo privilegios suficientes.
   No asignar EACCES a un subpaso sin evidencia. Preparar permiso por objetivo de diagnóstico
   y lectura F1 allowlisted condicionada a identidad PASS, sin permisos por cada campo.
   Si requiere administrador local, entregar al humano un script revisado y acotado para
   ejecutar/verificar en el host correcto; no reinstalar engine ni cambiar permisos globales.
   Sin identidad no se inicia r9. Si el entorno no ofrece esa prueba, presentar alternativa
   verificable, costo/impacto y aprobación; no seguir con métodos equivalentes a ciegas.
2. **CI independiente:** la evidencia administrativa ya está disponible y la ausencia del
   workflow/check independiente está confirmada. No pedir otra vez capturas ni repetir el
   conector que no expone reglas. Preparar desde base confiable un paquete bootstrap solo
   de controles: workflow/helper/tests y mínima integración necesaria. No incluir producto,
   SQL ni el WIP completo. Congelar patch/manifest/branch base y publicar solo tras instrucción
   separada. La validación local del patch espera Docker acreditado; su preparación no.
   El primer bootstrap debe evitar depender de un workflow ausente en su base. Mantener
   protecciones existentes, revisión independiente/humana y las identidades distintas
   del plan. Instalar primero y comprobar emisión del job; luego configurar el check exacto
   `Protected Workflow Integrity` junto con `security-audit` en las bases aprobadas.
   Concretar por rama transición del control sin promover código funcional a main ni disparar
   despliegues del producto inadvertidamente. Verificar eventos/efectos y pedir alcance
   separado si la vía elegida afecta despliegues. No cambiar actor bypass ni política de
   último push de main por analogía. Evidencia de cierre: bloqueo sin aprobación, rechazo
   de review obsoleto y aceptación del SHA vigente según plan, con snapshots sanitizados de
   configuración y resultados. Writes/merge/configuración no están autorizados aún.

Tras desbloqueo, ejecutar en orden: r9 (sin descargas, permisos de todos los ancestros y
fuentes verificados) -> diagnóstico/remediación F1 según alcance nuevo -> copia completa
-> healthz Pages/workerd -> C03 conjunto -> candidato/checks/UAT final -> revisión/
atestación/pilares/grafo. Conservar SQL/wire intacto por impacto; no repetir todo por
documentación. No borrar fixtures antiguos como precondición ni usar una excepción de
seguridad para producir PASS. Cada FAIL debe tener subpaso/exit/causa y corrección revisada.

Hitos de seguimiento, todos condicionados a evidencia íntegra y sin nuevos findings:
G03 y G04 cerrados => 40%; copia+arranque+C03 => 70%; candidato final+aceptación => 90%;
CI efectivo/paquete PR completo => 100% GO_LOCAL_PR. G10 puede cerrarse antes en paralelo,
pero el total suma solo gates realmente cerrados. No dar crédito doble ni asumir que
comprobar identidad por sí sola cierra G04: también exige disposición F1.

GO_LOCAL_PR no inicia por sí solo aceptación remota: después se requiere autorización
commit/push/PR del producto, integración/review/merge y despliegue Development, con
artefactos/host/bindings/schema identificados. Free Dev/Cert compartido, Pro intacto;
expand compatible -> Worker/DO -> Edge -> Pages/BFF -> gateway con consumidores listos.
Mantener cuenta MFA, onboarding separado y rollback; ventana aprobada D01–D14 literal.
GO_DEVELOPMENT_REAL solo después de esa aceptación. Certification/Production funcional
quedan fuera. Los dos paquetes concretos ya están preparados y vinculados abajo; su
preparación no autoriza ejecutar el diagnóstico ni promover el patch.

El diagnóstico separado del F2d se ejecutó una sola vez con aprobación elevada exacta y terminó
`phase=peer-identity|error_code=EACCES`, exit 1. Llegó a la validación del peer; no acredita
identidad ni precisa si EACCES vino de metadata del proceso o de revalidar el socket. No se
ejecutaron pruebas sintéticas, r9, copia, startup ni C03, y no se cambió Docker. Las capturas
confirman PR, 1 approval, stale dismissal, up-to-date y solo `security-audit` requerido en las
tres ramas; el workflow PWI independiente no existe en refs remotas. El ruleset está activo;
su bypass actor se mantiene redactado. El candidato de integridad CI queda confirmado y
documentado; no se modificó configuración protegida.
Ver [preparación diagnóstica y CI](../evidencia/h3req1_diagnostic_ci_prep_2026-10-08.md)
y [solicitud JIT](jit_h3req1_peer_phase_diagnostic_once_2026-10-08.md), SHA-256
`70764727e392ebb612ca44d9ffadc0bec4b1bb2ef38158d20489b99200c396df`.

| Gate | Estado actual | Delta de este corte |
|---|---:|---:|
| G01 | 10/10 | 0 |
| G02 | 10/10 | 0 |
| G03 | 0/10 | 0 |
| G04 | 0/10 | 0 |
| G05 | 0/10 | 0 |
| G06 | 0/10 | 0 |
| G07 | 0/10 | 0 |
| G08 | 0/10 | 0 |
| G09 | 0/10 | 0 |
| G10 | 0/10 | 0 |
| Total | **20%** | **0 puntos porcentuales** |

Las pruebas parciales aprobadas se muestran individualmente en la evidencia enlazada. No se
suman entre gates ni sustituyen sus criterios de cierre.

## Resultado de los dos paquetes exigidos — 2026-10-08

| Frente | Entrega y estado | Dependencia inmediata |
|---|---|---|
| Diagnóstico Docker | JIT peer-substep, SHA `e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173`, consumido en Ubuntu WSL con `IDENTITY_MISMATCH`; no F1. JIT alternativo aprobado y ejecutado, pero la salida no fue recibida. | No repetir ninguna de esas invocaciones. Intentar recuperar únicamente las líneas phase/error_code del scrollback; sin ellas no se acredita endpoint/Linux ni F1 y r9 no está habilitado. No rebuild/pull ni limpieza bajo este permiso. |
| Bootstrap CI | [Paquete V3](h3req1_ci_bootstrap_package_2026-10-08.md) y [patch](../evidencia/h3req1_ci_bootstrap_minimal.patch), base 4eb4d877a50b012bb630a129bd0c74482c33be9, SHA-256 4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b. Revisión independiente hold_for_evidence; no instalado. | PRT policy pública está en evaluate, no requiere write inmediata; antes de 2026-11-02 puede requerir event policy repo. Pages Production `main`, include `*`, exclude vacío; Deployments muestra Preview histórico en una rama feature, pero el modo branch control sigue desconocido. Merge queue por rama, verificación Pages y check real/head/re-evaluación base pendientes. |

Las pruebas sintéticas del diagnóstico (32 casos previstos) están escritas, sin ejecutar.
La validación local del patch CI (pytest/actionlint/Docker) también queda pendiente hasta
acreditar Docker. Solo constan como parciales históricos aprobados: SQL C03 v3 PASS con
41/41 inputs; pytest r4 20/20, proyector/scope PASS y scanner r7 PASS; UAT BFF r2 con
60 checks y 10 casos de cuota PASS. Se reportan por separado y no elevan el total. r8 salió
126 antes de ejecutar checks. Las 144 ejecuciones visuales, onboarding 10/10 y revisión final
siguen pendientes de aceptación.

Estado vigente de G01–G10: G01=10/10, G02=10/10, G03=0/10 (parciales conservados),
G04=0/10 (JIT peer `IDENTITY_MISMATCH`; WSL V1 consumido sin salida; nuevo JIT output-capture pendiente de aprobación), G05=0/10, G06=0/10, G07=0/10, G08=0/10,
G09=0/10 y G10=0/10 (patch preparado, controles remotos sin instalar). Total 20%, delta 0.
No hay GO.

El manifiesto r9 mantiene su requisito textual de aprobación después de acreditar identidad.
La excepción iterativa aprobada en el paquete consolidado puede cubrir una ejecución de A/B
tras corrección revisada sin permiso por hash. Reconciliar el alcance antes de r9 y solicitar,
solo si hace falta, una autorización agrupada por objetivo/fase. No ejecutar r9 antes de identidad.

## Resultado del ciclo iterativo aprobado — 2026-10-08

El paquete consolidado V1 se aprobó y ejecutó en el alcance A/B/C. F2d consumió su única
invocación y terminó NO-GO en `daemon-identity-proof`: `direct-peer-credentials-unavailable`,
`api-requests=0`. Por el stop acordado no se ejecutó F1, r9, Docker, PG17, SQL, UAT ni runtime.
En ese corte GitHub fue read-only y las reglas seguían desconocidas por 403; la captura
posterior y validación read-only actualizan esa observación, no el resultado histórico del
ciclo. La revisión estática sellada terminó 51/51; el candidato CI antes diferido se validó
por separado. Ver [evidencia del ciclo](../evidencia/h3req1_cierre_local_iterativo_2026-10-08.md)
y [evidencia GitHub actual](../evidencia/h3req1_diagnostic_ci_prep_2026-10-08.md).

La comparación de cierre continúa **20% -> 20%**, delta 0; D01–D14 sigue 0/14. G01–G02
conservan sus 10 puntos; G03–G10 permanecen en cero. El bloqueo de identidad no acredita
G04 ni habilita GO_LOCAL_PR.

## Último ciclo — r8 exit 126; corrección r9 preparada — 2026-10-08

El Codex Security scan `2437a725-55cf-403d-8081-2c8f96520245` cerró 51/51 filas, cero
hallazgos reportables confirmados y cobertura parcial. Quedó un candidato medio condicional
de CI, pendiente de verificar si cada rama protegida exige `Protected Workflow Integrity`
como estado separado. La observación CORS se suprimió por falta de un flujo navegador que
entregue el JWT admin. El resultado es estático, para el snapshot
`codex-security-snapshot/v1:sha256:2f6b7c1204f9a7e3beb22543f02263a994ce304017705fb350526335179ace58`; el informe
advierte que el árbol cambió durante la revisión. No declara seguridad global ni GO.

R8 se autorizó para una invocación exacta, 180 s, sin retry. El manifiesto de 71 entradas
coincidió; las descargas actionlint 1.7.7 y ShellCheck 0.11.0 pasaron sus SHA-256. El
contenedor fijado se creó con red desactivada y fuente de solo lectura, pero falló antes de
ejecutar checks: exit 126, `bash: run-in-container.sh: Permission denied`. La causa es la
raíz del bind mount en modo 0700, owner UID/GID 1000, inaccesible al UID/GID 1001 interior.
No se ejecutaron linters, typecheck, pytest ni regresiones. El contenedor propio se retiró
por `--rm`; no hubo limpieza de recursos existentes.

Se preparó r9 con los mismos 71 inputs, raíz 0755 y los tarballs ya verificados, sin nuevas
descargas. `r9-package.sha256` =
`b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`; `run-r9.sh` =
`2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`. No se ejecutó.
F2c no acreditó el peer de `unix://`; hay que resolver la identidad del daemon antes de una
nueva operación Docker. r8 está consumido y r9 requiere JIT/permiso nuevo. G03 sigue abierto:
**20% -> 20%**, delta 0. D01–D14 permanece 0/14. Detalle en
[evidencia r7/r8/r9](../evidencia/h3req1_helper_docker_fixture_2026-10-08.md) y el
[JIT r9 propuesto](manifiesto_jit_h3_g03_local_validation_r9_2026-10-08.md).

## Ciclo previo — scanner r7 PASS — 2026-10-08

La aprobación r7 exacta se verificó contra el paquete congelado y se consumió en una
ejecución: manifiesto 3/3 y regresión del scanner PASS, exit 0, sin retry. r4 aportó pytest
20/20, proyector y scope guard PASS; r5/r6 localizaron el problema de la fixture bajo
`/tmp noexec`, resuelto en r7 con tmpfs ejecutable acotado. G03 sigue incompleto por falta
de linters/revisión pertinentes: **20% -> 20%**, delta 0. Permisos consumidos en este
conjunto: r4–r7; BFF r2 es evidencia parcial separada. No se reutilizaron permisos. Evidencia:
[ciclo Docker r4–r7](../evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

## Fuentes y ficha de esta actualización

Se consultó el registro local de la sesión, sus mensajes/aprobaciones/cierre, el estado
actual, [evidencia de fixtures](../evidencia/h3req1_helper_docker_fixture_2026-10-08.md),
[revalidación de inputs](../evidencia/h3req1_revalidacion_hashes_2026-10-08.md), manifests,
fuentes BFF/test y workflow independiente. No se publica el registro privado completo.
Candidato: rama `feat/h3req1-sync-20261002`, baseline HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; el WIP es parte del candidato, no del HEAD.

Ficha constructor: solo documentación DOC/REL, consumida por índice/estado/continuación.
No cambio de contrato ni código. Preservar fuentes, cambios ajenos, original y reportes.
Agregar seguimiento compatible; sin deploy/contract. Rollback solo de estas adiciones.
Autoría documental dentro del traspaso solicitado; ninguna operación Docker/SQL/remota
ni JIT consumida en esta revisión. Pruebas documentales no equivalen a runtime.

## Ciclo posterior — UAT BFF y acceso Docker local — 2026-10-08

La UAT aislada BFF del paquete r2 pasó con Node `v20.20.2`, TypeScript `5.9.3` y
`{"result":"PASS","checks":60,"quotaCases":10}`. El permiso r2 se consumió en una única
ejecución; r1 falló antes de iniciar pruebas por acceso denegado al socket y no se repitió.
G08 sigue en 0 porque solo quedó acreditada la regresión BFF: faltan checks y revisión del
candidato final. El resultado posterior r4 es NO-GO por scanner; su permiso está consumido.
G03–G10 no cambian. Evidencia:
[ejecución BFF r1/r2](../evidencia/h3req1_bff_validation_access_2026-10-08.md).

## Resultado de la sesión analizada

Hubo trabajo técnico real, pero no se cerró otro gate completo hacia GO_LOCAL_PR.

- Se encontró/corrigió clasificación fail-open de controles CI; el helper contempla JSON
  malformado, rutas anterior/nueva en renombres, aprobación sobre SHA actual y límites.
- Se corrigieron scanner y regresiones para nombres especiales, NUL/binarios, `.lock`
  y contenido con forma de marcador de diff. Las correcciones actuales no están revalidadas.
- Primer paquete: 12 tests aprobados/1 fallido de fixture; no valida las fuentes actuales.
- r3: 19 tests aprobados/1 fallido; también fallaron comparador y scanner shell. Scope
  guard pasó sus casos (`ordinary=3|newline=1|controls=1|malformed=3`). No confundir el
  95% de pytest de ese intento con avance de H3 ni con PASS global del paquete.
- Se corrigieron el motivo del helper F2d, el registro duplicado del fixture y la salida
  del scanner. r4 está preparado con 13 archivos; no ejecutado ni autorizado según cierre.
- Se agregó barrera BFF: claves de cuota y gateway iguales producen 503 antes de efectos;
  logout mantiene limpieza. La regresión sintética fue escrita, no ejecutada. r4 no la incluye.
- Dos scans estáticos cubrieron snapshots delimitados; el más reciente registra 51/51
  rutas, cero findings confirmados y cuatro candidatos diferidos, cobertura parcial.
  No es cierre global de seguridad; el anterior advierte cambios durante la revisión.
- No se ejecutaron F2d contra F1, copia completa, smoke, C03 integrado, SQL ni remotos.
- La sesión analizada terminó bloqueada por aprobación r4 pendiente. Después se autorizó y
  consumió r4 con NO-GO por scanner. Esta nota conserva ese corte histórico y no concede r5.

## Verificaciones adicionales de este corte

1. En ese corte, paquete `/tmp/h3req1-helper-validation-29d8fff9-current-r4/inputs.sha256`:
   SHA `d915597d6eacb0a80e812e32c51b5c699ffb27e7c364501612cc576951404491`.
   Comparado con candidato actual: 13/13 coinciden. No se ejecutaron sus suites.
2. Manifiesto `tests/h3req1-c03-f1-diagnostic-f2d-inputs.sha256`: 16/17 coinciden.
   Diverge `tests/h3req1_c03_docker_daemon_identity_f2d.py`, corregido después de preparar
   el JIT. Antes de F2d se deben renovar manifiesto/pins, revisión y aprobación exacta.
   No ejecutar el F2d antiguo ni atribuirle autorización por r4.
3. C03 SQL: 41/41 entradas recalculadas coinciden; sin ejecutar SQL.
4. Hashes actuales workflow/BFF coinciden con los dos deltas de la nota C02 70/72.
   SQL/wire histórico se conserva en su alcance; el BFF actual y CI deben revalidarse.
5. `git diff --check` no presentó errores en el corte rastreado. No acredita lógica.

## Métrica fija de cierre local

Cada gate completo vale 10 puntos. Preparado/corregido/parcial/pendiente vale 0 hasta
cumplir todos sus criterios y existir evidencia vigente. Una regresión retira puntos
del gate afectado. No sumar porcentajes de tests de suites distintas ni asignar puntos
por archivos, scans repetidos, hashes, sintaxis o permisos solicitados.

| ID | Gate agrupado para seguimiento | Anterior | Actual | Evidencia o trabajo faltante |
|---|---|---:|---:|---|
| G01 | SQL/wire C02 de gateway/cuotas, alcance histórico preservado | 10 | 10 | SQL/harness aplicables conservados; no incluye BFF nuevo ni workflow actual, que van en G08/G10. |
| G02 | Suspensión/resume SQL C03 | 10 | 10 | PASS SQL v3 y 41/41 inputs; no equivale a integrado. |
| G03 | Tooling completo validado | 0 | 0 | r4: pytest 20/20 y proyector/scope PASS; r7: regresión scanner PASS. Faltan linters y revisión pertinente. |
| G04 | Diagnóstico local suficiente/F1 | 0 | 0 | F2d aprobado/consumido una vez y NO-GO por peer no acreditado; no repetir. Requiere nuevo método de identidad autorizado y evidencia/disposición F1. |
| G05 | Copia completa aislada | 0 | 0 | Snapshot íntegro verificado, sin secretos ni dependencias históricas. |
| G06 | Arranque real Pages/workerd | 0 | 0 | Healthz real tras copia PASS. |
| G07 | C03 integrado real | 0 | 0 | Secuencia completa suspensión/datos/finalizadores/recuperación. |
| G08 | Candidato final: checks/BFF/revisión | 0 | 0 | UAT HMAC r2 PASS; faltan checks finales y revisión independiente sin graves abiertos. |
| G09 | Aceptación final y trazabilidad | 0 | 0 | UAT 144/144 sin retries, onboarding 10/10, cliente/pilares/disposiciones/grafo. |
| G10 | CI independiente efectivo y paquete PR | 0 | 0 | Required PR/review y `security-audit` confirmados; falta instalar desde base confiable y requerir el status independiente `Protected Workflow Integrity` en las tres ramas. Falta review humano y plantilla PR completa real. |
| Total | Gates completos / 10 × 100 | **20%** | **20%** | **Delta de cierre: 0 puntos porcentuales.** |

Comparación retrospectiva con la misma definición en ambas sesiones; antes no existía
una métrica contractual porcentual. Los pesos iguales no representan duración comparable.
Conclusión: avance de ingeniería comprobable, cierre completo estancado en esta sesión.
El primer incremento medible será G03 a 30% cuando su alcance completo esté acreditado,
no al aprobar r4 ni si r4 deja linters/review obligatorios pendientes.

Seguimiento remoto separado: D01–D14 sobre el artefacto final Development actual:
0/14 casos acreditados en estos ciclos = 0%. Resultados históricos Auth/MFA no cierran
esa matriz. Integración/despliegue/ventana son prerrequisitos, no casos D aprobados.
100% local no implica deploy ni 100% remoto. Todos los gates vinculantes siguen aplicando,
aunque una exigencia no aparezca desglosada individualmente en estos grupos.

## Plan priorizado y decisiones

1. r7 está consumido y PASS; no repetirlo. Preparar un paquete Docker separado y congelado
   para linters/regresiones restantes y revisión de herramientas. Ejecutar solo tras su
   aprobación exacta; no instalar herramientas ni reutilizar r7.
2. La UAT BFF r2 ya pasó en su paquete aislado (60 checks); mantenerla como evidencia
   parcial y no repetirla. Revalidar sus bytes junto con los checks finales del mismo
   candidato antes de G08; no inferir bindings remotos.
3. Tras helpers válidos, usar F2d renovado (17/17), reconciliar ejecución host del
   diagnóstico con AGENTS y solicitar JIT fresco/residuales. Obtener discrepancia F1.
   Si falla identidad, alternativa local verificable con decisión explícita, no más
   intentos equivalentes sin nueva información. Resolver/disponer F1 expresamente.
4. Preparar stack nuevo condicionado copia -> smoke -> integrado, con SQL fixture,
   recuperación, bootstrap/egress, recursos/límites/retries y evidencia definidos.
   Aprobar antes de ejecución. No limpiar Docker como precondición; limpieza exacta aparte.
5. Ejecutar checks/UAT/revisión/documentación finales sobre candidato fijado. Conservar
   suites intactas; revalidar deltas. No agregar endurecimientos opcionales que vuelvan
   obsoletos paquetes durante el cierre. Defectos bloqueantes demostrados sí se corrigen.
6. El candidato CI está validado: el workflow trusted local es WIP y no está instalado en
   ninguna rama remota; las tres solo requieren `security-audit`. Preparar una única solicitud
   por objetivo para introducir el workflow trusted mediante la ruta protegida y, una vez que
   cada rama emita el status, requerir `Protected Workflow Integrity` junto con el check actual.
   La edición de branch protection es un write protegido y requiere instrucción humana
   separada; no inferir enforcement desde configuración local. La regla de aprobación del
   último push también difiere en `main` y queda para decisión de política aparte.
7. Tras GO_LOCAL_PR: autorizaciones separadas commit/push/PR, merge, despliegue y ventana
   Development. Ambiente Free compartido, Pro autoritativo intacto; D01–D14 literales.

Pregunta inmediata: ninguna para r7; su autorización exacta se recibió y consumió con PASS.
La siguiente aprobación se solicitará solo después de fijar el paquete restante de
lint/review, incluidos inputs, comandos, imagen, límites y manifiesto. No se reutiliza r7.

CI: integración continua. BFF: servidor intermedio que mantiene sesión fuera del navegador.
HMAC: firma con clave secreta; las dos claves tienen funciones distintas. JIT: aprobación
específica antes de operación protegida. UAT: pruebas de aceptación de usuario.

## Prompt para Luna 6 Max

Versión fusionada: plan, tablero porcentual y espera de aprobaciones de hasta 30 minutos.
Preferir reanudar la sesión `01a11c04-d49d-7dc3-8201-0a03535a7508`; una sesión nueva debe
leer este mismo prompt completo y comprobar resultados/permisos actuales. La instrucción
de espera no aprueba operaciones distintas de la que el usuario autorice expresamente. No
requiere pegar un segundo bloque adicional.

```text
continua H3REQ1 en ejecución por ciclos hasta GO_LOCAL_PR acreditado. Necesito cerrar
local e iniciar después las pruebas remotas con sus autorizaciones. Trabaja en
/home/romel/src/studiamatch-h3req1-sync-20261002; conserva original y todo WIP.

Empieza con tareas/gates y ficha constructor. Lee AGENTS aplicables, encabezado vivo,
índice y protocolo técnico, atestación sanitizada cliente/adendas, plan único de cierre
2026-10-04, ruta ejecutable 2026-10-06 y esta nota:
.context/operaciones/h3req1_avance_por_gates_y_prompt_luna_2026-10-08.md
Usa el prompt anterior Luna del 2026-10-08 para detalles aún aplicables; esta nota
actualiza resultados, prioridades y métrica, sin reemplazar autoridades ni D01–D14.
No releves todo el proyecto ni repitas scans/suites intactas por rutina.

Confirma rama feat/h3req1-sync-20261002 y baseline
4eb4d877a50b012bb630a129bd0c74482c33be9c. HEAD no representa el WIP completo.
Preserva ambos checkouts, evidencia y cambios ajenos. No accedas a .env*, tokens,
documento privado ni tests/h3req1-c03-bootstrap/node_modules/.deno sin autorización.

TABLERO OBLIGATORIO: usa G01–G10 exactamente como esta nota. Cada gate íntegro
10 puntos; parcial/preparado 0. Línea base 20%, sesión anterior 20%, delta 0.
No es porcentaje de código ni esfuerzo. Publica tras cada ciclo:
porcentaje antes/después, gates cambiados, evidencia, permisos consumidos,
siguiente acción/decisión. Retira puntos si se invalida evidencia; conserva historia.
No cuentes hashes, archivos, scans, aprobación ni 19/20 pytest como cierre.
Remoto separado: D01–D14 actual 0/14; no mezclar con métrica local.

SITUACIÓN ACREDITADA:
r3 es historia (19 pytest PASS/1 FAIL; regresión de proyector y scanner FAIL; scope guard
PASS en su alcance). r4 se ejecutó una vez: manifiesto 13/13, pytest 20/20, proyector y
scope guard PASS; scanner FAIL. r5/r6 localizaron que el `grep` falso no arrancaba bajo
`/tmp noexec`. r7 separó el ejecutable en `/exec-fixture`; el usuario aprobó el paquete
exacto y la única ejecución pasó manifiesto 3/3 y regresión scanner, exit 0. r7 está
consumido; no heredar permisos ni repetir ejecuciones consumidas. G03 aún requiere lint/review.
C02 no-C03 70/72 por workflow/BFF; SQL/wire intacto conserva alcance histórico.
C03 SQL 41/41. Revalida inputs sin repetir SQL innecesariamente.
Scan actual: 51/51 rutas, cero findings confirmados, cuatro diferidos, cobertura parcial;
no equivale a aprobación global ni aplica a futuros deltas automáticamente.
BFF nuevo rechaza claves HMAC iguales con 503 antes de cuota/RPC; UAT BFF r2 pasó 60
verificaciones/10 casos de cuota, sin acreditar bindings remotos.
F2d no ejecutado sobre F1. Su manifiesto actualizado verifica 17/17 y los fixtures
sintéticos del helper pasaron dentro de Docker r4; la revisión estática/JIT r2 tienen pins
renovados, pero requieren aprobación fresca del diagnóstico host y sus residuales. F1 sigue
sin control discrepante identificado. No ejecutar pins/JIT anteriores.

ORDEN DE EJECUCIÓN:
1) r7 está consumido con PASS y queda registrado en evidencia. No repetirlo ni ampliar
   su alcance.
2) Completa linters/regresiones/revisión de tooling pertinentes para cerrar G03. Prepara
   un paquete Docker separado y congelado si hace falta ejecución adicional; no instales
   herramientas ni uses pruebas de host como sustituto.
   No instales herramientas ni ejecutes comandos de desarrollo en host; prepara
   un paquete Docker separado si hacen falta checks adicionales, con fuentes,
   dependencias, comandos y límites fijados antes de pedir su aprobación.
3) Helper F2d validado sintéticamente en Docker; manifiesto 17/17, revisión/JIT r2
   renovados. La identidad real del daemon requiere aprobar el JIT exacto, el auxiliar
   Python en host Linux según reconciliación con AGENTS y los dos residuales MEDIUM.
   Solo entonces acredita identidad y lee metadata allowlisted del F1 exacto. Guarda
   nombres discrepantes y corrige sin quitar aislamiento. Si no acredita motor, presenta
   alternativa local concreta y decisión, sin instalar/reconfigurar implícitamente.
4) Prepara JIT de stack coherente condicionado: copia completa -> smoke real
   Pages/workerd -> C03 integrado real con Edge/PG17/PostgREST. Recursos, pins,
   SQL fixture, bootstrap/egress, límites/retries, fallos y recuperación definidos.
   Copia read-only desde candidato a trabajo aislado, sin env/cache/deps antiguos;
   no tocar web/out original ni montar socket. No avanzar tras FAIL ni repetir
   todo el drill por un fallo de arranque. No presentar SQL/VM/mock como integrado.
   Limpieza no es precondición; inventario/evidencia/JIT destructivo aparte.
5) Cierra checks del mismo candidato, UAT 48×3=144 sin retries/onboarding 10/10,
   revisión independiente @security-auditor, atestación cliente, seis pilares,
   grafo y documentación. No HIGH/CRITICAL abiertos; waiver aprobado completo.
   Agrupa disposiciones warnings/PyPDF2/cuatro live; no inventar aceptación.
   Conserva Romel/2026-11-03 para braces/priceMin como seguimiento, no waiver.
6) Prepara CI independiente desde base confiable. Solicita lecturas/configuración
   remotas necesarias. Verifica enforcement Protected Workflow Integrity y
   review humano del SHA final. YAML/test/helper/scan no lo prueban. Prepara PR
   con plantilla y resultados reales, inventario/rollback; no publicar aún.
7) Acreditado GO_LOCAL_PR, pide por separado commit/push/PR, merge y despliegue/
   ventana Development. Free aqrldlmlszjtgpqiegaa comparte Dev/Cert; Pro
   xwhtiqmboljkshrtviyw permanece autoritativo e intacto. Expand compatible ->
   Worker/DO -> Edge -> Pages/BFF -> gateway con consumidores listos. Identifica
   SHA/host/deploy/bindings/schema, preserva cuenta MFA y usa onboarding separado.
   Ejecuta D01–D14 solo bajo ventana aprobada. Certification/Production fuera.

DISCIPLINA PARA EVITAR ESTANCAMIENTO:
Congela cada paquete antes de solicitar aprobación. No edites sus inputs durante
la espera; prepara otros deltas en paquetes separados y registra qué candidato
validan. Si un defecto bloqueante exige cambiarlo, retira la solicitud anterior,
actualiza pins y presenta una única solicitud actual sin confundir versiones.
No introducir mejoras opcionales durante cierre; sí corregir bloqueantes
demostrados y revisar consumidores/pruebas afectados.

APROBACIONES: ESPERA HASTA 30 MINUTOS
Tras presentar una solicitud completa y concreta, permite hasta 30 minutos para
mi respuesta. Mientras esperas, completa trabajo independiente ya autorizado.
Mantén congelados inputs/comandos/alcance del paquete pendiente. No gastes un
permiso solicitado para otra versión. Si debes sustituir el paquete, explica
el motivo y reemplaza expresamente la solicitud anterior con pins nuevos.

Si no queda trabajo independiente y hay herramienta de espera disponible,
espera con pausas de hasta 60 segundos, revisando si llegó una respuesta entre
pausas. No hagas bucles de consultas/hashes ni mensajes repetidos para simular
avance. Esta espera es para decisión humana; no la presentes como prueba de que
un proceso Docker o un job siga ejecutándose.

Al llegar mi aprobación, verifica paquete exacto, alcance y que no esté consumida;
ejecuta lo autorizado sin repetir la misma pregunta. Si la respuesta es ambigua,
aclara únicamente la parte necesaria. Mi ausencia nunca es aprobación ni rechazo.
Si pasan 30 minutos, conserva la solicitud pendiente y entrega un punto concreto
de reanudación, con porcentaje actual y operación que espera permiso. No recrees
el paquete ni declares GO por haber esperado. Si la interfaz interrumpe la espera,
registra dónde retomar sin afirmar que seguirá ejecutándose en segundo plano.
Este prompt no garantiza disponibilidad continua de la sesión o de la aplicación.

Tras un ciclo que no cierre gate, explica si produjo nueva evidencia accionable,
corrección pendiente de validar o ninguna progresión. Repetir estado/hashs/planes
no aumenta porcentaje. Si falta permiso, presenta una pregunta concreta una vez,
con recomendación, alternativas y causa AGENTS; no repitas aprobaciones mientras
no cambia alcance. Esperar respuesta no es aprobación; respeta stop-on-failure.
Continúa trabajo independiente autorizado. No terminar en runner preparado si
la ejecución ya fue autorizada. No declarar GO anticipado ni reducir el objetivo.
Explica abreviaturas y decisiones en lenguaje sencillo. Resultado final: GO con
evidencia por gate; GO local y aceptación remota siempre separados.
```

## Addendum de corte — F1 `INSPECT_TEMPLATE_ERROR` — 2026-10-08

El JIT `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-READ-ERROR-CLASSIFICATION-ONCE-20261008-V1`
(`ce424f43901752cab76d9bcad88ceca05eb94a65790e4750a3b5f71f4b417395`) fue aprobado y
consumido por una única invocación en Ubuntu WSL como `romel`, sin sudo. Resultado reportado:

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=INSPECT_TEMPLATE_ERROR
```

Fase detenida: `f1-container-read`. El runner termina exit 1 por esa rama; no expuso el código
numérico del CLI. Falló el predicado del `docker inspect` F1 fijado con el formato allowlisted.
El clasificador reconoció un marcador de template; no permite distinguir parseo de evaluación
ni el campo/token concreto. No existe corrección segura demostrada: no se cambia formato,
Docker, imagen ni contenedor y no se repite el JIT. G03/G04 permanecen 0/10; r9 y etapas
dependientes detenidas. Total G01–G10: 20%, delta 0; D01–D14: 0/14.

Antes de cualquier nuevo diagnóstico, el test sintético mínimo debe separar errores de parseo
y evaluación de campo en el clasificador, comprobar códigos allowlisted distintos y ausencia
de texto crudo en salida/persistencia. Si la revisión demuestra una corrección de formato,
probar además el formato exacto con fixture tipado de 25 campos y orden estable. Ese test no
acredita el objeto real ni autoriza lectura: cualquier invocación requiere nuevo JIT.

El helper V2 que separa parseo, evaluación y marcador ambiguo, runner y aserciones sintéticas
ya están preparados en `tests/h3req1_docker_peer_substep_diag/`; no se ejecutaron. El JIT V2
[test + una lectura F1 + r9 condicional](jit_h3req1_docker_desktop_wsl_f1_classifier_v2_and_r9_once_2026-10-08.md),
SHA-256 `c2f9414cea67402af76727b3c240982d1c264252569ab94aea9dedc47c687a66`, espera aprobación.
No cambiar el formato F1 ni reutilizar el JIT consumido.

Bootstrap CI V3 (`.context/evidencia/h3req1_ci_bootstrap_minimal.patch`, SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`) sigue aislado y no
publicado. Revisión estática `hold_for_evidence`; no hubo pytest/actionlint/Docker/GitHub real,
ni cambios de reglas o Pages. Se conserva como parcial separado; G10 no cierra. Continúan
pendientes la observación real del check y la seguridad de promoción/Pages. Referencias:
[matriz y evidencia del corte](../evidencia/h3req1_corte_matriz_aceptacion_f1_2026-10-08.md),
[paquete CI](h3req1_ci_bootstrap_package_2026-10-08.md).

## Addendum de corte — pruebas sintéticas V2 fallidas; fixture corregido — 2026-10-09

El JIT V2 anterior `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-AND-R9-ONCE-20261008-V1`,
SHA-256 `c2f9414cea67402af76727b3c240982d1c264252569ab94aea9dedc47c687a66`, fue aprobado y
consumido una vez en Ubuntu WSL2 como `romel`, sin sudo. Resultado sanitizado: endpoint `OK`,
`classifier-synthetic-tests/SYNTHETIC_TESTS_FAILED`; wrapper exit 1. Stop antes de lectura F1
y r9. No reintentar.

La revisión estática encontró que la prueba de `main()` no sustituía `run_synthetic_tests()`;
`main()` intentaba lanzar Docker anidado desde el contenedor pytest efímero. Se añadió no-op a
esa orquestación únicamente en el fixture; el runner exterior mantiene los tests V2 reales. No
se ejecutó la corrección. La salida pytest se había suprimido, por lo que el defecto explica una
causa suficiente, pero no se afirma que fuera el único fallo. Ver [evidencia del JIT y límite](../evidencia/h3req1_c03_f1_classifier_v2_synthetic_failure_2026-10-09.md).

El nuevo JIT corregido + lectura F1 + r9 condicional
([paquete](jit_h3req1_docker_desktop_wsl_f1_classifier_v2_fix_and_r9_once_2026-10-09.md),
SHA-256 `1cb4ad0dbf3f3928c88a62441c2806c8eff2358ff3970c1f07d5a787d8fd29b5`) requiere aprobación
exacta. Los JIT consumidos no se repiten. G01–G02=20/20; G03–G10=0/80; total 20%, delta 0;
D01–D14=0/14. No hay GO.

## Addendum de ejecución — pin discrepante; nueva invocación pendiente — 2026-10-09

La aprobación del JIT `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-FIX-AND-R9-ONCE-20261009-V1`
(SHA-256 `1cb4ad0dbf3f3928c88a62441c2806c8eff2358ff3970c1f07d5a787d8fd29b5`) se consumió. Exit
1 en `classifier-v2-r9-preflight/DIAGNOSTIC_RUNNER_HASH_MISMATCH`; no endpoint, sintéticos,
F1, Docker API ni r9. El runner combinado declaraba `1fe0…` y el runner diagnóstico incluido
en el JIT tiene `97b5…`. Se actualizó solo ese pin; no se reintentó.

El usuario reportó aparte mismatch entre `web/package.json`/`web/package-lock.json` del origen y
la imagen staged de `studiamatch-dev`. No se inspeccionó, inició ni reconstruyó; la imagen queda
preservada y el reporte no prueba la causa del error de pin. Requiere resolver el gate del
runner antes de etapas locales; si una etapa futura necesita reconstruir ese contenedor, se
presentará una autorización específica agrupada para esa operación.

El patch CI V3 continúa preparado y aislado, SHA `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`;
su apply-check y revisión previos se conservan, sin nuevos tests Docker ni writes remotos. El
JIT de pin corregido, lectura F1 y r9 condicional está preparado en
[paquete nuevo](jit_h3req1_docker_desktop_wsl_f1_classifier_v2_pin_corrected_and_r9_once_2026-10-09.md)
y requiere autorización nueva. G01–G02=20/20; G03–G10=0/80; total 20%, delta 0; D01–D14=0/14.
No hay GO.

## Addendum de ejecución — synthetic V2 FAIL; clasificación preparada — 2026-10-09

El JIT pin-fix aprobado (`dbc58ec3dcc3ce7cacc83d84ec6689a16f1564ae40c0776607fba5e35371e79d`)
se consumió: endpoint `OK`, sintéticos `SYNTHETIC_TESTS_FAILED`, exit 1. F1 y r9 no se
alcanzaron. El error genérico no distingue el fallo del contenedor, framework, colección o
caso. No se conservó salida cruda; revisión estática no demostró una aserción rota.

Se añadió un verificador read-only del digest y un runner pytest que informa solo códigos
cerrados por caso; salida raw queda efímera. El
[JIT diagnóstico V2 + F1/r9 condicional](jit_h3req1_docker_desktop_wsl_f1_classifier_v2_synthetic_diagnostic_and_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-SYNTHETIC-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`,
SHA-256 `708cb4210fb59df7f85d1f69c83f22007304b99a6414496ea0c9268d8bb32d26`, requiere una
autorización nueva. No habrá retry ni acceso/rebuild de `studiamatch-dev`.

CI V3 sigue separado, con patch `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`;
sin pytest/actionlint/remote run. G01–G02=20/20, G03–G10=0/80, total 20%, delta cero;
D01–D14=0/14.

## Addendum de ejecución — clasificador identificó el caso sintético `main()` — 2026-10-09

El usuario aprobó una invocación del JIT V2 diagnóstico
(`708cb4210fb59df7f85d1f69c83f22007304b99a6414496ea0c9268d8bb32d26`). Se ejecutó una vez
como `romel` en Ubuntu WSL interactiva, sin sudo. Salida: endpoint `OK`, digest de imagen
sintética `OK`, y `classifier-synthetic-tests/V2_MAIN_SANITIZATION_FAILED`; exit 1. El caso
`test_v2_main_emits_only_sanitized_template_error` reportó fallo, pero el código cerrado no
identifica exit, salida, secreto, excepción o clasificador. No se retuvo salida raw. F1/r9 no
se ejecutaron; se detuvo la secuencia dependiente. Sin pull/rebuild/cambios Docker ni acceso a
`studiamatch-dev`.

El único cambio de prueba preparado etiqueta tres predicados con strings constantes y añade
un runner que traduce etiquetas permitidas a códigos cerrados. No se ejecutaron esos nuevos
tests. El paquete agrupado [JIT V3 con F1/r9 condicional](jit_h3req1_docker_desktop_wsl_f1_classifier_v3_main_assertion_and_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V3-MAIN-ASSERTION-AND-R9-ONCE-20261009-V1`,
SHA-256 `1aa957146fbe98b6bec2e04c9d9cbc67414cbb4a9dbe3af138d53b592f8af178`, requiere aprobación
exacta. La primera solicitud con SHA `a7fe73ac…` quedó obsoleta antes de ejecutarse: revisión
estática encontró y corrigió la ruta fija al entrypoint sintético V2. Una falla volverá a
detenerse sin retry.

La matriz de cuatro ajustes y el patch CI V3 no ganan cobertura con este resultado. CI sigue
aislado; no se ejecutaron pytest/actionlint ni checks remotos. G01/G02=20/20, G03–G10=0/80;
total **20%**, delta cero; D01–D14=0/14. Sin GO.
