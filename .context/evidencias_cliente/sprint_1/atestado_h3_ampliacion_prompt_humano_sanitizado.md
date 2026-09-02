# Atestación H3 ampliación — prompt humano

Estado: `HUMAN_SCOPE_ATTESTED_LOCAL_EXECUTION`

| Campo | Valor |
|---|---|
| ID | `H3-EXPANDED-PROMPT-2026-08-30` |
| Fuente de decisión | `PROMPT-HUMANO-CONTINUA-H3REQ1` |
| Fuente base | `SRC-REQ-002` mediante `ADENDA-REQ-EST-001-001` |
| Autorización | Ejecución local hasta GO local |
| Alcance | Ownership, transporte de campos, MFA TOTP, `aal2`, invitaciones, membresías, hostname, 404 público y convergencia Pro/local |
| Ambiente autorizado | Desarrollo local Docker; cualquier validación read-only remota requiere instrucción humana separada |
| Exclusiones | Supabase writes, Auth remoto, Cloudflare real, DNS, push, PR, merge, deploy, schedules y `workflow_dispatch` |
| Fuente privada | Permanece fuera de Git; esta atestación no afirma verificación de una fuente privada adicional |
| Sanitización | Sin emails, PII, tokens, passwords, API keys, hashes inventados ni contenido privado del cliente |

La autorización del alcance ampliado proviene del prompt humano actual
`CONTINUA H3REQ1`. Esta atestación habilita únicamente la ejecución local y no
autoriza acciones remotas, promoción protegida ni cambios en ambientes compartidos.
