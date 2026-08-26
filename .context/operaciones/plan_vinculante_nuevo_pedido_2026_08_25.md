# Plan Vinculante Nuevo Pedido 2026-08-25

> Esta nota no crea autoridad fuera de Obsidian. La autoridad viva esta en
> [`estado_del_proyecto.md`](../estado_del_proyecto.md) y las reglas operativas
> estan en [`AGENTS.md`](../../AGENTS.md).

## Estado

```text
FASE = F11
ESTADO = H2_MERGED_TO_CERTIFICACION_CI_GREEN
AUTORIDAD = AGENTS.md + .context/estado_del_proyecto.md + Obsidian versionado
SOPORTE_TEMPORAL_RAIZ = REMOVED
DB = FREE_H2_VALIDATED_BLOCKED_FOR_NEW_DDL_DML_WITHOUT_JIT
PRODUCTION_MUTATIONS = BLOCKED_WITHOUT_JIT
```

Todo cierre de hito o task vinculado al requerimiento debe validar sus criterios
contra la fuente privada cliente mediante atestacion sanitizada versionada. El
documento privado no se versiona ni se expone en PRs.

## Hitos Redefinidos

| Hito | Alcance vinculante | Criterios | Dependencia |
|---|---|---|---|
| H1 | Automatizacion segura y reactivacion gradual de FG1/FG2/FG3 | CA1 | H2 y H3 aceptados |
| H2 | Modelo editorial, calidad y pipeline tolerante a incompletos | CA2, CA3 | Intake y JIT DB |
| H3 | Administracion editorial autenticada | CA4 | H2 aceptado |
| H4 | Home publica y documentacion tecnica | CA5, CA6, CA7, CA13H | Contrato H2 estable |
| H5 | Resultados publicos, filtros y cards | CA8-CA12, CA13R | Contrato H2 estable |

El orden numerico no es el orden de ejecucion:

```text
Intake documental
-> H2
-> H3
-> H1
-> H4
-> H5
```

El cierre historico anterior de H1 se preserva en actas, ADR y evidencias, pero
deja de representar el H1 activo del nuevo pedido. Sus waivers no cierran CA1
nuevamente.

## Activacion Documental

1. Crear rama desde el `origin/desarrollo` vigente antes de promover cambios.
2. Verificar nuevamente los tres hashes originales si los archivos fuente estan disponibles.
3. Publicar fuentes solo si pasan inspeccion final de metadatos y redistribucion.
4. Mantener HTML como referencias, nunca servirlos desde `web/public`.
5. Mantener manifiesto con fuente, fecha, hash, proposito y precedencia.
6. Corregir `.gitignore` solo cuando los tres archivos esten presentes e inspeccionados.
7. Actualizar indice, estado vivo, `AGENTS.md` y notas Obsidian.
8. Retirar definitivamente el soporte temporal raiz.
9. Preservar estado anterior como historia no ejecutable.
10. Redefinir formalmente Hitos 1-5 conforme a este plan.

## Gate De Alcance

| Alcance | Paths autorizables |
|---|---|
| Intake | fuentes, `.context/**`, tests de gobernanza; scanner y workflow de seguridad solo con instruccion humana separada o excepcion declarada en PR documental |
| H2 | migraciones nuevas, pipeline afectado, backfill, tests y documentacion DB |
| H3 | `/admin`, cliente Auth, RPC/migracion admin, tests y dependencias fijadas |
| H1 | workflows FG1-FG3, preflight, tests operativos y runbooks |
| H4 | Home, componentes compartidos, estilos, tests y documentacion |
| H5 | Resultados, filtros, rutas, componentes, tests y documentacion |

`security-audit` debe rechazar archivos fuera del alcance activo, credenciales,
PII, fuentes con hashes divergentes, DOCX con macros, firmas, embeddings o
revisiones, fuentes copiadas dentro del bundle web, cambios DB mezclados con
hitos frontend no autorizados, workflows invalidos o schedules activados por
implicacion.

## H2 Modelo Editorial

Mantener `courses` como base producida por pipeline y agregar una capa editorial
separada: `editorial_field_definitions`, `course_editorial_state`,
`course_editorial_audit` y una vista efectiva publica con prioridad `override
manual > valor pipeline`.

Estados editoriales: `draft`, `pending_review`, `published`, `archived`.
Estados de calidad: `pending`, `complete`, `blocked`.
Ownership: `pipeline_owned`, `manual_owned`, `computed`,
`hybrid_manual_preferred`.

Reglas obligatorias: el pipeline no publica, no cambia patrocinio, no sobreescribe
overrides manuales, conserva incompletos con identidad minima, calcula
`missing_fields` de forma persistente o deterministica, backfill paginado,
reanudable e idempotente, segunda corrida `NOOP`, no elimina leads legacy sin
evaluar datos, revoca captura publica, retira llamadas frontend relacionadas y
garantiza unicidad global de slug antes de adoptar `/programas/[slug]`.

Seguridad Supabase: RLS en toda tabla expuesta, grants explicitos, vista publica
con `security_invoker`, implementacion privilegiada fuera del schema expuesto,
RPC publica minima con `EXECUTE` revocado a `PUBLIC` y grants explicitos,
autorizacion via `auth.uid()` y auditoria append-only sin `UPDATE`, `DELETE` ni
`TRUNCATE`. Diagnosticar y documentar el estado de `public.exec_sql(text)` antes
de aceptar separacion pipeline/editor; cualquier creacion, reemplazo o grant
requiere JIT DDL separado.

