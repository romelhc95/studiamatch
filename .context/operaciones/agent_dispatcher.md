# Agent Dispatcher — Politica De Integracion

## Estado
Implementado como herramienta asistiva en `scripts/maintenance/agent_dispatcher.py`. No esta activado como gate bloqueante ni ejecuta agentes automaticamente.

## Objetivo
Agregar un despachador de agentes que reduzca errores de handoff sin reemplazar el gate deterministico.

## Regla Principal
El dispatcher no decide estado de release. El estado valido sigue saliendo exclusivamente de `scripts/maintenance/release_gate.py`, el manifest y las evidencias JSON.

## Entradas
- Manifest de release.
- Estado derivado por `release_gate.py`.
- Archivos modificados.
- Dominio principal: frontend, pipeline, Supabase, DevOps, datos, QA o seguridad.

## Salidas
- Rol siguiente sugerido.
- Agente recomendado.
- Agentes de apoyo sugeridos segun dominios de archivos modificados.
- Validaciones minimas.
- Evidencia JSON esperada conforme a `schemas/role-evidence.schema.json`.

## Restricciones
- No puede autorizar `AUTHORIZE_PRODUCTION`, `AUTHORIZE_RESUME` ni `PROMOTE`.
- No puede emitir evidencia por un rol si el mismo actor implemento el cambio.
- No puede modificar `release-manifest.json` sin registrar una nueva revision permitida por schema.
- No puede saltar `security-auditor` cuando hay DB, RLS, auth, secrets, workflows o integraciones.
- No puede crear agentes locales en `.opencode/agents/` salvo aprobacion explicita.

## Uso

```bash
PYTHONPATH=/app python3 scripts/maintenance/agent_dispatcher.py \
  --manifest .context/evidencias/releases/pre-hito1/release-manifest.json \
  --stage structure \
  --changed-files changed-files.txt
```

La salida es JSON y puede ser consumida por el agente gestor. Si `release_gate.py` falla o el rol siguiente no es soportado, devuelve `NO_GO` con handoff a `developer`.

## Mapeo Inicial
| Dominio | Agente principal | Apoyo obligatorio |
|---|---|---|
| Frontend publico | `frontend-architect` | `accessibility`, `seo` si afecta indexacion |
| Pipeline Python | `pipeline-engineer` | `qa-test-engineer` |
| Supabase/PostgreSQL/RLS | `supabase-architect` | `security-auditor` |
| CI/CD/GitHub/Cloudflare | `devops-release-manager` | `security-auditor` |
| Datos/ROI/ranking | `data-quality-analyst` | `qa-test-engineer` |
| Cierre de hito | `qa-test-engineer` | `security-auditor` si aplica |

## Estado De Activacion
El dispatcher puede usarse manualmente para orientar handoffs. Para convertirlo en check informativo o bloqueante de CI se requiere una aprobacion posterior explicita.
