# Evidencia Hito 003

`PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION`
`SRC-REQ-002`
`ADENDA-REQ-EST-001-001`

Estado: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR). La auditoría detallada previa
(`H3_PR_DEVELOPMENT_NO_GO`, histórica) encontró bloqueadores HIGH/CRITICAL en QA,
seguridad y DB; el ciclo de corrección local del 2026-09-02 los resolvió y la UAT
canónica quedó en 47/47 casos y 141/141 ejecuciones PASS con 0 retries y evidencia
regenerada en `.context/evidencia/h3-expanded/`. El build normal/mock fue
revalidado PASS. Commit + push + PR protegido a `desarrollo` fueron autorizados por
instrucción humana separada; las acciones remotas posteriores (JIT Supabase
Free/Auth, Cloudflare, certificación, merge y deploy) siguen sin autorizar.

## Explicación Para Cliente No Técnico

Se está construyendo una oficina privada para corregir información de cursos y
administrar a las personas autorizadas. La estructura principal existe y ya quedó
probada localmente: el programa de pruebas completo (47 situaciones repetidas en
tres tamaños de pantalla = 141 comprobaciones) pasó dos veces seguidas, sin
reintentos y con capturas de pantalla.

Los cambios no se realizarán en servicios reales ni se publicarán sin
autorización posterior. Queda pendiente aplicar y probar lo mismo contra los
servicios reales de acceso cuando se otorgue el permiso correspondiente.

| Campo | Valor requerido |
|---|---|
| Commit/tree | Rama `feat/h3req1-extended`; SHA del commit de evidencia H3 se registra al abrir el PR (ver "Aprobacion humana"). Push/PR protegido a `desarrollo` en ejecución tras autorización separada |
| Ambiente | Development local Docker: `studiamatch-dev` + `studiamatch-h2-pg-test` |
| Work package | `NONE_SUPERSEDED`; readiness PR `H3_PR_DEVELOPMENT_READY_LOCAL` |
| Criterio | `H3-CA4` |
| Fuente cliente | `SRC-REQ-002` via `ADENDA-REQ-EST-001-001` |
| Comandos | Build normal/mock PASS; suite CI-local 142 PASS; lint, tsc, pycompile y scanner PASS; harnesses H3 PG17 `h3_pg17_harness_ok` / `h3_pg17_harness_local_ok`; auditorías QA/seguridad/DB revalidadas sin HIGH/CRITICAL |
| Resultado esperado | Admin y user con límites definidos, 13 campos editoriales con ownership, cola paginada, edición allowlisted, optimistic locking, MFA TOTP `aal2`, invitación por correo, cambio de rol y activación/desactivación de miembros, auditoría, `admin.studiamatch.com`, 404 público, convergencia Free/local PG17 hacia Pro y no regresión pública |
| Resultado observado | UAT canónica 47/47 y 141/141 PASS con 0 retries y hostname 404 local funcional. Los bloqueadores HIGH/CRITICAL en CI, DB, MFA real, rollback y trazabilidad que detectó la auditoría previa quedaron resueltos en el ciclo de corrección local. Build normal/mock PASS; waiver static export superseded |
| Avance estimado | `H3_PR_DEVELOPMENT_READY_LOCAL`; 78.7% implementación y 57.7% validación contractual provisional (estimación, no readiness). H3-CA4.11 queda 100% estructural / 55% contractual hasta UAT real en Free/Certification |
| Artifacts/hashes | Evidencia canónica autocontenida y vinculada al candidato en `.context/evidencia/h3-expanded/` (141 screenshots); corridas estructurales previas (`h3-expanded-run-pass1/` y `run-pass2/`) preservadas fuera del repo como evidencia histórica |
| Desviaciones | `sessionStorage` sin waiver formal (pre-Certification). Static export revalidado PASS y waiver superseded. Resto de hallazgos HIGH/CRITICAL resueltos localmente |
| Aprobacion humana | Scope confirmado; commit + push + PR a `desarrollo` autorizados por instrucción humana separada. JIT Supabase Free/Auth, Cloudflare, certificación, merge y deploy siguen sin autorizar |

## Validacion Pre-Arranque

El alcance base de H3 se contrasta contra `SRC-REQ-002` mediante la atestación sanitizada versionada `ADENDA-REQ-EST-001-001`: panel `/admin`, cola de pendientes, edicion manual y publicacion. La ampliación está respaldada por la atestación sanitizada versionada `H3-EXPANDED-PROMPT-2026-08-30`, que autoriza únicamente ejecución local Docker hasta GO local. La fuente privada no se versiona ni se expone en PRs.

## Contrato de roles

- `/admin/` es una ruta compartida para los roles editoriales activos.
- `user` puede consultar la cola y completar únicamente campos incluidos en `missing_fields`.
- `admin` hereda las capacidades de `user` y además puede publicar, despublicar, archivar, actualizar `quality_status` y gestionar membresías.
- Un usuario autenticado sin membresía activa y un usuario inactivo quedan bloqueados.
- Toda mutación valida identidad y rol en la RPC y genera auditoría cuando corresponde.

## Checklist de cierre local

- Estado actual: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR). El checklist
  reabierto por las auditorías previas (`H3_PR_DEVELOPMENT_NO_GO`, histórico)
  quedó cerrado tras el ciclo de corrección local del 2026-09-02.
- Matriz estructural completa: 47 casos, 141 ejecuciones y 141 screenshots por
  corrida.
- Resultado: UAT canónica `PASS`, 47/47 casos y 141/141 ejecuciones con 0 retries;
  evidencia en `.context/evidencia/h3-expanded/`.
- Build normal/mock revalidado PASS; rutas admin exportadas; waiver static export
  superseded.
- Suite CI-local 142 PASS, `tsc`, lint, pycompile, credential scan, harnesses H3
  (`h3_pg17_harness_ok`, `h3_pg17_harness_local_ok`) y `git diff --check` PASS.
- Bloqueadores HIGH/CRITICAL resueltos: workflow/allowlist/db-gate H3, invariantes
  DB, MFA real, E2E, rollback y artifacts vinculados al candidato.
- `sessionStorage` sigue como riesgo pre-Certification sin waiver formal.
- Commit + push + PR protegido a `desarrollo` autorizados por instrucción humana
  separada; JIT Supabase Free/Auth, Cloudflare, certificación, merge y deploy
  permanecen bloqueados hasta sus aprobaciones separadas.
