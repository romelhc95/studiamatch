# Agent Dispatcher — Politica De Integracion

## Estado
Implementado como herramienta asistiva en `scripts/maintenance/agent_dispatcher.py`. No esta activado como gate bloqueante ni ejecuta agentes automaticamente.

## Objetivo
Agregar un despachador de agentes que reduzca errores de handoff y enrute roles de implementacion sin reemplazar el gate deterministico.

## Regla Principal
El dispatcher no decide estado de release. El estado valido sigue saliendo exclusivamente de `scripts/maintenance/release_gate.py`, el manifest y las evidencias JSON.

## Entradas
- Manifest de release.
- Estado derivado por `release_gate.py`.
- Tarea aprobada de `.context/backlog_tareas/<requerimiento>/` cuando se usa `mode=implementation`.
- Hito aprobado por Usuario/PM cuando se usa `mode=implementation`.
- Archivos modificados.
- Dominio principal: frontend, pipeline, Supabase, DevOps, datos, QA o seguridad.

## Salidas
- Rol siguiente sugerido.
- Agente recomendado.
- Roles de implementacion para el hito aprobado.
- Agentes de apoyo sugeridos segun dominios de archivos modificados.
- Validaciones minimas.
- Evidencia JSON esperada conforme a `schemas/role-evidence.schema.json`.

## Restricciones
- No puede autorizar `AUTHORIZE_PRODUCTION`, `AUTHORIZE_RESUME` ni `PROMOTE`.
- No puede crear alcance nuevo ni implementar fuera del hito/tarea aprobados.
- No puede emitir evidencia por un rol si el mismo actor implemento el cambio.
- No puede modificar `release-manifest.json` sin registrar una nueva revision permitida por schema.
- No puede saltar `security-auditor` cuando hay DB, RLS, auth, secrets, workflows o integraciones.
- No puede crear agentes locales en `.opencode/agents/` salvo aprobacion explicita.

## Uso Review

```bash
PYTHONPATH=/app python3 scripts/maintenance/agent_dispatcher.py \
  --manifest .context/evidencias/releases/pre-hito1/release-manifest.json \
  --stage structure \
  --changed-files changed-files.txt
```

La salida es JSON y puede ser consumida por el agente gestor. Si `release_gate.py` falla o el rol siguiente no es soportado, devuelve `NO_GO` con handoff a `developer`.

## Uso Implementation

```bash
PYTHONPATH=/app python3 scripts/maintenance/agent_dispatcher.py \
  --mode implementation \
  --task .context/backlog_tareas/req_hito_2/tarea_123_catalogo.md \
  --approved-hito "Hito 2" \
  --changed-files changed-files.txt
```

Reglas de `mode=implementation`:

- La tarea debe tener `estado` aprobado (`aprobada`, `aprobado`, `approved` o `en_ejecucion`).
- La tarea debe estar en `.context/backlog_tareas/<requerimiento>/tarea_NNN_<slug>.md`.
- El `hito` de la tarea debe coincidir exactamente con `--approved-hito`.
- Si la tarea declara archivos concretos en `Archivos afectados`, los changed files deben estar dentro de ese alcance.
- Devuelve `NO_GO` ante tarea pendiente, hito distinto o archivos fuera de alcance.
- Produce `primary_agent`, `implementation_roles`, `support_agents`, `required_checks` y `forbidden_scope`.
- Respeta `skill_principal`, `skills_apoyo` y `gate_obligatorio` cuando declaran agentes conocidos.

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
El dispatcher puede usarse manualmente para orientar handoffs y roles de implementacion. Para convertirlo en check informativo o bloqueante de CI se requiere una aprobacion posterior explicita.
