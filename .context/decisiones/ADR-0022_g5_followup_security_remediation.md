# ADR-0022 - G5 Follow-Up Security Remediation

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED` |
| Fecha | 2026-08-16 |
| Subfase | `F10.9` |
| Alcance | PR L repository-only post-merge PR #394 |
| Gate actual | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust actual | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected actual | `IMPLEMENTED_DISABLED_NOT_CONFIGURED` |

## Contexto

PR #394 queda registrado como `MERGED_POST_MERGE_VERIFIED_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED`:

```text
candidate_commits = 7861af0cf94b726d6ce5fadad9ffb6c2274fdcaa, 03bab905901f62dba7631a9fe0a87290d70802d9, 82ef6e92c125040cededb4a648d1eedd6d519ecf
merge = 25be9caffe5674156c7515735a15ad45c5ad22e2
tree = 9f81f71bdabb2012ab593b1999cf4df92fa712eb
security = 31968991218=PASS
f9_7_run = 31968990202=PASS
focused_g5_job = 95218353795=PASS
f9_7_job = 95218447778=PASS
run_attempt=1
```

La remediacion PR K cerro hallazgos residuales, pero el follow-up detecto que el boundary aceptaba cadenas lineales genericas de commits. Esa flexibilidad no debe convertirse en autorizacion reutilizable para futuras remediaciones.

## Decision

El boundary conserva PR #394 unicamente por identidad historica exacta e inmutable:

- Tres commits exactos, en orden: `7861af0cf94b726d6ce5fadad9ffb6c2274fdcaa`, `03bab905901f62dba7631a9fe0a87290d70802d9`, `82ef6e92c125040cededb4a648d1eedd6d519ecf`.
- Base exacta PR #393: `51aaac5d289226b1f8f16de1daf69a16a084d585`.
- Merge protegido exacto PR #394: `25be9caffe5674156c7515735a15ad45c5ad22e2` / tree `9f81f71bdabb2012ab593b1999cf4df92fa712eb`.
- Cualquier futura remediacion repository-only debe ser un unico commit directo desde su base congelada.

El broker y sus pruebas quedan endurecidos asi:

- `Link` headers se rechazan si son malformados, ambiguos, duplicados o inesperados; `rel=next` siempre produce STOP.
- Los fixtures de installation token no derivan permisos de la solicitud que estan validando; responden con permisos read-only fijos.
- La confirmacion terminal prueba mutaciones durante cada lectura terminal: workflow run, job/check y deployment status.

## Riesgo Residual

La confirmacion terminal reduce la ventana TOCTOU entre Snapshot B y CAS, pero no demuestra autoridad atomica global multi-endpoint. GitHub expone workflow run, jobs/checks, deployments, approvals, branch, environment y commit/blob como lecturas separadas; por tanto queda una carrera residual multi-endpoint documentada como `DOCUMENTED_NO_FULL_ATOMICITY_CLAIM`.

Esta decision no declara atomicidad completa del trust operacional. El CAS del Durable Object sigue siendo single-use para el receipt local, pero la autoridad externa completa requiere un rediseño futuro si se quiere reducir la carrera multi-endpoint a una fuente atomica.

## Backlog No Ejecutable

Se registra `BK-F10.9-G5-ATOMIC-AUTHORITY` como backlog no ejecutable y cotizable para un rediseño futuro de autoridad atomica. No suma avance al Hito 1, no cambia F10.9/G5, no autoriza implementacion y requiere estimacion y aprobacion del cliente antes de cualquier trabajo.

## Consecuencias

- E2 queda `NOT_EXECUTED` con `E2_STOP_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED`.
- E3, E4, E4A, E4B, E5 y E6 permanecen `NOT_EXECUTED`.
- El endpoint sigue inexistente y `G5_TRUST_RUNTIME_ENABLED` sigue ausente o false.
- No se configura GitHub App, private key, installation ID, Cloudflare, endpoint, OIDC live, Production, Supabase, SQL, writers ni schedules.
- Hito 1 `60%`, F10.9 `38%` y G5 `50%` permanecen sin cambio.