Validacion: contratos estaticos/offline, JIT DDL en Supabase Free, backfill JIT
DML separado, matriz RLS real por rol, advisors, segunda corrida `NOOP` y
promocion a Pro solo despues de Certification y nuevo JIT.

## H3 Admin

Ruta estatica `/admin/` compatible con `output: 'export'`. Debe usar Supabase
Auth con email/password para usuarios preprovisionados, signup publico
deshabilitado, membresia `admin_members`, datos y mutaciones protegidos por
RLS/RPC, cola por cursor, filtros por estado editorial/calidad, edicion
allowlisted, optimistic locking por `version`, publicar/despublicar/archivar con
auditoria atomica y conflicto visible entre sesiones.

Contrato de credenciales: API key moderna solo en `apikey`; JWT de sesion Auth en
`Authorization: Bearer`; publishable/secret keys nunca como bearer token.

## H1 Automatizacion

Readiness: corregir preflight para distinguir `blocked`, `preflight-only` y
ejecucion funcional; impedir que corridas con estaciones skipped cierren evidencia
funcional; validar FG1, FG2 y FG3 con `actionlint`; corregir concurrency group de
FG3; alinear frecuencia FG2 entre workflow y documentacion; reemplazar textos
historicos del job de auditoria por resultados verificables; confirmar
`pipeline_ready`, limites, entornos y rollback.

Activacion JIT secuencial:

```text
FG1 -> observar -> repausar/evaluar
FG2 -> observar -> repausar/evaluar
FG3 -> observar -> repausar/evaluar
schedules ordinarios
```

Cada workflow requiere autorizacion separada para habilitarlo, cambiar variables
de environment, ejecutar canary o dispatch mutable, despausar writers o mantener
schedule activo. Los tres workflows no se activan simultaneamente.

## H4 Home

Separar Home del catalogo actual y seguir el lenguaje visual aprobado: Inter,
paleta `#0A2540`, `#2D6BE4`, hero con gradiente, instituciones, 6 programas
patrocinados, 3 programas abiertos organicos, 3 paises, conteos reales, logos
cero formularios o `POST /leads` y ROI ausente. Si no existen seis programas
reales patrocinados en el dataset editorial, H4 queda bloqueado; no se inventan
placeholders para cerrar criterio.

## H5 Resultados

Rutas recomendadas: `/`, `/resultados/`, `/resultados/?q=...`,
`/programas/[slug]/`.

Contrato query string: `q`, `disponibilidad`, `area`, `modalidad`, `pais`,
`precio`, `duracion`, `page`, `orden`.

Debe usar URL como fuente de verdad, back/forward con estado restaurado, sticky
search, chips removibles, limpiar todo, sidebar desktop, drawer movil accesible,
seis filtros exactos, contador total filtrado, patrocinados primero, desempate
determinista, paginacion, loading/empty/error/retry, `A consultar` sin precio,
`Sin confirmar` sin fecha, ruta canonica `/programas/[slug]`, redirects desde
`/courses/...` y cero captura de leads o egress comercial.

Patrocinio y disponibilidad son dimensiones independientes, no cuatro estados
mutuamente excluyentes.

## Testing

Offline y Docker: credential scan, Python compile, pytest de seguridad,
contratos y pipeline, ESLint, TypeScript, static build, actionlint y shellcheck.

H2/H3: matriz RLS `anon`, `authenticated`, non-admin, admin y service/CI;
pipeline incapaz de publicar; preservacion de overrides; auditoria append-only;
backfill reanudable y segundo run `NOOP`; mas de 1000 filas; conflictos de
edicion; casos Auth positivos y negativos.

H4/H5: unit tests para filtros, orden, formatos, query string y contador;
Playwright desktop/mobile; network assertions contra leads, email, webhook y
terceros no autorizados; snapshots visuales 1440x900, 768x1024 y 390x844;
navegacion por teclado y focus; sin overflow entre 320 y 1440 px; comparacion
humana separada para CA13H y CA13R.

Los specs Playwright actuales deben reemplazarse si exigen ROI, formularios de
leads o rutas `/courses`, porque son incompatibles con el nuevo contrato.

## Secuencia De Entrega

1. PR documental: fuentes, autoridad, hitos y gate de alcance.
2. PR H2: migraciones, pipeline y pruebas.
3. JIT Free: inventario, DDL, backfill y RLS.
4. Promocion H2 por `desarrollo -> certificacion -> main`.
5. JIT Pro de H2.
6. PR H3: Auth, RPC y `/admin`.
7. UAT en Certification y promocion protegida.
8. PR H1: readiness operacional.
9. JIT individual para FG1, FG2 y FG3.
10. PR H4: Home y CA7.
11. PR H5: Resultados.
12. Certificacion visual y funcional.
13. Promocion final a `main`.

Push, PR, merges, mutaciones DB, configuracion Auth, schedules, writers y deploys
requieren instrucciones humanas separadas.

## Stop Conditions

- Aparece un secreto, PII o valor credential-like.
- Falta una fuente que se intenta versionar o su hash no coincide.
- Se intenta publicar una fuente no inspeccionada.
- Se intenta servir fuentes desde `web/public`.
- Se mezclan DB/H2 con frontend/H4/H5 sin autorizacion.
- Se requiere mutacion Supabase, DB Sync, canary, writer, schedule, deploy o
  decision humana adicional.
