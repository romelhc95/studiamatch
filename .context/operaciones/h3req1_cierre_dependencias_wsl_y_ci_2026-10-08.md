# H3REQ1 — decisión Docker Desktop WSL y dependencias del bootstrap CI

Fecha: 2026-10-08. Candidato: `feat/h3req1-sync-20261002`,
HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.  
Autoridad: encabezado vigente de [estado](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md),
[paquete consolidado aprobado](h3req1_paquete_consolidado_cierre_local_luna_2026-10-08.md),
[diagnóstico y CI](../evidencia/h3req1_diagnostic_ci_prep_2026-10-08.md) y [bootstrap V3](h3req1_ci_bootstrap_package_2026-10-08.md).

## Tareas y gates de esta actualización

1. Resolver la ubicación válida del diagnóstico aprobado y preparar una alternativa segura
   para Docker Desktop WSL. Gate: una solicitud revisable, salida phase/código, alcance
   allowlisted y residual explícito; sin operación hasta aprobación nueva.
2. Completar las dependencias de bootstrap Protected Workflow Integrity. Gate: patch V3 y
   revisión existentes preservados; dependencias administrativas exactas; no instalar ni
   publicar ni modificar Pages/branch rules.
3. Corregir estado, tablero e índice. Gate: G01/G02 conservan PASS, G03–G10 abiertos, 20%,
   WIP/evidencia histórica intactos.

## Docker: respuesta a “¿dónde ejecuto?”

No existe un ID de contenedor donde ejecutar el JIT aprobado. Tampoco es correcto ejecutarlo
en Ubuntu WSL: Docker documenta que el Engine está en su distro `docker-desktop`, aislada de
Ubuntu, mientras WSL integration da acceso al CLI/socket. `sudo` en Ubuntu eleva dentro de
Ubuntu y no expone el `/proc` aislado del Engine. Entrar a la distro interna no está en el
alcance del JIT y el checkout fijado no está allí.

El JIT peer-substep aprobado, SHA-256
`e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173`, fue ejecutado una vez
desde Ubuntu WSL como root y terminó `phase=peer-identity|error_code=IDENTITY_MISMATCH`.
Queda consumido; no repetir. No acreditó la identidad esperada y detuvo el flujo antes de
consultar F1. `uname` confirmó WSL2; la discrepancia no demuestra que Docker esté mal ni
identifica cuál condición del peer difirió.

### Alternativa limitada preparada

El [JIT Docker Desktop WSL](jit_h3req1_docker_desktop_wsl_attestation_once_2026-10-08.md),
SHA-256 `9327c0ea163e47aa35c798442fec4230341b97fda1c19dfa811c492e3416fe4d`, corre como el
usuario normal en una terminal Ubuntu WSL donde existe el checkout. Verifica
localmente que el contexto `default` apunta exactamente al socket WSL documentado
`unix:///var/run/docker.sock`, consulta solo `.Server.Os` y acepta `linux`; solo entonces lee
volúmenes de la imagen fijada y F1 mediante la proyección ya revisada. No inspecciona `/proc`,
no exige EUID 0, no muta Docker y se detiene al primer error. Pruebas sintéticas están
preparadas y no ejecutadas; revisión estática manual completada.

Esta alternativa no demuestra PID/UID, ejecutable `dockerd`, namespaces ni integridad del
proceso. Vincula una configuración local conocida y una respuesta Linux del Engine con el F1
exacto. El usuario aprobó una invocación y aceptó el residual MEDIUM; informó que ejecutó el
bloque y que se cerró la ventana, pero no proporcionó las líneas de fase/código. La invocación
queda consumida. El runner emite solo stdout y no deja log en el checkout; sin recuperar esas
líneas no se puede evaluar endpoint/Linux ni F1 y G04 queda abierto. No reintentar este JIT.

