# Cierre de validación local H3REQ1 — G01–G09

Fecha: 2026-10-10. Autoridad: encabezado vigente de
[Estado Del Proyecto](../estado_del_proyecto.md), AGENTS y autorización humana de esta sesión.
El permiso cubre exclusivamente preparación, correcciones y validación local H3REQ1 en el
candidato; no concede Git remoto, CI remoto, despliegue, servicios/cuentas/datos cloud ni
acceso a secretos.

## Identidad, impacto y preservación

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`; HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
  HEAD no define por sí solo el WIP.
- En la captura de cierre el candidato contiene 741 entradas WIP: 0 staged, 55 modificadas
  rastreadas y 686 untracked. Se conserva íntegramente, sin reset, clean ni commit.
- El checkout original `/home/romel/src/studiamatch` no recibió escrituras durante este ciclo;
  al inspeccionarlo conservaba 78 entradas de estado. Sus cambios no se incorporaron al
  candidato ni se limpiaron.
- Componente/consumidores: Admin editorial y membresías, BFF Pages/HttpOnly, gateway/Edge,
  cuotas, migraciones y harness PostgreSQL, Pages/workerd, workflows de seguridad y pruebas
  UAT/onboarding. Contratos preservados: ownership/procedencia, auditoría atómica append-only,
  disponibilidad fail-closed, identidad Auth, roles/MFA, cookie HttpOnly y gateway firmado.
- Se reutilizan resultados con inputs compatibles; los deltas editorial/BFF/workflow se
  renovaron mediante harness PG17, pytest y pruebas G03. No se repitieron suites intactas.
- Rollback: fuentes/manifiestos y exportes son artefactos separados; los fixtures tienen
  limpieza por IDs exactos y la transición de producto conserva compatibilidad legacy. No se
  ejecutó rollback de despliegue porque ningún despliegue remoto está autorizado en este ciclo.

## Gates y evidencia

| Gate | Estado | Resultado y alcance |
|---|---|---|
| G01 — SQL/editorial | Completo local | C02 v4 conserva 69/72 inputs coincidentes; los tres deltas son `tests/sql/h3_pg17_harness.sql`, `.github/workflows/security-audit.yml` y `web/functions/_lib/admin-bff.ts`. El harness editorial actual se ejecutó en PG17.11 en UAT R11 y onboarding R5 y emitió los marcadores de harness completos. Workflow/BFF se cubrieron en G03/G08. No se afirma C02 72/72 ni se repite el C02 intacto. |
| G02 — suspensión SQL | Completo | C03 safe-suspend/resume v3 conserva sus 41/41 inputs exactos; el PASS SQL aislado continúa aplicando a esos bytes. R46 aporta además la integración real local, sin sustituir ni ampliar retroactivamente el subgate SQL aislado. |
| G03 — tooling | Completo | La invocación aprobada del JIT r9 V5 (`0cdd62518f924693c0c05b45a69ecaf8a2bf4b4b0d96001f1bde75a39f403eb6`) se consumió una vez, exit 0, y terminó `ALL_PENDING_CHECKS_OK`. Actionlint se reutilizó porque coincidieron los tres hashes fijados. ShellCheck, ESLint, typegen, TypeScript, pruebas protegidas del workflow, scanner de credenciales y scope guard completaron el ciclo. Evidencia: [r9 V5](h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v5.txt). |
| G04 — controles F1 | Completo | Lecturas allowlisted y controles de imagen/contenedor se acreditaron con F1 V3 y el snapshot S12; sintéticos positivos/negativos conservaron aislamiento y fallo cerrado. No se usó `inspect` completo ni se expusieron `Env`. |
| G05 — snapshot completo | Completo | S12 validó 14 archivos (13 fuentes y manifiesto), 540,851 bytes, 13/13 hashes, cero symlinks, permisos exactos y cero ownership preservado. Productor, limitador, receptor y filtro salieron 0; el verificador independiente read-only/net-none salió 0. Volumen preservado. [S12](h3req1_c03_source_snapshot_2026-10-10_s12.md). |
| G06 — Pages/workerd | Completo | Pages/workerd real respondió healthz en S9, cinco intentos, exit 0, sin OOM ni egress. No incluyó DB/Edge en esa etapa. [S9](h3req1_c03_startup_smoke_2026-10-10_s9.md). |
| G07 — C03 integrado | Completo local | R46 PASS sobre PG17.11, PostgREST 13, Pages/workerd y Edge Runtime. Reserva previa, suspensión, rechazos 503/403 con nonce preservado, finalizador in-flight de efecto único, auditoría/cuota, resume persistente, lectura de una fila, replay idempotente sin segunda llamada Auth, AAL2/rol admin y smoke final pasaron. Evidencia: [inventario R46](h3req1_c03_r46_result_inventory_2026-10-10.md), [log sanitizado](h3req1_c03_integrated_run_2026-10-10_r46.txt), SHA-256 `0fefdb22984226124a2847c8f9f4a01923a2396569b01309db8239f30b4f1a00`. La corrección que habilitó la lectura PostgREST fue solo del rol sintético en PG17 desechable; no se cambió producto o policy remota. |
| G08 — checks finales | Completo local | Pytest del proyecto: 307 passed, 4 skipped por dependencia explícita de API/credenciales live, 1 warning deprecación PyPDF2. Builds normal y mock generaron 17 rutas; ambos exportes tienen manifiestos verificados de 126 archivos. Scanner, contratos de BFF/SDK/Edge, ShellCheck, ESLint, TypeScript, actionlint, H2 writer scan y regresiones focales quedaron cubiertos por G03/G08 con inputs identificados. |
| G09 — aceptación local | Completo local | UAT sintético: 48 casos × 3 viewports = 144/144 PASS, 144 capturas verificadas por hash, retries 0. Onboarding aislado: 10/10 PASS, retries 0, spacing mínimo 20,100 ms. Harness editorial PG17 actual pasó en ambos runners. No se usó cuenta existente, MFA real, correo real ni servicio cloud. |
| G10 — CI remoto | Pendiente | Workflow/control y patch local preparados, pero no publicados, integrados, configurados como required ni verificados en GitHub. G10 conserva sus 10 puntos históricos pendientes y requiere instrucción remota separada y revisión humana. |

### Conciliación C02/C03

C02 v4 no-C03 sigue en 69/72; este valor es comparación de inputs, no conteo de pruebas.
Los deltas del harness editorial, BFF y workflow tienen cobertura renovada en los runners
actuales citados arriba. C03 SQL v3 conserva 41/41 inputs coincidentes; el PASS de ese
subgate es histórico y acotado a sus entradas. El cierre integrado procede únicamente de R46.

## Cuatro criterios de aceptación del cliente

La atestación sanitizada H3 y la aceptación del plan editorial son la fuente de criterios; el
documento privado no se incorporó ni se leyó. Las pruebas locales cubren:

1. Admin completa/corrige manteniendo origen y autoría; conserva override y resuelve conflicto
   de versión sin sobrescribir silenciosamente cambios concurrentes.
2. Cada mutación registra actor, fecha y valores anteriores/nuevos; el cambio editorial y su
   auditoría son atómicos y el historial permanece protegido/append-only.
3. La disponibilidad exige evidencia válida: el día 90 calendario es inclusivo, el exceso,
   ausencia, expiración o evidencia inválida se rechaza/falla cerrado; el dato legacy conserva
   compatibilidad sin inferir disponibilidad.
4. El encabezado usa el correo de la sesión Auth autenticada con fallback de error; el rol
   continúa aplicando permisos sin exponer el token al navegador.

Evidencia: harness PG17 `pg17-harness-r3.txt` y `pg17-harness-onboarding-r5.txt`, UAT R11 y
regresiones del proyecto. Compatibilidad verificada en export normal/mock, BFF/HttpOnly,
gateway firmado, cuotas, RBAC y MFA sintética. Las 4 pruebas live omitidas son solo las que
requieren API/credenciales externas; no se cuentan como PASS.

## Seis pilares y transición

| Pilar | Evidencia y límite |
|---|---|
| Funcionalidad | R46 integrado, criterios anteriores, 144/144 UAT y 10/10 onboarding sintéticos. No acredita comportamiento remoto. |
| Escalabilidad | Límites locales fijados hasta 4 GiB/2 CPU para app y 2 GiB/2 CPU para PG17 en el drill. No hubo prueba de carga, concurrencia a escala ni garantía global. |
| Seguridad | BFF same-origin con cookie HttpOnly, gateway firmado, cuotas, roles/MFA y pruebas sintéticas; scanner/credenciales y audits locales completos. No se inspeccionaron secretos ni se validó configuración remota. |
| Mantenimiento | Manifiesto de 599 entradas SHA-256 `7c153c3e9098b7117bddd654f26fd83f8a82db20bda255533a691f32f7728dbc`; export normal/mock, artefactos y logs identificados. Nueve advertencias ESLint y una deprecación PyPDF2 permanecen visibles, sin waiver; revisión humana braces/`priceMin` al 2026-11-03 preservada. |
| Calidad | 307 pruebas aprobadas; 4 pruebas live omitidas por el límite de acceso; actionlint, ShellCheck, TypeScript, scanner/scope guards, builds, harness editorial y revisión estática cubiertos. |
| Rendimiento | Las duraciones UAT incluyen navegador y workflow: mínimo 315 ms, mediana 4,772.5 ms, p95 6,842 ms, máximo 7,998 ms. No son latencia de aplicación ni Core Web Vitals; no se ejecutó benchmark dedicado. |

Transición documentada como `expand → compatibilidad → deploy → contract`: cambios aditivos y
lecturas/exports legacy se probaron localmente; despliegue, estabilización, contracción y
rollback remoto quedan pendientes. El rollback local de fixtures se verificó mediante retirada
exacta; no se usó rollback de producto.

## Auditoría de dependencias R7 y revisión

El audit R6 se conserva como inválido para aceptación: la revisión detectó que entrada y salida
podían solaparse a través de un mount writable. R7 corrige la separación con directorios hermanos,
guarda `realpath` y monta entrada read-only y salida aparte. Wrapper SHA-256
`c73fe36cab6a5641680d407a013c3abde9c1b48ed517d11789efe0cb72c79b6a`; inner SHA-256
`27ba27e290f45337f15f6ed0e6c45778352869dbee8874a7f511d18935ab1cc3`. Bash syntax y ShellCheck
oficial local pasaron. El runner registró proxy allowlisted con 3 destinos permitidos, uno
rechazado, cero upstream failures y retries 0; audit full y production informaron 0 vulnerabilidades
en la captura. La revisión estática independiente de esos hashes fue PASS; el límite de que la
lista del path se valida después de crear los directorios queda anotado, sin hallazgo de cruce de
mounts. Evidencia: [log del audit R7](h3req1_g08_npm_audit_2026-10-10_r7/output/npm-audit-r7.log)
y outputs JSON archivados en la misma carpeta.

## Docker y evidencia preservada

Inventario de cierre, sin leer `Env`:

- `studiamatch-dev`: ID `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`,
  imagen `studiamatch-h3req1:20261009-v3`, healthy; `/app` monta el candidato y el volumen
  `studiamatch_h3req1_node_modules` sigue montado RW como entorno habitual de trabajo.
- Volumen holders S2/S3, ambos `network=none`, usan la imagen fijada
  `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`; retienen
  `/pages`, `/source` y `/tools` en solo lectura (`h3req1-c03-startup-*-20261010-s2/s3`).
- No quedan activos los fixtures UAT, onboarding, R46, proxy de build ni proxy de audit. La
  red `studiamatch-h3req1_default` tiene solo `studiamatch-dev`; las redes H3 históricas restantes
  observadas no tienen miembros. No se hizo prune ni limpieza global.
- Los runners retiraron solo contenedores/redes fijados después de preservar evidencia. No se
  borraron imágenes ni volúmenes; quedan fuentes/snapshots/TLS/caches históricos, incluidos
  volúmenes de rondas previas R1–R49. Se conserva evidencia en archivos; no se mantiene cada
  contenedor histórico como requisito.

## Fallos corregidos y observaciones

- TypeScript falló inicialmente con exit 134 por heap/memoria insuficiente en contenedor de
  512 MiB. La ejecución r9 fijó 4 GiB y `--max-old-space-size=3072`; TSC pasó. No se cambió
  `tsconfig` por analogía.
- R6 npm audit no se usa; la revisión y R7 reemplazaron únicamente el método de captura.
- Un intento de ejecutar ShellCheck dentro de la imagen de aplicación devolvió exit 127 porque
  no contenía ShellCheck. Se usó la imagen local oficial fijada `koalaman/shellcheck:v0.11.0`;
  Bash syntax/ShellCheck pasaron. No se instaló en el host ni en el producto.
- ESLint conserva nueve warnings y Pytest una deprecación; se registran sin aceptación tácita.
- G10, revisión humana protegida, integración/push/PR/merge, configuración remota, deploy
  Development y D01–D14 no se ejecutaron. Certification y Production quedan fuera.

## Métricas y decisión

La métrica conserva el mismo denominador de diez gates históricos y nueve gates locales:

| Métrica | Inicial al empezar esta continuación | Final | Delta |
|---|---:|---:|---:|
| Tablero histórico G01–G10 | 70% (7/10) | 90% (9/10) | +20 puntos porcentuales |
| Cierre local G01–G09 | 7/9 = 77.78% | 9/9 = 100% | +22.22 puntos porcentuales |

El aumento corresponde a G08 y G09 completados con sus resultados ejecutados, no a documentación,
hashes, limpieza ni preparación de CI. G10 sigue pendiente.

**Validación local H3REQ1 completa: GO para revisión del responsable.** No declara `GO_LOCAL_PR`
ni `GO_DEVELOPMENT_REAL`. La siguiente decisión separada es revisar este candidato y, si se
aprueba, autorizar integración y pruebas remotas Development; CI protegido debe quedar efectivo
por el flujo humano correspondiente antes de considerar G10 cerrado.
