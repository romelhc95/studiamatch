# TASK-H3-001 - HITO-003

| Campo | Valor |
|---|---|
| Estado | `PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION` |
| Work package | `SUPERSEDED` |
| Criterio | `H3-CA4` |
| Bloqueo | Ejecucion requiere instruccion humana separada despues del gate fuente cliente |

## Pendiente

1. Confirmar gate fuente cliente contra `SRC-REQ-002` via `ADENDA-REQ-EST-001-001`.
2. Implementar `/admin/` compatible con static export solo tras instruccion humana separada.
3. Probar acceso negativo anon/auth no admin.
4. Probar edicion allowlisted, optimistic locking, publicar/despublicar y auditoria.
5. Ejecutar UAT en Certification con evidencia Playwright desde H3.

Bloqueada para ejecucion hasta instruccion humana separada. El pre-arranque documental queda validado contra fuente cliente.
