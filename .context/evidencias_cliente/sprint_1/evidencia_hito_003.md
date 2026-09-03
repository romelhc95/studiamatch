# Evidencia Hito 003

`PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION`
`SRC-REQ-002`
`ADENDA-REQ-EST-001-001`

Estado: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO local para PR). La auditoría detallada previa
(`H3_PR_DEVELOPMENT_NO_GO`, histórica) encontró bloqueadores HIGH/CRITICAL en QA,
seguridad y DB; el ciclo de corrección local y la revalidación del candidato
2026-09-03 los resolvieron localmente. La UAT canónica histórica quedó en 47/47 casos
y 141/141 ejecuciones PASS con 0 retries y evidencia regenerada en
`.context/evidencia/h3-expanded/`; los gates reproducidos ahora incluyen la regresión
PG17 A6/A13 del delta `20260903_h3_rbac_contract_fix.sql`. El build normal/mock fue
revalidado PASS. Las acciones remotas JIT-A/JIT-B fueron ejecutadas parcialmente y
quedan documentadas por separado; la aplicación de `20260903`, la revalidación
remota, los casos restantes, certificación, merge y deploy siguen pendientes de sus
aprobaciones separadas.

Estado histórico preservado: `READY_FOR_PROMPT_CONTINUA` fue el gate documental previo; la evidencia vigente acredita `H3_PR_DEVELOPMENT_READY_LOCAL`.

## Explicación Para Cliente No Técnico

Se está construyendo una oficina privada para corregir información de cursos y
administrar a las personas autorizadas. La estructura principal existe y ya quedó
probada localmente: el programa de pruebas completo (47 situaciones repetidas en
tres tamaños de pantalla = 141 comprobaciones) pasó dos veces seguidas, sin
reintentos y con capturas de pantalla.

El candidato no aplica por sí mismo cambios adicionales en servicios reales ni
promueve a producción. JIT-A y JIT-B ya tienen acciones parciales documentadas;
queda pendiente aplicar y probar el delta contra Free y completar los servicios
reales de acceso cuando se otorguen las autorizaciones correspondientes.

| Campo | Valor requerido |
|---|---|
| Commit/tree | Rama local `feat/h3-jit-supabase-admin-combined`, basada en `origin/desarrollo` `c675ef1`; commits `39979e9`, `8d85665`, `9515909` y `a38d5d6` (paquete JIT, evidencias JIT-A/JIT-B y fix A6/A13). Push/PR protegido a `desarrollo` se ejecuta tras validación documental y autorización separada |
| Ambiente | Development local Docker: `studiamatch-dev` + `studiamatch-h2-pg-test` |
| Work package | `NONE_SUPERSEDED`; readiness PR `H3_PR_DEVELOPMENT_READY_LOCAL` |
| Criterio | `H3-CA4` |
| Fuente cliente | `SRC-REQ-002` via `ADENDA-REQ-EST-001-001` |
| Comandos | Revalidación 2026-09-03 en Docker: suite CI-local 142 PASS; lint 0 errores/9 warnings históricos; tsc, pycompile, credential scan, actionlint, shellcheck, builds normal/mock, H2/H2-Pro/H3 PG17 y mock smoke PASS; `h3_pg17_harness_ok` incluye regresión A6/A13 |
| Resultado esperado | Admin y user con límites definidos, 13 campos editoriales con ownership, cola paginada, edición allowlisted, optimistic locking, MFA TOTP `aal2`, invitación por correo, cambio de rol y activación/desactivación de miembros, auditoría, `admin.studiamatch.com`, 404 público, convergencia Free/local PG17 hacia Pro y no regresión pública |
| Resultado observado | UAT local histórica 47/47 y 141/141 PASS con 0 retries y hostname 404 local funcional. La revalidación PG17 actual incluye A6/A13 corregidos localmente. JIT-A remoto hasta `20260902` dejó A6/A13 FAIL; `20260903` aún requiere aplicación/revalidación remota. JIT-B tiene E1/E3/E4/E8 PASS y E2/E5/E6/E7 pendientes. Build normal/mock PASS; waiver static export superseded |
| Avance estimado | `H3_PR_DEVELOPMENT_READY_LOCAL`; 78.7% implementación y 57.7% validación contractual provisional (estimación, no readiness). H3-CA4.11 queda 100% estructural / 55% contractual hasta UAT real en Free/Certification |
| Artifacts/hashes | Evidencia canónica autocontenida y vinculada al candidato en `.context/evidencia/h3-expanded/` (141 screenshots); corridas estructurales previas (`h3-expanded-run-pass1/` y `run-pass2/`) preservadas fuera del repo como evidencia histórica |
| Desviaciones | `sessionStorage` sin waiver formal (pre-Certification). Static export revalidado PASS y waiver superseded. Resto de hallazgos HIGH/CRITICAL resueltos localmente |
| Aprobacion humana | Scope y push/PR a `desarrollo` autorizados separadamente. La aplicación remota de `20260903`, configuración Auth, dependencia build, certificación, merge y deploy requieren aprobaciones separadas |

