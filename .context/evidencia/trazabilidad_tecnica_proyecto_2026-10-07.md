# Reconciliación documental y trazabilidad técnica del proyecto completo

Fecha: 2026-10-07. Pedido humano: implementar la capa global del análisis y publicarla
junto al candidato H3REQ1 **cuando se aprueben PR y pruebas remotas**. No es aprobación
de commit/push/PR/deploy ni de writes. Owner técnico: constructor de este ciclo;
aceptación/operaciones protegidas: responsable humano.

## Alcance y tareas

Levantamiento por dominios de fuentes/config/workflows/tests; mapa y contratos, matriz
de impacto, cobertura/evidencia y protocolo constructor. Reconciliar índice/entradas y
rotular históricos sin borrar resultados. Solo documentación/guía, sin código funcional,
SQL, configuración de pipeline, workflow, secreto o servicios remotos modificados.

Fuente observada: worktree `studiamatch-h3req1-sync-20261002`, WIP preexistente amplio;
no se congela el producto con HEAD baseline. No se restaura arquitectura retirada ni
se hace un inventario remoto. La capa abarca dominios de todo el proyecto, no es una
auditoría exhaustiva línea a línea ni un diccionario de cada tabla/función SQL.

## Fuentes y contrastes reales

- AGENTS/estado/índice/atestaciones/planes/matrices existentes.
- Scripts core/shared/maintenance, config, DB/migrations/rollback y modelo Supabase.
- Imports BFF/middleware/HTTP y cliente público; fetch directos a lector efectivo;
  mapping sync/manual overrides/calidad RPC/ROI, gates modernos/fallback.
- CI FG1/2/3/DB sync/canary/security/protected integrity, PR template y tests por dominio.
- Docker compose/package/deps y separación de mocks/runtimes/manifests.

## Hallazgos documentales y tratamiento

| Hallazgo | Corrección o disposición |
|---|---|
| Índice enlaza manifiesto inicial como pendiente | Rotular histórico y dar entrada vigente por estado/capa/ruta |
| Reporte H3 mantiene READY_LOCAL anterior al BFF | Banner histórico con candidato/fecha, referencias a estado y mapa actual |
| Borrador BFF describe inexistencia de rutas que ahora están implementadas | Banner PROPUESTA/HISTÓRICO; implementación actual via middleware/BFF, no rehacer diseño |
| Matriz H3 contiene pendientes/porcentajes anteriores | Corte histórico explícito; contrato cliente no se reinterpreta; D01–D14/estado vigentes |
| Modelo DB mezcla investigaciones/gobierno histórico y adopción | Separar cortes históricos de fuentes del candidato/adopción por ambiente |
| Plantilla PR arrastra resultados marcados de otro candidato | Preservar cuerpo anterior como historia y sustituir plantilla por estructura sin PASS heredados |
| Guía pipeline describe solo gate legacy y harvesters dedicados como estructura normal | Añadir amarre a mapa/gates modernos y aclarar rutas deprecated; no cambiar código/gates |
| Guía «sin DB local» parece excluir PG17 fixture | Distinguir DB cloud operativa de bases desechables de prueba JIT |
| Nueva carpeta documental fuera de allowlist H3 explícita | Registrar revisión scope/inclusión pendiente antes de PR; NO cambiar ni quitar guard aquí |
| Evidencia `.log` ignorada puede no viajar con PR | Exigir resumen sanitario versionado y recuperabilidad; no subir raw logs/keys |

Cuerpo anterior íntegro: [plantilla PR histórica](../seguimiento/plantilla_pr_historica_2026-09-24.md).
Nueva [plantilla reusable](../../.github/pull_request_template.md) sin checks/PASS marcados.

## Demostración de uso de la capa (documental, no runtime)

| Cambio hipotético | Aristas contrastadas | Pruebas/evidencia que revisar |
|---|---|---|
| HTTP firma | BFF importa transporte; cliente público también; dispatcher SQL/wire | Credenciales+SDK headers, público, gateway/replay/wire; no ROI sin otra arista |
| Cookie auth | Constantes en BFF y lista/chunks en middleware; callback/idle/UI | BFF/logout/recovery/MFA, limpieza cookies workerd, C03; SQL sin cambio puede conservar PASS |
| Campo sync | enriched mapea certification/benefits/objectives/audience; lee overrides y calidad RPC | Contrato pipeline/editorial, SQL calidad, DTO/view y render/preview; writer real JIT |
| Snapshot tar | SOURCE_MANIFEST -> tar pipeline -> verificación -> npm -> workerd | D3 falló antes de tar por logger local con `max-file=1` y compresión habilitada (causa D3 demostrada, no S1). D4 fixture devolvió exit 0; J3 atribuyó el NO-GO del harness a `.Mounts` vacío pese a `HostConfig.Tmpfs[/diag]` correcto. F1 completo está preparado; auditoría final deja únicamente MEDIUM de bypass same-user, waiver no aprobado. No ejecutar hasta aceptación explícita + JIT; no repetir gates consumidos |

