# H3REQ1 — prompt único de continuación para Luna 6 Max

Fecha: 2026-10-08. Uso: pegar el bloque siguiente en una nueva sesión de Luna 6 Max.
Contexto: [hallazgos detallados](../evidencia/h3req1_analisis_sesion_01a11a7e_2026-10-08.md).
Autoridad: [estado vivo](../estado_del_proyecto.md) y [AGENTS](../../AGENTS.md).
Este prompt no es resultado, JIT, waiver ni autorización de operaciones remotas.
El [plan único](plan_cierre_integral_h3req1_2026-10-04.md) conserva los gates y D01–D14;
la [ruta vigente en el corte 2026-10-08, ahora archivada](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md) conserva su navegación.

```text
continua con H3REQ1 en ejecución. Trabaja hasta acreditar GO_LOCAL_PR y dejar
habilitada la ruta real para iniciar las pruebas remotas Development. Si recibes
las aprobaciones necesarias durante esta misma sesión, ejecuta la integración,
despliegue y ventana remota; GO_DEVELOPMENT_REAL exige D01–D14 aceptados.

No entregues otro plan equivalente ni cierres en "runner preparado". Mantén ciclos
de analizar -> implementar -> validar -> revisar -> convertir hallazgos en tareas
-> corregir -> revalidar. Un intento fallido detiene solo su etapa dependiente:
diagnostica y corrige dentro del mismo ciclo autorizado; no abandones el objetivo.
Cuando falte una decisión o aprobación, pregunta de forma clara y espera la
respuesta para la acción dependiente; continúa con trabajo independiente autorizado.
No declares GO sin evidencia ni rebajes gates para satisfacer el objetivo.

1. PUNTO DE PARTIDA Y LECTURA FOCALIZADA

Candidato: /home/romel/src/studiamatch-h3req1-sync-20261002
Rama esperada: feat/h3req1-sync-20261002
Baseline HEAD: 4eb4d877a50b012bb630a129bd0c74482c33be9c
Original preservado: /home/romel/src/studiamatch
Rama original histórica: feat/h3req1-development-remote-tests
HEAD original histórico: 7650093b05a820e8e6faf9ec711e12fab8b50398

Antes de editar, lee AGENTS aplicables, encabezado vigente de
.context/estado_del_proyecto.md, .context/indice.md, la entrada técnica y
protocolo constructor, la atestación sanitizada cliente del 2026-10-01 y adendas,
el plan de cierre integral del 2026-10-04 y la ruta ejecutable del 2026-10-06.
Lee .context/evidencia/h3req1_analisis_sesion_01a11a7e_2026-10-08.md y solo las
evidencias adicionales que resuelvan una dependencia. Usa los encabezados vigentes;
los textos históricos inferiores y los JIT consumidos no autorizan ejecución.

Empieza listando tareas concretas y gates. Confirma rama/HEAD/WIP, clasifica el
delta y presenta ficha de contratos, consumidores, evidencia preservada/a renovar,
transición/rollback y permisos. HEAD no identifica el WIP completo. Preserva ambos
checkouts, archivos ajenos, secretos y evidencia. No accedas a
tests/h3req1-c03-bootstrap/node_modules/.deno sin instrucción humana específica.
No leas .env*, documentos privados ni sesiones/token reales para inventariar.

2. QUÉ NO REABRIR Y QUÉ SIGUE SIN PROBAR

C02 v4 registró PASS SQL/PostgREST/cuotas/gateway/replay/concurrencia; la sesión
anterior comprobó sus 72 inputs no-C03. C03 SQL v3 registró PASS de suspensión/
resume persistente/fail-closed; sus 41 inputs coincidían. Revalida hashes sin
ejecutar suites. Conserva resultados si inputs/contratos siguen aplicando;
explica cualquier cambio y renueva solo la evidencia afectada.

F1 creó el contenedor y falló antes de start; el control discrepante no quedó
registrado. ID exacto:
54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9
F2b falló canonicalidad, F2c falló identidad del proceso; ninguno leyó F1 ni llamó
Docker API. Ambos permisos están consumidos. F2c no conserva el submotivo.
No deduzcas proxy, fallo de Docker, ownership, mounts o imagen por analogía.
D4/J3 demuestra una expectativa errónea sobre tmpfs en otro ensayo, no la causa
F1/S1. D3 fue logging inválido; S1 falló la copia antes de npm/workerd; R4 falló
healthz antes de PG17/SQL. Preserva todos esos resultados.

Scanner, comparador y scope guard cambiaron localmente; faltan sus regresiones,
linters y revisión en Docker. PASS anteriores de 287 tests/4 skips y UAT/onboarding
son antecedentes, no aceptación del candidato final. CI independiente efectivo
sigue pendiente. No conviertas hashes o sintaxis en PASS runtime.

3. RESOLVER PRIMERO LA DEPENDENCIA DE F2D

F2d propone SO_PEERCRED para identificar directamente el proceso de la conexión
local, con causas de fallo sanitizadas. Está preparado, no autorizado ni ejecutado.
Lee su manifiesto y revisión estática del 2026-10-08. SHA del JIT en este corte:
f662d26783c9bb09d6cef2688da6bbf55e725dcc7fc77b92472ba0dc83a6c02e
Compara pins actuales; cualquier cambio exige nuevo paquete/pins/aprobación.

Resuelve antes de pedir ejecución: la revisión exige validar helper/parser en
Docker, pero se intenta acreditar ese mismo Docker. El runner llama python3 en
el host para ver el socket/proceso; reconcilia explícitamente ese contexto con
AGENTS. No presupongas una excepción ni cambies visibilidad al moverlo a Docker.
Prepara una validación aislada con fixtures controlados, positivos/negativos,
sin acceso a Docker API ni secretos. Define dónde corre y cómo obtendrá permisos.
Si hace falta excepción o entorno alternativo, presenta opciones concretas y
pide decisión humana antes de ejecutar. No instales/reconfigures un motor implícitamente.

Después de validar y revisar, prepara el JIT coherente de diagnóstico: comandos,
inputs/hashes, recursos exactos, lecturas permitidas, límites/timeout/retries,
egress, fallo y recuperación. Solicita aprobación fresca y aceptación expresa
de los residuales: Docker CLI procesa brevemente el objeto inspect completo en
memoria; el mismo usuario local podría operar fuera del runner. Explica ambos
en lenguaje sencillo; no heredes su aceptación de F2b/F2c.

Solo tras identidad acreditada lee la metadata permitida del F1 exacto y registra
nombres de controles discrepantes, sin valores sensibles. Corrige lo demostrado
con comparación estructurada, tmpfs/mounts correctos e identidad de imagen por
ID inmutable. Incluye regresiones de formatos observados y casos negativos.
Mantén aislamiento; no suprimas controles para conseguir PASS.

Si el nuevo método falla, conserva causa/fase/exit sanitizados y ofrece una
alternativa local concreta. No encadenes diagnósticos equivalentes sin información
nueva. Un entorno aislado alternativo requiere alcance aprobado; no explica por
sí solo F1. Cualquier disposición de esa investigación debe ser explícita.

4. STACK LOCAL Y C03: EJECUTAR EN ORDEN, SIN REPETIR TODO

Prepara un paquete JIT de stack nuevo por objetivo, con etapas condicionadas:
copia completa -> smoke real Pages/workerd -> C03 integrado. No continues una
etapa si falla la anterior. Reutiliza runners existentes con cambios mínimos.

Candidato como fuente read-only; copia de trabajo independiente. Excluye .env*,
sesiones, secretos, caches y dependencias históricas. No montes el socket Docker
en el runtime ni modifiques web/out original. Fija versiones/imágenes/lockfiles
y dependencias transitivas; delimita descargas/bootstrap y bloquea egress externo
después. Loopback donde proceda. PG17 es fixture desechable, nunca DB operativa.

El JIT debe cubrir recursos/nombres/labels, creación, SQL/recuperación de fixture,
límites, timeout, retries acotados, outputs recuperables y manejo de fallo.
No ejecutar SQL, recursos ni recuperación antes de aprobación expresa.

Comprueba copia completa: allowlist, paths/symlinks, permisos, extracción sin
restaurar ownership, hashes interiores y controles. Registra por separado exits
de productor, receptor y verificador, con errores sanitizados útiles.
Solo tras PASS arranca Pages/workerd hasta healthz, antes de añadir DB/Edge.
Si falla arranque, diagnostica ese componente sin repetir el drill completo.

Tras smoke PASS ejecuta C03 con Pages/workerd, Edge Runtime, PG17 y PostgREST reales:
normal -> reserva previa -> suspensión coordinada -> rechazo de nuevos iniciadores
y dispatcher -> limpieza de cookies/chunks -> finalizadores in-flight con efecto
único -> conservación de datos/auditoría/publicación/último admin -> rechazo de
drift -> resume persistente -> recuperación Edge/Pages -> smoke final.
Auth externo puede ser fixture explícito; sin correo remoto. No cuentes bootstrap
DB como nuevo PASS C02 ni VM/mock/SQL aislado como C03 integrado.

La limpieza no es precondición. Si se necesita, inventaría bajo permiso IDs,
labels/mounts/propiedad, preserva evidencia y pide JIT destructivo separado para
la lista exacta. No prune global, limpieza por prefijos, reset/clean ni down -v
global. Preserva studiamatch-dev, ambos checkouts y recursos ajenos.

5. CANDIDATO FINAL: VALIDAR, REVISAR Y CERRAR HALLAZGOS

Prueba scanner limpio/hit redacted/errores lectura-escritura-grep/concurrencia y
cleanup propio. Prueba comparador y scope guard: paths permitidos/rechazados,
errores Git/filtro y paths vacíos; actionlint/ShellCheck. No root para reparar
temporales ajenos ni allowlists indiscriminadas.

Inventaría código, SQL, vendor, tests y trazabilidad para PR; excluye generados,
caches y privados sin borrarlos. SQL nuevo conserva JIT de autoría/ejecución.
En Docker, sobre el mismo candidato, ejecuta checks pertinentes: pytest controlado,
TypeScript, ESLint, audits dev/prod, scanner, H2 writer scan, builds normal/mock
con fixture público elegible y regresiones público/SDK/BFF/Edge/cuotas/suspensión.
Renueva SQL/wire solo por inputs/contratos afectados y justifica reutilización.

UAT final: 48 casos × 3 viewports = 144 ejecuciones/capturas, cero retries,
onboarding 10/10. Si cobertura cambia, explica delta y ejecuta todos los casos
aplicables; no ajustes conteos para aparentar continuidad. La UAT r11 original
se preserva como antecedente, no valida el artefacto final.

Invoca revisión independiente @security-auditor conforme AGENTS, con alcance y
evidencia precisos. Convierte findings en tareas, corrige y revalida por impacto.
No cierres con HIGH/CRITICAL. Waiver requiere causa/evidencia/owner/riesgo/
vencimiento y aprobación humana. Agrupa decisiones pendientes de warnings,
PyPDF2 y cuatro tests live; no inventes owner/aceptación/ejecución.
Conserva Romel y fecha 2026-11-03 para braces/priceMin: seguimiento, no waiver.

Actualiza estado/tarea/hito/evidencia y relaciones Obsidian. Valida grafo completo
vigente; 115/115 era otro corte. Separa manifiestos fuente/build/resultados para
evitar hashes circulares. Preserva fallos/historia. Verifica aceptación contra
atestación cliente y seis pilares con mediciones/límites reales; no derives
seguridad/rendimiento/escalabilidad globales de unit tests o documentación.

6. CI, GO LOCAL E INICIO REMOTO

CI es integración continua; PR, solicitud de incorporación de cambios. El control
independiente debe ser efectivo desde base confiable y tener review humano sobre
el SHA final. YAML local o check histórico no acredita enforcement. Prepara
bootstrap mínimo, pide lecturas/configuración remotas necesarias y ejecútalas
solo al aprobarse. Si es el último gate, trabaja únicamente en resolverlo;
no repitas suites intactas ni declares un GO alternativo.

Completa plantilla PR versionada con resultados reales, inventario incluido/
excluido, riesgos, transición y rollback. Commit/push/PR requieren instrucción
separada; merge otra. No hagas Git remoto implícitamente.

Prepara Development: expand DB compatible -> Worker/DO y configuración -> Edge
compatible -> Pages/BFF -> activar gateway solo cuando consumidores estén listos.
BFF es servidor intermedio que conserva sesión fuera del navegador; MFA es segundo
factor de autenticación. Preserva contratos aprobados y fase compatible/rollback.

Free Development/Certification: aqrldlmlszjtgpqiegaa; Pro autoritativo:
xwhtiqmboljkshrtviyw. No modificar Pro desde Free ni sincronizar datos operativos.
Documenta coexistencia Free; no uses admin.studiamatch.com para aceptación Dev.
Identifica SHA integrado, hostname aprobado, Pages deployment, Edge, Worker/DO,
schema/ledger/bindings. Preserva cuenta Auth+MFA; prueba transición al BFF sin
reset/reinvitar/reenrolar. Onboarding separado; reset requiere JIT propio.

Prepara y pide por objetivos coherentes integración, deploy y ventana UAT remota
con cuentas/fixtures/operaciones/cuotas/efectos/rollback. Tras aprobación ejecuta
literalmente D01–D14 del plan único; no inventes una matriz reducida. Evidencia
sanitizada por caso y artefacto; corrige/repite solo casos afectados autorizados.
Certification/Production/main/schedules/contract productivo quedan fuera.

7. COMUNICACIÓN Y SALIDA

Explica bloqueos/decisiones sin tecnicismos innecesarios y define abreviaturas.
Cada pregunta: qué falta, recomendación, alternativas, efecto, permiso exacto y
por qué AGENTS exige aprobación. Prepara antes todo lo autorizado y revisable;
no pidas aprobación campo por campo ni otro continua para el mismo ciclo local.

Mantén la sesión activa por ciclos hasta GO acreditado o una decisión humana
necesaria; una pregunta pendiente no es aprobación. Si la interfaz obliga a
terminar mientras falta permiso, entrega el paquete exacto pendiente sin afirmar
éxito. Nunca ocultes un fallo para cumplir la exigencia de GO.

Al acreditar GO_LOCAL_PR entrega identidad completa del candidato, evidencia por
gate, suites conservadas/renovadas, findings/disposiciones, aceptación/pilares,
permisos consumidos y paquete para inicio remoto. No confundir implementación,
pruebas, integración y despliegue. GO_DEVELOPMENT_REAL requiere aceptación remota
real completa; no significa promoción automática a Certification/Production.
```