## Validacion Pre-Arranque

El alcance base de H3 se contrasta contra `SRC-REQ-002` mediante la atestación sanitizada versionada `ADENDA-REQ-EST-001-001`: panel `/admin`, cola de pendientes, edicion manual y publicacion. La ampliación está respaldada por la atestación sanitizada versionada `H3-EXPANDED-PROMPT-2026-08-30`, que autoriza únicamente ejecución local Docker hasta GO local. La fuente privada no se versiona ni se expone en PRs. Este PR solo incorpora la atestación sanitizada y no contiene la fuente privada.

## Contrato de roles

- `/admin/` es una ruta compartida para los roles editoriales activos.
- `user` puede consultar la cola y completar únicamente campos incluidos en `missing_fields`.
- `admin` hereda las capacidades de `user` y además puede publicar, despublicar, archivar, actualizar `quality_status` y gestionar membresías.
- Un usuario autenticado sin membresía activa y un usuario inactivo quedan bloqueados.
- Toda mutación valida identidad y rol en la RPC y genera auditoría cuando corresponde.

## Estado documental del candidato PR

- `20260903_h3_rbac_contract_fix.sql` está incluido en el payload candidato y validado localmente con regresión PG17 A6/A13.
- JIT-A: payload remoto aplicado hasta `20260902`; A6/A13 permanecen FAIL históricos y deben repetirse después del delta.
- JIT-B: E1/E3/E4/E8 PASS; E2/E5/E6/E7 pendientes por Access interactivo, configuración Auth y dependencia build.
- El documento mantiene GO local para revisión del PR, no cierre contractual remoto.

## Checklist de cierre local

- Estado actual: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO local para PR). El checklist
  reabierto por las auditorías previas (`H3_PR_DEVELOPMENT_NO_GO`, histórico)
  quedó cerrado para los gates locales; JIT-A/JIT-B remotos permanecen parciales.
- Matriz estructural completa: 47 casos, 141 ejecuciones y 141 screenshots por
  corrida.
- Resultado: UAT canónica `PASS`, 47/47 casos y 141/141 ejecuciones con 0 retries;
  evidencia en `.context/evidencia/h3-expanded/`.
- Build normal/mock revalidado PASS; rutas admin exportadas; waiver static export
  superseded.
- Suite CI-local 142 PASS, `tsc`, lint, pycompile, credential scan, harnesses H3
  (`h3_pg17_harness_ok`, `h3_pg17_harness_local_ok`) y `git diff --check` PASS.
- Bloqueadores locales resueltos: workflow/allowlist/db-gate H3, invariantes DB,
  regresión PG17 A6/A13, MFA mock, E2E local, rollback y artifacts vinculados al
  candidato.
- `sessionStorage` sigue como riesgo pre-Certification sin waiver formal; no se
  declara resuelto por este PR.
- JIT-A remoto está documentado hasta `20260902` con A6/A13 FAIL históricos;
  JIT-B tiene E1/E3/E4/E8 PASS y E2/E5/E6/E7 pendientes. La aplicación de
  `20260903`, revalidación remota, certificación, merge y deploy permanecen bajo
  aprobaciones separadas.
