# Plan Vinculante Nuevo Pedido 2026-08-25

> Esta nota no crea autoridad fuera de Obsidian. La autoridad viva esta en
> [`estado_del_proyecto.md`](../estado_del_proyecto.md) y las reglas operativas
> estan en [`AGENTS.md`](../../AGENTS.md).

## Estado

```text
FASE = F11
ESTADO = H3_PR_DEVELOPMENT_READY_LOCAL
HISTORICAL_PRESTART_GATE = H3_READY_FOR_PROMPT_CONTINUA
AUTORIDAD = AGENTS.md + .context/estado_del_proyecto.md + Obsidian versionado
SOPORTE_TEMPORAL_RAIZ = REMOVED
DB = H2_PRO_EXPAND_VERIFIED_MAIN_PROMOTED
PRODUCTION_MUTATIONS = BLOCKED_WITHOUT_JIT
```

Para cualquier nuevo desarrollo con requerimiento cliente, antes de iniciar y al cerrar un hito o task vinculado al requerimiento debe validar sus criterios contra la fuente privada cliente mediante atestacion sanitizada versionada.
El documento privado no se versiona ni se expone en PRs.
Si el gate falla, se corrige primero la atestacion sanitizada y no se ejecuta el hito siguiente.
La ampliación H3 está respaldada por la atestación sanitizada `H3-EXPANDED-PROMPT-2026-08-30`, que autoriza únicamente ejecución local Docker hasta GO local. Supabase writes, Auth remoto, Cloudflare, DNS, push, PR, merge, deploy, schedules y `workflow_dispatch` requieren aprobaciones separadas.
Pro es la fuente autoritativa de schema, tipos, constraints, campos y últimas migraciones H2; Free y PostgreSQL 17 local deben converger hacia Pro. No se usa Free/local para modificar Pro ni se sincronizan datos operativos como mecanismo normal. Las migraciones H3 ya validadas en Docker se conservan y reutilizan como candidato; deben rebasarse sobre la forma Pro y solo requieren deltas idempotentes si una incompatibilidad es demostrada.

Todo cambio funcional, DB, UI, pipeline o despliegue debe tener transicion
transparente documentada: `expand -> compatibilidad -> deploy -> contract`.
Durante construccion y promocion se mantiene el comportamiento legacy necesario
para que la aplicacion siga funcionando sin degradar funcionalidad. Tras estabilizar en produccion se
contrae el soporte legacy y queda activo solo el nuevo contrato solicitado. El
cierre de hito/task exige rollback y evidencia de no degradacion funcional.

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

## Gate De Transicion Transparente

Cada cambio debe declarar:

1. `expand`: objetos, rutas o contratos nuevos agregados sin romper el legado.
2. `compatibilidad`: comportamiento legacy preservado durante construccion,
   certificacion y ventana de rollback.
3. `deploy`: evidencia de que la aplicacion sigue funcionando durante la
   promocion.
4. `contract`: condicion objetiva para retirar legacy y dejar solo el contrato
   nuevo en produccion.
5. Rollback: camino probado o documentado para volver al estado funcional previo
   sin perdida de datos.

Si alguno de estos puntos falta, el cambio queda en `NO-GO` para promocion.

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
promocion a Pro solo despues de Certification y nuevo JIT. Para produccion,
Pro debe expandirse y verificarse antes del deploy frontend: el frontend legacy
de `main` debe seguir leyendo `courses` mientras el frontend H2 queda preparado
para `courses_public_effective`; la revocacion de lectura directa y retiro de
cohorte son fases `contract` posteriores, no parte del `expand` inicial.

## H3 Admin

`admin.studiamatch.com` como hostname canónico exclusivo del panel, protegido por
Cloudflare Access y compatible con `output: 'export'`. Debe usar Supabase Auth con
email/password y MFA TOTP obligatorio para `admin` y `user`; las operaciones
sensibles requieren sesión `aal2`. Signup público deshabilitado, membresía
`admin_members`, datos y mutaciones protegidos por RLS/RPC, cola por cursor,
filtros por estado editorial/calidad, edición allowlisted, optimistic locking por
`version`, publicar/despublicar/archivar con auditoría atómica y conflicto visible
entre sesiones.

Contrato de roles confirmado: el hostname administrativo es compartido por los
roles editoriales. Un `user` activo puede consultar la cola y completar únicamente
campos incluidos en `missing_fields`. Un `admin` activo hereda las capacidades de
`user` y además puede publicar, despublicar, archivar, actualizar `quality_status`
y gestionar membresías. Un usuario autenticado sin membresía y un usuario inactivo
quedan bloqueados. El admin puede invitar usuarios por correo mediante una Edge
Function protegida, cambiar el rol y activar/desactivar cualquier miembro `admin` o
`user` mediante botón o checkbox; nunca se expone `service_role` y siempre se
conserva al menos un admin activo.

