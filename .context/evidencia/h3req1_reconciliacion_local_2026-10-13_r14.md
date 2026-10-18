# Reconciliación local del candidato H3REQ1 — R14

> Corte local: 2026-10-13. Este informe prepara un paquete local para revisión; no crea PR ni acredita adopción remota.

## Autoridad y alcance

Se leyó `AGENTS.md`, `.context/estado_del_proyecto.md`, los manifiestos y cuerpos R8/R9/R12/R13, el cierre R13, sus catálogos y la plantilla versionada. La autorización cubre conciliación y validación local. No cubre commit, push, PR, merge, lecturas/configuración remota, deploy ni escrituras Supabase. La atestación sanitizada de cliente se conserva; el documento privado no se leyó ni se incluye.

El paquete combina el alcance funcional del R8 (G01–G09, con resultado local R178 y delta local G10 R181/R182) con el contenido documental más reciente del R13. Para las rutas compartidas se usan los bytes actuales del R13; R8, R9, R12 y R13, sus manifiestos, cuerpos, checks e informes de cierre/revisión permanecen como evidencia histórica sin reescritura. Los 110 paths del scope R12 están contenidos en R13: el contenido más nuevo reemplaza 23 versiones anteriores y R13 agrega 28 paths. R8/R13 comparten 18 paths: 15 se toman de R13 y 3 conservan bytes idénticos.

R9 es una iteración documental intermedia. Su manifiesto, cuerpo y checks se preservan como evidencia; sus diez rutas exclusivas no se agregan en bloque. Ocho mapas retirados no existen en el checkout y no tienen referencias directas en los catálogos. `.context/sistema_db_supabase.md` y `web/vendor/README.md` siguen disponibles por el alcance R8 y por enlaces actuales. Las siete eliminaciones del scope R13 se conservan como eliminaciones. No se reactiva una navegación alternativa ni se reorganiza Obsidian.

## Disponibilidad de catálogos y fuentes

Los 13 catálogos contienen 1,173 destinos directos únicos tras corregir tres enlaces a salidas/cache generadas que R8 excluye y que no existen en HEAD. La corrección se limita a retirar esos paths de dos relaciones fuente del JSON canónico y regenerar la vista; no cambia el conjunto de 433 documentos históricos ni su navegación. El scope seleccionado cubre 166 destinos; 324 están en el HEAD base, con 54 rutas presentes en ambos conjuntos. Los 737 restantes son archivos locales no versionados que los catálogos enlazan directamente. Se seleccionan esas 737 rutas y ninguna otra ruta solo por pertenecer a un directorio o a WIP. Trece logs ignorados por `.gitignore` forman parte de la evidencia R8 seleccionada; otros 22 logs ignorados son destinos de catálogo. Se declaran expresamente, y una futura inclusión en Git requerirá agregarlos de forma explícita. En el checkout actual los 1,173 destinos están presentes. El manifiesto final fija path, fuente del enlace, estado de disponibilidad, modo, tamaño y SHA-256.

Las 433 referencias históricas R13 siguen enlazando evidencia original. El cierre de disponibilidad añade los artefactos directamente enlazados por los catálogos; no transforma logs, scripts ni fixtures históricos en cambios funcionales activos. Los targets versionados no seleccionados se consumen desde el HEAD base, incluso si el checkout contiene WIP modificado en esos paths: esos deltas no se añaden por defecto. El WIP observado registra 20,566 paths en `git status`; 1,082 de ellos forman parte del paquete y 19,484 quedan fuera. De los 88 paths modificados, los tres `.github/agents/*.md` ajenos a R8/R13 se excluyen. Además se incluyen 35 paths ignorados: 13 logs de evidencia R8 y 22 logs de catálogo. Los cinco artefactos R14 ya están incluidos entre los 1,082 paths con estado Git propuesto. R14 fija 1,117 rutas en total. La reconciliación del mismo conjunto contra `desarrollo` sigue pendiente de G10 remoto.

## Dependencia `braces`

`web/package.json` y `web/package-lock.json` mantienen `braces` en `file:vendor/braces-3.0.4-h3.1.tgz`; `web/vendor/README.md` documenta el snapshot local asociado al PR upstream #72. R14 no cambia tarball, versión ni lock. No se hizo una consulta upstream.

Opciones para decidir antes de modificar la dependencia:

1. **Mantener el snapshot local**, preservar reproducibilidad y solicitar en G10 una lectura de procedencia/upstream, escaneo renovado y comprobación de hash antes de promoción. Es la opción aplicada a este paquete local.
2. **Migrar a una versión oficial publicada** únicamente si la lectura remota confirma disponibilidad y equivalencia del fix; luego regenerar lock y repetir scanner, instalación, lint, typecheck y build en Docker.
3. **Separar el paquete funcional y documental** mientras la procedencia quede sin resolver; conservar R8/R9/R12/R13 como antecedentes y posponer la reconciliación de dependencia.