El usuario indicó que preferiría reconstruir imágenes con los últimos cambios para obtener un
entorno limpio y evitar residuos. El flujo aprobado ya toma una copia aislada del candidato y
usa imágenes runtime por digest fijado; el código actual llega por esa copia/mount, no por
reconstruir la imagen base. r9 usa un contenedor efímero `--rm`; las fases C03 registran recursos
por ID y retiran solo recursos creados por este ciclo tras exportar evidencia. Los recursos
históricos quedan intactos. Rebuild/pull, cambio de digest o limpieza de recursos anteriores no
están incluidos en la aprobación actual y requieren una decisión/JIT agrupado si pasan a ser
requisito.

La autorización anterior ya fue recibida y la invocación se informó ejecutada. Si las líneas
sanitizadas siguen visibles en el scrollback restaurado de Windows Terminal, comparte solo
`phase=…|error_code=…`. No vuelvas a ejecutar el bloque. Si no se recupera la salida, no hay
evidencia para habilitar r9; una nueva captura requeriría preparar otro JIT agrupado y obtener
una autorización nueva.

El usuario confirmó que no puede recuperar el scrollback. El bloque V1 queda consumido, sin
resultado inferible. Se preparó una nueva solicitud agrupada, sin ejecución, en
[JIT output-capture](jit_h3req1_docker_desktop_wsl_output_capture_once_2026-10-08.md), ID
`H3REQ1-C03-DOCKER-DESKTOP-WSL-OUTPUT-CAPTURE-ONCE-20261008-V1`, SHA-256
`bbaa2242bf026f252864b4e476a60e9de2a8e327c0456d2b343b612402c61c92`. Mantiene la misma
lectura allowlisted y residual MEDIUM, captura solo líneas sanitizadas en una variable y espera
en una TTY; necesita aprobación nueva. Si da las tres fases PASS, r9 continúa bajo los límites
consolidados. Hasta entonces G04=0/10, G03=0/10 y total 20%.

## CI: lo que ya está acreditado y lo que falta

- MCP GitHub confirmó `owner.type=User` para `romelhc95/studiamatch`: repo de cuenta personal,
  público, no de organización/Enterprise. El usuario confirmó que no hay Actions policies
  creadas; Policy insights informa que el análisis de reglas requiere Enterprise. No se
  solicitan capturas repetidas.
- GitHub documenta para repos públicos una policy predeterminada de `pull_request_target`:
  hoy está en `evaluate`, así que los runs continúan; el enforcement anunciado es
  **2026-11-02**. No hace falta habilitar un evento hoy para hacer el bootstrap, pero antes de
  esa fecha se deberá crear una Actions event policy aplicable al repo que permita PRT, si
  PWI aún lo requiere. Mientras no exista un run real, no afirmamos que el workflow ya corre.
  Fuente primaria: [GitHub — securely using `pull_request_target`](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).
- El usuario confirmó Cloudflare Pages: proyecto vinculado a `romelhc95/studiamatch`,
  Production branch `main`, despliegues automáticos activos, include `*`, exclude vacío,
  root `web`, `npm install && npm run build`, salida `out`, comentarios de build activos,
  cache desactivado, build system v3, sin deploy hooks. El patch de cuatro rutas coincide con
  `*`; un PR/merge puede disparar build Preview/Production. El panel Deployments compartido
  muestra producción desde `main` y un Preview histórico de
  `feat/h3req1-development-remote-tests`. Esto confirma que existió un Preview para esa rama,
  pero no el modo exacto Preview branches ni el build del bootstrap.
- Cloudflare documenta que prefijar el mensaje de commit con `[CF-Pages-Skip]` omite ese
  deployment; no se ha probado en este proyecto. La opción de menor alcance es aplicar el
  prefijo al commit bootstrap y al título squash, verificar el comportamiento del PR antes del
  merge y detenerse si aparece una Preview inesperada. Si ese método no sirve, la alternativa
  requiere autorización agrupada para excluir solo las cuatro rutas exactas del patch en Build
  watch paths y observar el efecto antes del merge. No se fija el prefijo ni se cambian settings
  ahora. `cf-builds` no aparece entre las herramientas habilitadas para esta sesión.
- Preview branch control exacto (None/All/Custom) y merge queue sí/no en `desarrollo`,
  `certificacion` y `main` siguen sin confirmarse. Son las entradas administrativas pendientes
  para cerrar el camino del bootstrap y verificar la cobertura del evento. El deployment
  histórico no basta para inferir la configuración actual.
