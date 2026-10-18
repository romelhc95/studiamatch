# H3REQ1 — paquete consolidado de cierre local para Luna 6 Max

ID: `H3REQ1-CLOSE-LOCAL-ITERATIVE-20261008-V1`.
Estado: **PROPUESTA PREPARADA; NO APROBADA; NO EJECUTADA**.
Autoridad: [estado vivo](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md),
[plan único](plan_cierre_integral_h3req1_2026-10-04.md),
[tablero G01–G10](h3req1_avance_por_gates_y_prompt_luna_2026-10-08.md).
Ejecutor previsto: Luna 6 Max en una nueva sesión, leyendo esta nota completa.
El nombre del modelo no acredita capacidad ni resultados: los fallos observados son de
preparación/aislamiento y permisos, no evidencia de incapacidad del modelo.

## Ficha constructor y resultado solicitado

Preparar el ciclo de diagnóstico -> tooling -> copia -> arranque -> C03 integrado ->
checks/UAT -> revisión/evidencia para cerrar validación local del candidato. Componente
K14/tooling y DOC/REL, con consumidores BFF/Edge/SQL-fixtures/CI y runners existentes.
Preservar contratos de sesión HttpOnly, gateway firmado, claves distintas, cuotas, RBAC,
onboarding, publicación/auditoría y disponibilidad; no rediseñar negocio. Aceptación:
atestación sanitizada cliente y seis pilares según alcance probado, sin inferir globales.

Esta autoría solo añade documentación/navegación; no modifica runtime ni ejecuta tests.
Transición documental compatible; rollback retirando estas adiciones, sin revertir WIP.
El futuro ciclo mantendrá expand -> compatibilidad -> deploy -> contract según ambiente;
este permiso propuesto no incluye deploy/contract remoto. Preservar PASS anteriores en
su alcance, renovar deltas, conservar todos los fallos. No consumir permisos históricos.