La revisión pendiente se asigna a Romel para el 2026-11-03. Mantener la copia en R14 no afirma que el origen o el fix upstream estén verificados.

## Compatibilidad y transición

La aceptación funcional local G01–G09 está documentada en R178; sus harnesses PG17 desechables y datos sintéticos no son escrituras a la instancia operativa. La cobertura local R181/R182 permanece como evidencia acotada. Los cambios actuales de BFF y transporte que se superponen con R13 son líneas de marcador documental; las pruebas/contratos cuyo propio input cambió se vuelven a ejecutar. La revisión detectó que la condición del gate H2 admitía `pull_request_review`, evento ausente del trigger Stage 1; se quitó esa rama inalcanzable sin cambiar la condición efectiva para PR a `main`. El test `security_flow` se alineó al estado R13 y a la separación Stage 1/Stage 2 ya registrada en R180. La corrida combinada focal pasó 78/78. R14 no agrega un contrato de runtime ni cambia SQL/producto fuera del candidato funcional R8.

| Fase | Resultado y límite |
|---|---|
| expand | El esquema y migraciones del alcance R8 tienen evidencia local PG17/R178; R14 no aplica SQL. |
| compatibilidad | Se conserva el fallback legacy y el contrato previo probado localmente en R178; no se retiran rutas de servicio remoto. |
| deploy | Build/Pages/workerd local documentado por R178 para inputs compatibles; no hubo deploy de Cloudflare ni GitHub. |
| contract | Contracción remota no ejecutada; G10 debe comprobar orden de consumidores, compatibilidad y autorización. |
| rollback/recuperación | Rollback SQL local y recuperación sintética están en R178; rollback remoto no ejecutado. |
| no degradación | Los criterios de cliente y pilares locales se limitan a fixtures, harnesses y pruebas R178; no acreditan usuarios ni datos reales. |

## G10: alcance de lecturas remotas requerido

Para comenzar G10 se requiere una instrucción separada que autorice únicamente estas lecturas, sin cambios remotos:

1. **Supabase Pro (`xwhtiqmboljkshrtviyw`)**: leer schema, tipos, constraints, funciones/RPC y ledger de migraciones relacionados con H3REQ1 para comparar con el baseline y el paquete. No consultar filas operativas, usuarios, invitaciones, cursos ni datos personales; no aplicar DDL/DML.
2. **Edge/Auth/correo**: inspeccionar versión desplegada de `admin-invite`, configuración no secreta de origins/redirects, Auth invite/recovery y su template/proveedor, callers autorizados y estado de validación. No leer contenido de buzones, tokens ni valores de secretos.
3. **Pages Functions/BFF/gateway**: verificar rutas y versiones desplegadas, presencia/nombre/ID de bindings Admin, Worker/DO y gateway, `pgrst.db_pre_request`, allowed hosts y configuración de cuota/firma. Confirmar presencia/rotación mediante metadata; nunca revelar ni exportar valores HMAC/API.
4. **GitHub**: leer existencia y SHA de `desarrollo`, comparación contra el HEAD candidato, protección de ramas, required checks, instalación/estado de `security-audit` y PWI, workflow runs relevantes, schedules y estado CodeQL. Sin crear PR, ejecutar workflow ni cambiar configuración.
5. **Cloudflare Pages/CDN**: leer proyecto/ambiente, deployment/ref actual, preview y rutas publicadas, estado de cache y smoke de solo lectura. Sin deploy, purge ni mutación.
6. **Solo si se elige la opción 2 de `braces`**: verificar metadata/release oficial, PR/fix upstream y hash del tarball publicado para decidir equivalencia. Esta lectura no forma parte de R14.

PR, merge, deployment, GitHub `workflow_dispatch`, Supabase writes y cambios de secretos conservan aprobaciones JIT separadas. G10 no se considera iniciado por este documento.

## Validación local y cierre

La revisión independiente local R14 dio PASS: cero HIGH/CRITICAL y ningún finding de código pendiente. Su dictamen no reemplaza CI o comprobaciones remotas. Tras esa revisión, `actionlint` v1.7.12 validó todos los workflows en Docker y `ShellCheck` 0.11.0 pasó con seguimiento de `source` en los dos scripts del guard de rutas. El escaneo adicional de los 181 scripts `.sh` seleccionados reportó diagnósticos en runners/evidencias históricos; no se hizo limpieza masiva fuera de la delta funcional. Resultados, comandos y alcance están en `h3req1_reconciliation_checks_2026-10-13_r14.txt`; el manifiesto fija los paths y hashes finales.
