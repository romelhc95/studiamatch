# TASK-H3-001 - HITO-003

| Campo | Valor |
|---|---|
| Estado | `READY_FOR_PROMPT_CONTINUA` |
| Work package | `SUPERSEDED` |
| Criterio | `H3-CA4` |
| Bloqueo | Requiere plan enumerado y prompt `continua`; JIT separado aplica a cambios remotos |

## Pendiente

1. Listar plan H3 y gates antes de cualquier build.
2. Confirmar gate fuente cliente contra `SRC-REQ-002` via `ADENDA-REQ-EST-001-001`.
3. Implementar `/admin/` compatible con static export solo despues de `continua`.
4. Probar acceso negativo anon/auth no admin.
5. Probar edicion allowlisted, optimistic locking, publicar/despublicar y auditoria.
6. Ejecutar UAT en Certification con evidencia Playwright desde H3.

Lista para el prompt `continua`; el pre-arranque documental queda validado contra fuente cliente. No implica autorizacion de cambios remotos.