## Identidad y punto de partida

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`.
- Baseline HEAD: `4eb4d877a50b012bb630a129bd0c74482c33be9c`; inventariar WIP por separado.
- Original preservado: `/home/romel/src/studiamatch`.
- Corte: 20% de gates completos; BFF r2 PASS, pytest r4 20/20, scanner r7 PASS.
- r8 consumido: exit 126 por raíz 0700 UID 1000 frente a contenedor UID 1001. No corrieron
  linters/checks. r9 corrige raíz a 0755 y reutiliza herramientas ya verificadas, sin descarga.
- F2d r2 está preparado, helper probado en Docker, inputs 17/17; motor real/F1 pendientes.
- C02 conserva SQL/wire histórico; BFF/workflow son deltas. C03 SQL conserva 41 inputs.
- GO_LOCAL_PR además exige CI independiente efectivo y revisión humana; no prometer GO
  si esos prerrequisitos externos siguen faltando.

## Propuesta de aprobación única: operaciones separadas en una respuesta

La futura respuesta debe identificar este ID y SHA de la nota, aprobar expresamente los
alcances A/B/C y la excepción de revisiones del siguiente apartado. No basta "continua".
Esta nota no es aprobación; no ejecutar hasta recibirla. El control del sandbox conserva
sus propias solicitudes de acceso exacto: la aprobación humana no lo desactiva.

### A — diagnóstico Linux y recursos de prueba locales

1. F2d r2 según [JIT exacto](manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08.md), SHA
   `deb429e38070174b7f179ed2c178bf4c5598ef04c0de4b92ba2f87d624b54078`.
   Ejecutar el comando de ese JIT y sus pins; límite 120 s. Aprobar expresamente el auxiliar
   `/usr/bin/python3` en host Linux solo para peer/proceso/socket, sin instalar ni correr
   tests de producto en host. Si falla identidad, cortar toda etapa Docker dependiente.
2. Único recurso histórico inspeccionable: F1 ID
   `54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`, metadata allowlisted
   y lectura de imagen fijada del JIT. Nunca inspect completo persistido, Env/secretos,
   logs arbitrarios ni lectura de archivos del contenedor histórico. Preservar F1.
3. r9, solo tras identidad PASS, conforme [JIT r9](manifiesto_jit_h3_g03_local_validation_r9_2026-10-08.md),
   SHA `49502617f2bb788b2e9664e659c3f9dd4fe3dc84188ee0b5d86e2909c3dadedf`:
   `/tmp/h3req1-g03-validation-29d8fff9-r2/run-r9.sh`, máximo 180 s.
   Inputs SHA `6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee`;
   paquete SHA `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`.
4. Crear fixtures nuevos exclusivamente para las fases de este ciclo. Nombres finitos:
   `h3req1-close-local-20261008-<fase>-a<N>`, donde fase pertenece a
   `snapshot,tools,web,pg17,postgrest,edge,pages,uat` y N a `1,2,3`.
   Redes/volúmenes con el mismo ID de ciclo y fase declarada; registrar IDs reales después
   de crear. No reutilizar ni retirar recursos históricos. Hasta 12 contenedores activos,
   3 redes y 6 volúmenes de este ciclo; si se necesita más, presentar decisión.
5. Docker create/run/start/exec/inspect/wait/stop únicamente sobre recursos de ese registro.
   Exportar evidencia sanitaria antes de retirar recursos propios con rm/network rm/volume rm
   por IDs exactos registrados. No prune, barrido por prefijo ni limpieza de ajenos.

Riesgos residuales A que necesitan aceptación expresa: procesamiento transitorio del objeto
inspect completo por CLI; posibilidad procedimental de operar fuera del runner por el mismo
usuario. Owner propuesto Romel; vencen al terminar/expirar el ciclo. Mitigaciones: IDs exactos,
proyección limitada, revisión, hashes/registro y no persistir valores secretos. La aprobación
no debe interpretar estos riesgos como permiso para exceder alcance.

### B — autoría, SQL fixture, dependencias y validación iterativa

Correcciones mínimas de tooling/fixtures y defectos H3 demostrados dentro del contrato
aceptado; revisión de consumidores antes de editar. Reutilizar runners, no otro framework.
Nuevas revisiones deben copiarse con nombre/manifest propio; no reescribir runners/reportes
consumidos. Cambios de negocio, nuevos contratos y SQL nuevo del producto quedan fuera.

SQL permitido: aplicar los archivos/harnesses H2/H3 ya incluidos en los manifiestos C02/C03
y los setup/assert SQL C03 existentes, exclusivamente a PG17 fixture de este ciclo.
Creación de DB/roles, seeds sintéticos, suspensión/resume y teardown solo en ese fixture.
Nunca DB cloud ni datos operativos. Si un defecto exige SQL nuevo o fuente Pro nueva, detener
esa parte y presentar el delta concreto; no tomar el snapshot histórico como Pro actual.

Imágenes admitidas, fijadas desde los runners existentes:

- Dev: `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`.
- Node: `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`.
- PG17: `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`.
- PostgREST: `postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`.
- Deno: `denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9`.
- Edge: `supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09`.

Sin pull por defecto. Falta de imagen o dependencia sin caché es una decisión pendiente,
no permiso implícito para descargar. Bootstrap npm dentro de fixture, con lockfiles vigentes,
únicamente registry.npmjs.org, sin retries de descarga; primero inventariar dependencias y
scripts de instalación y registrar cierre transitivo. Deno/browser: usar artefactos fijados
disponibles; nueva descarga/destino no enumerado requiere ampliar paquete antes de aprobar.
Esto evita prometer stack listo cuando sus artefactos aún no se han comprobado.

Fuente candidata RO y copia independiente allowlisted; excluir .env*, tokens, caches,
dependencias históricas y evidencia privada. No montar socket dentro del runtime, no tocar
web/out original ni usar studiamatch-dev como candidato. No acceder a
tests/h3req1-c03-bootstrap/node_modules/.deno sin instrucción humana específica.
Tras bootstrap, bloquear egress externo; comunicación solo entre fixtures/loopback.

Checks: comandos y suites del plan H3-CLOSE-06, leyendo sus argumentos vigentes; npm ci,
lint/typecheck/audit/build en copia Docker, pytest seleccionado, actionlint/ShellCheck,
scanner/scope guard, H2 writer scan, BFF/SDK/Edge/cuotas/suspensión, builds normal/mock con
fixture público elegible. SQL/wire intacto se conserva con justificación; no repetir por prosa.
No ejecutar los comandos destructivos de build en las fuentes originales.

Secuencia obligatoria: snapshot completo PASS -> healthz Pages/workerd PASS -> C03 integrado
real PASS. Runners base: `tests/h3req1_c03_source_snapshot_f1.sh`,
`tests/h3req1_c03_startup_smoke_s1.sh`, `tests/h3req1_c03_integrated_drill.sh` y runtime
asociado. Sus JIT/nombres originales están consumidos: preparar revisión mínima con ID y
recursos de este ciclo, no invocarlos como si las aprobaciones antiguas siguieran vigentes.
Antes de cada fase guardar comando exacto, fuentes/hashes y recursos; no improvisar operaciones
fuera de la matriz aprobada. El drill cubre secuencia completa definida en el plan único.

UAT: `tests/h3_local_uat.mjs`, 48 casos × 3 viewports, 144 capturas, cero retries;
`tests/h3_invitation_uat.mjs`, onboarding 10/10. Cambio de catálogo exige explicar delta,
no reducir cobertura. Fixtures sintéticos sin correo/Auth cloud. Evidencia fuera de tmpfs.

### C — lectura CI remota, sin mutación

Solo repositorio StudIAMatch seleccionado por origin del candidato, cuya identidad debe
confirmarse antes de conectar. Credenciales existentes mediante cliente oficial sin imprimir
valores ni modificar secretos. Métodos GET de GitHub: identidad/permisos necesarios, reglas
de `desarrollo`, `certificacion`, `main`, rulesets/required checks y workflow runs/checks
pertinentes al bootstrap independiente. Hasta 30 requests, timeout 15 s, sin retry automático.
401/403/información parcial = desconocido, no ausencia ni PASS. Registrar configuración
sanitizada y necesidad exacta de bootstrap/review humano.

No push/PR/merge, PUT/PATCH/POST, cambios de protecciones ni workflow_dispatch bajo C.
Esas operaciones todavía no están concretadas contra reglas y base confiable actuales.
Si el control no existe, preparar el patch/PR/commands/rollback del bootstrap y presentarlo
para decisión. No afirmar que la aprobación de lectura autoriza instalarlo. Esta limitación
impide garantizar de antemano una única aprobación para GO_LOCAL_PR completo: la parte local
puede ejecutarse por ciclos con esta respuesta; G10 necesita hechos/revisión externa reales.

## Excepción explícita propuesta para evitar autorizaciones por cada intento

Si el humano aprueba este apartado, la aprobación autoriza hasta tres ejecuciones por fase
de A/B, únicamente después de diagnosticar el fallo anterior y revisar una corrección.
El diagnóstico F2d inicial mantiene su lectura única fijada; si falla identidad, no repetir
ni cambiar de motor sin decisión. Las fases locales posteriores pueden renovar manifiestos
e inputs por correcciones dentro del alcance sin una nueva autorización por cada hash.

Antes de cada intento: snapshot de fuentes/hash, diferencia causal, revisión estática,
comando exacto, recurso/ID, límites y evidencia esperada. Nunca repetir idéntico para buscar
verde, continuar etapa dependiente tras FAIL, aumentar timeout ni ocultar retries.
Los pins aprobados identifican el inicio; el ledger encadena revisiones y nunca edita historia.
Cambios de scope, engine/host, imagen, secreto, destino de red, recursos o contratos fuera de
esta matriz exigen decisión nueva. Este apartado solo sustituye el permiso de una ejecución
por revisión en las fases enumeradas del nuevo ciclo; no revive r1–r8 ni grants históricos.

Duración: hasta 6 horas de ejecución activa en una sola sesión; hasta 3 intentos por fase.
F2d 120 s; linters por intento 180 s; bootstrap hasta 20 min; snapshot 5 min; smoke 3 min;
integrado 30 min; checks 30 min; UAT 45 min. Límites no son garantía de tiempos suficientes:
si se agotan, presentar causa/opciones sin ampliarlos implícitamente. Tope fixture 2 CPU y
4 GiB por contenedor; UAT hasta 4 CPU/6 GiB, PG17 2 CPU/2 GiB. Sin puertos no loopback.
Esperar decisiones hasta 30 min mediante pausas breves, sin simular proceso activo.

Preflight obligatorio sin consumo de ensayo: UID/GID y permisos de todos los ancestros,
archivos y tools montados; directorios allowlisted sin symlinks inesperados; scratch noexec
separado de ejecutables de fixture; hashes, rootfs/usuario/límites y dependencia package/lock;
destino de reporte nuevo, evidencia exportable y fuentes allowlisted. Si no puede comprobarse
un prerrequisito sin ejecutar, incorporarlo como primera comprobación al intento y registrar
su alcance, sin atribuir pruebas no ejecutadas.

## Revisión, recuperación y finalización

Solicitar @security-auditor según AGENTS, corregir findings demostrados y revalidar impacto.
No endurecimientos opcionales que vuelvan a invalidar todos los paquetes. Waivers nunca
automáticos. Disposiciones warnings/PyPDF2/live se agrupan para decisión humana; Romel y
2026-11-03 para braces/priceMin permanecen como seguimiento, no exención.
Detener fase al fallar, preservar salida sanitizada/exit/inputs. Limpiar solo recursos propios
registrados después de exportar evidencia; no retirar ajenos ni fuente por conveniencia.
No modificar Pro, Free, Auth, email, secretos, schedules, writers o deployment del producto.

G01–G10 conservan 10 puntos por gate completo; subcasos aprobados se muestran aparte sin
inflar porcentaje. GO_LOCAL_PR solo tras todos los criterios, CI efectivo y revisión humana
del SHA final. G10 no se reemplaza por "local técnico PASS" ni otra etiqueta de GO.

## Prompt único para la nueva sesión Luna 6 Max

```text
continua H3REQ1. Lee íntegramente:
.context/operaciones/h3req1_paquete_consolidado_cierre_local_luna_2026-10-08.md

