# Paquete de integración Development H3REQ1 — R19

> **Estado: NO-GO Development; no publicar todavía.** Este sucesor parte del baseline y contiene el snapshot R18 reconciliado más los deltas R19 seleccionados. Preserva R8/R9/R12/R13, R14–R18 y sus evidencias. El checkout Syncthing no se sincroniza ni publica. No incluye WIP automáticamente.

## Candidato, base y alcance

- Repositorio: `https://github.com/romelhc95/studiamatch`; target final `desarrollo`.
- Base exacta: `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El sucesor local está en `/tmp/h3req1_r19_publication_prep_20261018`, rama `feat/h3req1-sync-20261018-r19`; no hay commit, push, PR ni deployment Pages.
- R18 histórico permanece en `/home/romel/src/studiamatch-h3req1-publication-prep-r18`, HEAD `0d7c89dccffd1146b6cc669d4994787e9b78b533`, árbol `332ae4d156863c1f5524e7d5f6c8f1ecb4424dc2`. La fuente Syncthing permanece intacta en HEAD `a57bc415257ab8154d40d7c71d34c69d0bdaeb0d`; no se trasladan sus 19.510 entradas WIP.
- El delta R18 reconstruido respecto del baseline tiene 1.143 rutas sin detección de renombres: 1.050 altas, 86 cambios y 7 bajas; dos renombres se contabilizan como alta+baja. R19 sustituye 46 PNG por un placeholder neutral y excluye dos WEBM; conserva los originales en fuentes históricas locales. Ningún original visual se vuelve a cargar.
- R19 añade reporte remoto, esta ficha, cuerpo PR con la plantilla versionada, log de checks, revisión independiente, manifiesto y nota de tratamiento visual. Los tres documentos con referencias a video apuntan a la nota R19. No reabre la reorganización Obsidian.
- Se mantiene `braces@3.0.4-h3.1`; no se cambia lockfile ni tarball. No se declara release oficial upstream ni waiver.

## Permisos y estado de consumo

- A: aprobado y consumido una vez en Free en el alcance del paquete R18. No repetir; Pro queda de solo lectura.
- B: aprobado en alcance exacto, con efectos parciales observados. No volver a pedir aprobación. No considerar completo ni realizar deployment adicional hasta resolver el exceso de deployments y el gateway key ID ausente.
- C: alternativa retentiva aprobada, no consumida. Depende de B, D01/D02 con la identidad Outlook existente y lectura administrativa de las dos notificaciones Auth en estado deshabilitado. No DELETE físico. Gmail permanece intacta.
- D: aprobado, no consumido. La interacción del responsable en navegador sigue siendo necesaria. Sin secretos, códigos MFA o links por chat.
- `main`, Certification y Production siguen fuera de alcance. No cambiar rama default, bypass, autoaprobar ni relajar checks.

## B — lecturas y discrepancias actuales

El reporte [R19 remoto](h3req1_g10_remote_preparation_2026-10-18_r19.md) distingue los datos del conector de la confirmación humana.

**Leído por conector, sin valores secretos ni filas operativas:**

- Pages Preview tiene `ADMIN_QUOTA` como Service binding al Worker esperado, los tres nombres HMAC con tipo secreto, `ADMIN_ALLOWED_HOSTS` y URL Free compatibles. `ADMIN_RPC_GATEWAY_KEY_ID` no está presente. Los dos flags locales no están configurados. Preview comparte configuración con Certification.
- Worker `studiamatch-admin-quota` y namespace `AdminQuotaCounter` están vinculados por nombre/clase. `workers.dev` está desactivado. La lista de deployments muestra versiones 1 y 2 en dos eventos diferentes; R18 B aprobaba como máximo un deployment Worker. No se interpreta cuál lo originó ni se hace un tercero o rollback.
- Free `admin-invite` está ACTIVE v14 con `verify_jwt=true`; el código remoto coincide byte por byte con R18 local. Supabase connector no tiene getter de presencia/nombres de Edge secrets.
- No hay deployment Pages R19 ni candidato servido.

**Confirmación manual recibida:** el responsable confirmó en Supabase Dashboard → Free → Edge Functions → Secrets que `ADMIN_QUOTA_HMAC_KEY` y `NEXT_SUPABASE_SECRET_KEY` están presentes y que la primera coincide con Pages Preview. El conector no puede comprobar esta igualdad ni leer valores. En Pages Preview, `NEXT_SUPABASE_SECRET_KEY` no está presente, conforme al paquete R18: el BFF no la consume y Pages no debe alojar una clave `sb_secret_`.

**Solicitud nueva, aún no ejecutada:** el responsable quiere rotar `NEXT_SUPABASE_SECRET_KEY`. Supabase Dashboard → Free → Project Settings → API Keys → Secret API keys es el origen para crear una nueva clave `sb_secret_`. La rotación no está incluida en B: requiere un paquete JIT aparte que inventaríe consumidores Development, actualice y verifique primero Edge `admin-invite` y los demás stores autorizados y retire la anterior al final. No ponerla en Pages Preview, no pegarla en chat/capturas y no borrarla antes de confirmar todos los consumidores. No se ha generado ni cambiado ninguna clave.

**Bloqueos concretos:** (1) aceptar/reconciliar los dos eventos Worker frente al límite aprobado; cualquier deployment/rollback adicional requiere un delta de alcance y aprobación JIT propia, sin repetir A–D; (2) resolver `ADMIN_RPC_GATEWAY_KEY_ID` coordinándolo con el key ID del subpaso gateway de A; su literal aún no está fijado y no se inventa ni se activa el gateway por inferencia. El cotejo humano de secretos HMAC/Edge ya se completó. La rotación de `NEXT_SUPABASE_SECRET_KEY` no pertenece a B y requiere paquete JIT independiente. No activar el pre-request ni hacer push que dispare Pages Preview mientras el BFF/Edge compatibles no estén listos. El deployment de Pages Preview afecta también Preview de Certification.

## Ruta GitHub y publicación

- GitHub confirma `desarrollo` protegida y en el baseline. La captura del responsable muestra PR requerido, una aprobación, dismissal de approvals obsoletas, aprobación del último push por persona distinta, `security-audit` requerido y rama al día.
- El conector recibió 403 al leer branch protection detallada y no acredita bypass, ruleset, required workflow organizacional ni PWI vigente. No se hace bootstrap en `main`, no se usa bypass ni se cambia la rama predeterminada.
- El ref feature remoto R18 no está presente; no se hará force push. La creación del branch remoto y PR quedan bloqueadas hasta completar B y demostrar la ruta protegida efectiva.
- Cuando se alcancen esos gates, publicar solo este paquete exacto validado y abrir PR hacia `desarrollo`. Debe revisar y aprobar una persona con permiso de review distinta de quien empuja y de la autora; la revisión debe corresponder al SHA más reciente. El responsable o admin del repositorio debe facilitar el acceso de solo lectura a protecciones/rulesets/workflows o confirmar en la UI de GitHub las reglas efectivas. El responsable no debe autoaprobar. Merge solo con el check obligatorio verde y review humana válida.

## Secuencia preparada, aún no ejecutable

1. Reconciliar el historial de dos deployments Worker, confirmar cuál versión/artefacto está activo y comprobar su compatibilidad mediante metadata permitida. No hacer upload, rollback o cambio de binding no listado.
2. El cotejo humano de presencia Edge y paridad HMAC ya está registrado. Resolver `ADMIN_RPC_GATEWAY_KEY_ID` mediante el paso previsto del paquete B/A y un cambio Preview acotado; no activar gateway pre-request todavía.
3. Cerrar gates locales, escaneo, manifest y revisión independiente del snapshot R19; resolver la ruta protegida leyendo reglas activas.
4. Solo después: publicar rama no-forzada desde base; verificar checks del SHA exacto y solicitar revisión humana independiente. No mergear antes de esas condiciones.
5. Merge protegido a `desarrollo` tras aceptación válida; identificar Pages deployment, SHA, hostname, Worker y Edge activos. No usar `admin.studiamatch.com` como Development.
6. Antes de C, ejecutar D01/D02 con la identidad Outlook anterior y confirmar el estado vigente de Gmail. C usa solo el RPC auditado, cambio de correo antiguo a `example.invalid`, bloqueo y retiro TOTP; conserva Auth row, referencias, invitación accepted y auditoría. Detener si el bloqueo no rechaza operaciones Admin o si requiere revocación no incluida.
7. Tras C, invitar Outlook otra vez desde Gmail con intervención del responsable, verificar UUID nuevo de forma privada y completar D03; continuar D04–D14 y 11 grupos de regresión adicional dentro de límites de D.

## Reconciliación acotada del gate documental

La validación del snapshot R19 reveló un defecto del checker, no de la reorganización: el JSON canónico marca 367 rutas como `candidate_only_paths`; 103 no seleccionadas y 40 referencias de evidencia a esas mismas rutas pertenecen al WIP excluido. El snapshot también omite 16 rutas de exclusión de fuentes y 4 rutas de exclusión documental que el registro enumera exactamente. Se corrigió el checker para que solo el modo con manifiesto exacto tolere ausencias expresamente registradas en esas listas y no seleccionadas; cada ruta seleccionada por manifiesto debe existir y una ausencia no listada sigue fallando. El modo normal de checkout completo conserva su exigencia. Se añadieron cinco artefactos concretos que el registro sí referenciaba fuera de esas listas, tras revisión de ruta y scanner.

La ejecución host del checker con `--self-test --candidate-manifest` cerró la integridad documental: 698/698 fuentes descubiertas asignadas; 113/113 documentos activos alcanzables; 433/433 documentos históricos catalogados y enlazados. El self-test pasa sus negativos para fuente no asignada, omisión no registrada/seleccionada/sin manifiesto, rutas o anchors inexistentes, relaciones inválidas, índice duplicado y documento retirado presente. Esta es la ejecución del checker Node en el snapshot candidato; el wrapper Docker sigue pendiente por el error de E/S del motor.

Cinco relaciones de evidencia adicionales no estaban en el alcance R18 y no pertenecían a `candidate_only_paths`. Se incluyeron individualmente porque el registro canónico las cita: dos logs ignorados, dos artefactos pequeños de UAT y una lista de hashes de inputs. Un scan sobre esos cinco archivos halló cero credenciales, correos, UUID o asignaciones de sesión. No se añadió ningún otro WIP. El guard independiente sigue comprobando 13 catálogos y 1.173 destinos.

## Transición, límites y recuperación

| Etapa | Acción / gate | Efectos y límite |
|---|---|---|
| `expand` | A ya aplicado en Free; no repetir. B requiere resolver las dos discrepancias listadas. | Pro solo lectura; no DDL/DML adicional, datos operativos, claves leídas ni escritores. |
| `compatibilidad` | Worker/DO, Pages Preview compartido y Edge v14 compatibles antes de publicar o ligar consumidores. | No activar pre-request; no Preview hasta B completo; preservar Certification. |
| `deploy` | Un Preview del SHA feature aprobado; merge protegido produce Development deployment. | B ya registra dos Worker deployment events frente al máximo de uno. No deployment/retry/rollback adicional hasta delta aprobado. Timeout 10 min; cero retries automáticos; ante timeout releer deployment antes de decidir. |
| `contract` | Solo tras aceptación y estabilidad, conforme a plan; no ocurre en este paquete. | Sin contracción en esta fase; conservar schema expandido. |
| `rollback/recuperación` | Preferir retorno al deployment compatible ya existente y detener nuevas mutaciones. | No restaurar DB, borrar DO/namespace, purgar cuota/auditoría ni rotar secretos. Cualquier despliegue/rollback adicional exige paquete JIT. |

## Aceptación y evidencia

D01–D14: 0/14 acreditados en remoto para este candidato. Regresión adicional: 0/11. No hay deployment Pages R19, aceptación cliente, onboarding nuevo ni resultado runtime. El último-admin requiere escenario remoto aislado y permiso adicional si no puede validarse sin tocar Gmail u otras identidades protegidas. Catálogo, discovery/pipeline y aceptación de producto no se fabrican con scraping, LLM, ETL cloud ni writers productivos.

Cualquier intervención humana se solicitará en bloques pequeños con objetivo, URL, cuenta, efectos y resultado esperado. Contraseña, MFA, tokens y enlaces Auth solo se introducen en navegador; la confirmación humana no equivale a PASS técnico. No capturar valores en screenshots/logs. Si no llega confirmación, mantener checkpoint y avanzar tareas independientes.

## Gates y dueños

| Gate | Estado R19 | Próximo responsable |
|---|---|---|
| B secretos Edge/Preview | Cotejo humano recibido; sin valores compartidos | Codex registra la confirmación, no la atribuye al conector. La rotación consultada queda fuera de B y pendiente de paquete JIT. |
| B deployment Worker | Discrepancia: 2 eventos / máximo aprobado 1 | Responsable + owner Cloudflare: decidir alcance correctivo; Codex prepara delta antes de cualquier acción extra. |
| B key ID gateway | Falta en Preview | Codex/owner fijan el mismo identificador no secreto para B Preview y el subpaso A antes de cambiar configuración; después se verifica presencia sin leer secretos. |
| GitHub protección/ruta | Protección detalle 403; captura parcial | Admin del repo: confirmar reglas efectivas/requerido organizacional por UI o habilitar lectura. |
| Docker/validaciones | El motor Docker devuelve `Input/output error`; el binario `actionlint` y `shellcheck` no están disponibles en el host. | Codex: recuperar el runtime para correr actionlint y ShellCheck focal; no se reclama PASS por `bash -n` ni por revisión estática. |
| Revisión independiente local | Ronda 1 NO PASS; sus hallazgos fueron corregidos. Ronda 2 PASS sin HIGH/CRITICAL/bloqueantes; su único LOW de conteo de discrepancias se corrigió en este sucesor. Ronda 3 dirigida a esa corrección, pendiente. | Revisor técnico independiente: confirmar el digest sucesor exacto; no sustituye approval GitHub. |
| Review GitHub | No hay PR | Colaborador distinto de autora/pusher: revisar SHA vigente y aprobar solo tras checks. |
| D01/D02, C y D | No ejecutados | Responsable participa en navegador; Codex observa y registra evidencia sanitizada. |

## Salida de GO

No declarar GO Development hasta candidato integrado y deployment identificado, protecciones efectivas/review/checks válidos, D01–D14 y regresión aplicable acreditados, aceptación cliente sanitizada, seis pilares satisfechos, rollback/transición documentados y ausencia de bloqueantes. R19 no satisface esos criterios.
