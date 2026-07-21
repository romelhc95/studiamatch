# Politica De Higiene Del Repositorio

## Objetivo
Mantener el repositorio limpio, reproducible y auditable sin perder trazabilidad operativa.

## Ramas Permanentes
Se mantienen tres ramas permanentes porque representan ambientes distintos y protegidos:

| Rama | Ambiente | Supabase | Proposito |
|---|---|---|---|
| `desarrollo` | Development | Free (`aqrldlmlszjtgpqiegaa`) | Integracion activa y pruebas iniciales. |
| `certificacion` | Certification | Free (`aqrldlmlszjtgpqiegaa`) | QA formal antes de produccion. |
| `main` | Production | Pro (`xwhtiqmboljkshrtviyw`) | Produccion y despliegue publico. |

## Ramas Temporales
- `feat/*`: implementacion aprobada desde `desarrollo`.
- `fix/*`: correcciones puntuales.
- `promote/*`: promocion controlada entre ramas protegidas.
- `release/hito-N`: congelamiento opcional del alcance cuando `desarrollo` contiene cambios futuros no liberables.

Las ramas temporales se eliminan despues de mergear, cerrar o reemplazar su PR. Antes de eliminarlas debe existir una nota en changelog o en el PR que indique si el trabajo fue mergeado, reemplazado o desestimado.

## Archivos Permitidos En Git
- Codigo de aplicacion y pipeline.
- Migraciones SQL versionadas.
- Workflows CI/CD vigentes.
- Scripts recurrentes de operacion, auditoria, migracion o release.
- Tests de contrato/regresion que se ejecutan mas de una vez.
- Documentacion Obsidian bajo `.context/` que sea fuente de verdad o evidencia canonica.

## Archivos No Permitidos En Git
- Scripts one-shot de diagnostico, backfill, exploracion o pruebas manuales.
- Launchers locales (`.vbs`, `.bat`, `.ps1`) sin uso CI/recurrente.
- Dumps, CSV, logs, capturas crudas o outputs de herramientas.
- Pruebas que dependen de datos efimeros o de una ejecucion unica.
- Credenciales, tokens, URLs firmadas o secretos.

## Uso De `desestimado/`
`desestimado/` esta ignorado por Git y sirve para conservar localmente material historico o descartado sin contaminar el repositorio. Si un archivo versionado se retira por ser one-shot, el commit debe eliminarlo del repo y registrar el motivo en changelog. La copia local en `desestimado/` no viaja a GitHub.