`studiamatch.com/admin/` debe responder 404 y no servir el panel. El despliegue,
DNS, Access, redirect URLs Auth y variables de origen requieren JIT separado.

### Estado de cierre local H3 actualizado

El estado vigente es `H3_PR_DEVELOPMENT_READY_LOCAL`. La auditoría de readiness
del 2026-09-02 dejó inicialmente `H3_PR_DEVELOPMENT_NO_GO` (histórico): dos
corridas UAT reportaban 47/47 y 141/141 PASS, pero se clasificaron como evidencia
estructural insuficiente para readiness. El ciclo de corrección local y la
revalidación documental del 2026-09-03 resolvieron los bloqueadores locales
(workflow/allowlist/db-gate H3, invariantes DB, regresión PG17 A6/A13, MFA local,
cobertura E2E, rollback y artifacts vinculados al candidato) y mantienen la UAT
canónica en **47/47 casos y 141/141 ejecuciones PASS, 141 screenshots, 0 retries**,
evidencia en `.context/evidencia/h3-expanded/`. Build normal/mock revalidado PASS;
waiver static export superseded.

Commit + push + PR protegido a `desarrollo` fueron autorizados por instrucción
humana separada. JIT-A Supabase Free/Auth y JIT-B Cloudflare/DNS ya tienen
acciones parciales documentadas: JIT-A conserva A6/A13 FAIL históricos sobre el
payload hasta `20260902`, y JIT-B conserva E1/E3/E4/E8 PASS con E2/E5/E6/E7
pendientes. La aplicación de `20260903`, configuración Auth, dependencia build,
Certification, merge y deploy permanecen bloqueados hasta sus aprobaciones
separadas. `sessionStorage` mantiene su riesgo pre-Certification.

### Pre-arranque H3

Antes de cualquier plan o build se debe listar el plan ejecutable, sus gates y
la evidencia esperada. La implementacion funcional inicia solo despues del
prompt humano `continua`. El prompt no sustituye JIT para Supabase/Auth,
DDL/DML, push, PR, merge o deploy. Cada cambio debe cerrar con checks locales
en Docker, pilares, criterios de aceptacion, documentacion Obsidian y
promocion protegida `desarrollo -> certificacion -> main`.

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

H2/H3: matriz RLS `anon`, `authenticated`, user, admin y service/CI; pipeline
incapaz de publicar; preservación de overrides; auditoría append-only; segunda
corrida `NOOP`; más de 1000 filas; conflictos de edición; casos Auth positivos y
negativos; ownership y transporte de los 13 campos editoriales.

H3 ampliado: MFA TOTP obligatorio para admin/user, `aal1` rechazado y `aal2`
permitido en mutaciones sensibles; enrollment, challenge, verify, renovación,
revocación y último admin protegido; invitación por correo sin `service_role` en
cliente; cambio de rol y activación/desactivación de cualquier miembro `admin` o
`user` mediante botón o checkbox, auditados; `admin.studiamatch.com` permitido por
Access y `studiamatch.com/admin/` con HTTP 404; Pro como baseline autoritativo y
Free/local PG17 convergentes en schema, campos y migraciones; second-run `NOOP`.

La prueba de Cloudflare Access/MFA perimetral requiere JIT Cloudflare y no puede
simularse como evidencia de producción únicamente con el mock local. Supabase
Auth MFA y el enforcement `aal2` deben probarse además en Free con JIT separado.

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
6. Plan H3 listado y prompt `continua` recibido.
7. Cierre local ampliado de H3 con campos, MFA, hostname, invitaciones y UAT completa: 47 casos lógicos únicos, 141 ejecuciones en tres viewports y dos corridas estables.
8. Preparación local del paquete H3 para PR usando la plantilla versionada, sin commit, push ni creación remota hasta aprobación humana separada.
9. Con `H3_LOCAL_EXPANDED_GO`, autorización humana separada para commit + push + PR H3 protegido a `desarrollo`; el PR se abre antes de las pruebas Free para incorporar su evidencia al mismo candidato sin mergearlo.
10. JIT independiente Supabase Free/Auth: inventario read-only, migraciones H3, MFA TOTP, Edge Function protegida de invitación y validación real. Cloudflare DNS/Access permanece en otra aprobación JIT y no se agrupa por defecto.
11. Incorporar resultados Free/Auth al PR H3, repetir validaciones y `security-audit`; merge a `desarrollo` solo mediante aprobación humana posterior.
12. UAT en Certification y promoción protegida.
11. PR H1: readiness operacional.
12. JIT individual para FG1, FG2 y FG3.
13. PR H4: Home y CA7.
14. PR H5: Resultados.
15. Certificacion visual y funcional.
16. Promocion final a `main`.

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