Los casos están en [matriz de impacto](../trazabilidad/matriz_impacto.md). No se ejecutaron
esos cambios ni sus tests funcionales como parte de este ciclo documental.

## Validación y límites

Resultados ejecutados:

| Control | Resultado real y alcance |
|---|---|
| Tests documentales/cliente en Docker | 21 PASS, exit 0: `test_obsidian_context_state.py`, `test_requirement_client_source_validation.py`, `test_h2_client_evidence_docs.py`; `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, `/candidate` en `h3req1-candidate-docker-20261004` |
| Destinos/formato de las notas editadas | Pasada final: 20 archivos, 251 destinos locales existentes, cero fallos y fences/newlines PASS; pasada inicial 249 destinos |
| Paths de fuentes en capa | 73 paths literales existentes, cero faltantes en la pasada registrada; links codificados al detalle también resuelven |
| Grafo `.context` | 115/115 notas alcanzables desde índice, 0 sin entrada y 0 destinos locales rotos; excluye config `.obsidian`, no verifica anchors/URLs externas/render |
| Casos de impacto A–D | Contraste documental de consumidores/código descrito arriba, no runtime |
| Whitespace y regresión documental final | `git diff --check` exit 0; segunda ejecución tests Docker 21 PASS, exit 0 |
| Scanner canónico | **EJECUCIÓN INVÁLIDA**, no PASS: `/tmp/studiamatch_credential_findings` no escribible en el contenedor; imprimió «credential scan passed» pese a errores. No se cambió permiso/archivo/scanner |
| Comprobación adicional en memoria | 20 archivos, 0 coincidencias con regex derivada del scanner canónico y adaptada POSIX→Python, exit 0; no usa temporal ni imprime valores; NO sustituye revalidación del scanner oficial |

El primer comando de comprobación en memoria falló por quoting WSL (exit 1); se corrigió
usando `wsl --exec` y completó. No se creó script persistente ni se instaló herramienta.
H3 continúa NO-GO. S1 falló antes de npm/workerd; D3 no alcanzó tar y su causa fue una
configuración inválida del logging local, recuperada por J2. D4 devolvió exit 0 desde el
fixture, pero su verificación de metadatos/controles falló y no hubo PASS aceptado del gate.
Esto no demuestra la causa histórica de S1. J3 de lectura allowlisted fue consumido y
determinó el falso negativo del harness D4. F1 está preparado con runner, sidecar y JIT
propios; hash/sintaxis pasan. Auditoría final no encontró HIGH/LOW, pero conserva un
MEDIUM procedimental de bypass same-user documentado como waiver NO aprobado. El siguiente
gate es aceptación humana del residual y JIT independiente antes de Docker. Ver
[D3](h3req1_c03_d3_create_start_failure_reconciliation_2026-10-07.md) y
[D4/J3](h3req1_c03_d4_metadata_mismatch_reconciliation_2026-10-07.md) y
[F1](h3req1_c03_source_snapshot_f1_static_review_2026-10-07.md).

### Hallazgo de validación que debe ver el siguiente constructor

El scanner usa una ruta temporal fija y su `if grep ... >archivo` puede tratar un error
de redirección como ausencia de hits. Observado al validar documentación, no auditado como
seguridad integral ni atribuido a los cambios de este ciclo. Owner: Security/Release.
Antes de GO_LOCAL_PR: conseguir ejecución válida del control en entorno correcto y revisar
fallo cerrado frente a error de I/O/grep y colisión de temporales, con pruebas reproducibles.
No ejecutar como root, borrar un temporal ajeno o cambiar permisos solo para obtener PASS.
Corrección de código/scanner pertenece a un ciclo explícito separado y review según AGENTS;
no se oculta ni se remedia fuera del alcance documental. No hay waiver aprobado.

No se consultaron APIs remotas ni raw secretos. No se ejecutaron writers, SQL/DDL/DML,
drills/bootstraps/start/stop/cleanup, correo, Auth/reset, push/PR/merge o deploy.
Los checks Docker documentales ejecutados no constituyen nuevos PASS del producto.

## Transición y publicación

Cambio documental sin comportamiento runtime: expand/compatibilidad significan añadir
guía y mantener historia; deploy/contract funcional NO aplican y no ocurren. Rollback
documental sería un delta que retire/corrija solo esta capa, preservando evidencia y WIP,
no reset ni borrado amplio. Se incluye en inventario PR H3 cuando el humano lo autorice.

Pilares: funcionalidad/seguridad/escalabilidad/rendimiento no se revalidan por prosa;
mantenimiento/calidad mejoran por aristas, protocolo y pruebas documentales, dentro
del alcance comprobado. No declarar seis pilares PASS global por este levantamiento.

Referencias: [entrada técnica](../trazabilidad/00_entrada_tecnica.md),
[estado](../estado_del_proyecto.md), [índice](../indice.md),
[plan de cierre](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md).
