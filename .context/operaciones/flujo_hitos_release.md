# Flujo De Hitos Y Ambientes

## Objetivo
Permitir desarrollo continuo por hitos sin desplegar a produccion cambios no aprobados.

## Ambientes Permanentes
StudIAMatch mantiene tres ramas permanentes porque representan ambientes protegidos distintos:

| Rama | GitHub Environment | Supabase | Regla |
|---|---|---|---|
| `desarrollo` | `Development` | Free (`aqrldlmlszjtgpqiegaa`) | Integracion activa con PR y `security-audit`. |
| `certificacion` | `Certification` | Free (`aqrldlmlszjtgpqiegaa`) | QA formal sobre el paquete aprobado antes de Pro. |
| `main` | `Production` | Pro (`xwhtiqmboljkshrtviyw`) | Produccion; requiere aprobacion humana y gates Pro. |

Las ramas temporales (`feat/*`, `fix/*`, `promote/*`, `release/*`) no son ambientes. Deben eliminarse o cerrarse cuando su PR haya sido mergeado, reemplazado o desestimado.

## Posta SDLC
El cierre se deriva de evidencia estructurada; ningun modelo, script ni persona que ejecuta una correccion puede certificar su propio trabajo.

- Cada rol emite un JSON conforme a `schemas/role-evidence.schema.json`.
- El estado valido lo deriva `scripts/maintenance/release_gate.py`.
- Obsidian documenta el proceso, pero no sustituye el gate JSON.
- El dispatcher asistivo puede sugerir el siguiente rol, pero no autoriza promociones.

## Flujo Normal

```text
feat/* -> PR -> desarrollo -> promote/* -> certificacion -> main
```

`certificacion` comparte Supabase Free con `desarrollo`, por lo que durante ventanas de QA debe congelarse cualquier escritura o cambio DB no liberable.