Trabaja en /home/romel/src/studiamatch-h3req1-sync-20261002. Lee AGENTS aplicables,
estado vigente, atestación cliente y autoridades enlazadas. Empieza con tareas/gates
y ficha constructor. No reabras levantamiento ni repitas resultados intactos.

Este paquete es PROPUESTA, no permiso. Revalida sus fuentes y SHA antes de pedir una
respuesta humana que identifique ID/SHA y apruebe A/B/C, riesgos/contexto Linux y
la excepción iterativa. Prepara toda dependencia disponible y comandos revisables
antes de preguntar. No heredes permisos consumidos ni el prefijo aprobado de r8.

Si faltan artefactos para bootstrap, presenta juntos los destinos/pins/costos/efectos
necesarios para completar esta misma propuesta antes de aprobarla; no ocultes huecos
ni pidas permiso por cada metadata. Si el paquete cambió, emite SHA actualizado.
Una vez autorizado, ejecutar F2d -> r9 -> copia/smoke/C03 -> checks/UAT/revisión,
con las correcciones/revalidaciones y límites expresamente aprobados. No nuevo framework.
No pedir otra aprobación solo por un hash renovado dentro de la excepción aprobada.

Registrar cada intento en ledger con permisos/comandos/inputs/recursos/causa/results.
Preflight de permisos de carpetas/UID/mounts/tools antes de iniciar contenedor;
los fallos de preparación r8 no deben repetirse. Tras FAIL, diagnosticar y corregir;
no repetir todo ni aumentar retries. Si cambia scope/ambiente/imagen/destino o se
agotan límites, presentar decisión. Si F2d no acredita identidad, no iniciar Docker.

Publica G01–G10 y subcasos tras cada ciclo: base 20%, puntos solo por gate completo.
Continúa hasta GO acreditado o decisión real; no cerrar en runner preparado si la
ejecución está autorizada. Preguntas claras, espera hasta 30 min, no ausencia=permiso.

La lectura CI C puede detectar bootstrap faltante: prepara patch/base/operaciones/
rollback y pide decisión específica antes de writes protegidos. Review humano final
no se aprueba a sí mismo. GO_LOCAL_PR exige G10 real. Remotos D01–D14/deploy quedan
fuera de este ciclo; no proclamar GO global para ocultar ese prerrequisito.
```