- La rama default y soporte de squash/merge/rebase están leídos; no hay PR/branch nuevo. Las
  reglas clásicas siguen exigiendo PR, 1 approval, stale dismissal, branch up-to-date y
  `security-audit`; el ruleset de updates permanece intacto. El check PWI todavía no existe
  ni está requerido.

## Próximo objetivo CI sujeto a permisos posteriores

El patch revisable es [V3](../evidencia/h3req1_ci_bootstrap_minimal.patch), SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`, desde base confiable
`4eb4d877a50b012bb630a129bd0c74482c33be9`. `git apply --check` y `git diff --check`
constan PASS en copia aislada. Revisión independiente `hold_for_evidence`, sin bypass de
código confirmado. No se ejecutaron pytest/actionlint/Docker/workflows y el patch no se aplicó
al checkout WIP.

Una vez acreditado Docker y completada la validación local del patch, la única autorización
de promoción debe agrupar el objetivo completo:

1. Crear PR de solo las cuatro rutas del bootstrap, con revisión humana independiente y flujo
   protegido existente; el commit de la rama y el título squash llevan `[CF-Pages-Skip]`;
   sin código de producto ni WIP colateral.
2. Verificar el skip de Preview antes del merge. Si aparece un build/deployment, detenerse y
   no integrar. La exclusión de watch paths de las cuatro rutas exactas es una alternativa que
   requiere incluirse expresamente en esa misma autorización. No se cambia ahora ningún
   ajuste Cloudflare.
3. Después de que el workflow exista, comprobar en GitHub el check exacto asociado al head
   vigente, los fallos sin review válida, review bot, stale head, avance de base con head
   estable y merge queue (si aplica).
4. Solo al observarlo en cada base, exigir `Protected Workflow Integrity` junto con
   `security-audit` en `desarrollo`, `certificacion` y `main`. Mantener reglas de aprobación,
   up-to-date, no-bypass, ruleset, force-push/deletion y bypass actor tal como están.
5. Antes del 2026-11-02, agrupar una escritura de Actions event policy a nivel repo para
   `pull_request_target` únicamente si el comportamiento observado/documentado sigue
   requiriéndolo. Sin cambios en secretos, deploys del producto, DB, branches directas o
   Production releases.

El patch no se promueve por este documento. Abrir/actualizar PR, alterar Pages/Actions/branch
protection y merge requieren aprobación humana separada y agrupada tras resolver las dos
entradas pendientes y validar el candidato localmente.

## Estado de gates y parciales preservados

| Gate | Estado | Evidencia/condición |
|---|---:|---|
| G01 | 10/10 | C02 histórico PASS. |
| G02 | 10/10 | SQL C03 v3 PASS, inputs 41/41. |
| G03 | 0/10 | pytest r4 20/20, proyector/scope y scanner r7 PASS parciales; r8 exit 126 antes de checks; r9 pendiente. |
| G04 | 0/10 | Peer-substep consumido con `IDENTITY_MISMATCH`; WSL V1 consumido sin salida; nuevo JIT de captura pendiente de aprobación; r9 y F1 sin evidencia. |
| G05 | 0/10 | Copia completa pendiente. |
| G06 | 0/10 | Pages/workerd healthz real pendiente. |
| G07 | 0/10 | C03 integrado pendiente. |
| G08 | 0/10 | UAT BFF r2 60 checks/10 casos de cuota PASS parcial; aceptación del candidato pendiente. |
| G09 | 0/10 | 144 ejecuciones visuales, onboarding 10/10 y revisión final pendientes. |
| G10 | 0/10 | Patch listo; run remoto, review, merge queue y required check efectivo pendientes. |
| Total | **20%** | G01–G02 completos; no crédito por documentación o revisión; no GO. |

D01–D14 sigue 0/14. No se repiten suites parciales intactas. No hubo Docker, tests,
modificaciones de configuración, push/PR/merge, DB, secrets ni deploy en esta actualización.
