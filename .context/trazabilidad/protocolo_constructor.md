# Protocolo del constructor: del estado al cambio con impacto conocido

Entrada: [índice principal](../indice.md) y [estado operativo](../estado_del_proyecto.md).
Este protocolo aplica a todo el proyecto, sin sustituir AGENTS/cliente/JIT. Se incorpora
al ciclo retroalimentado existente y no crea gobierno nuevo ni índice paralelo.

## Antes de editar

1. Leer estado, alcance cliente/atestación y fase autorizada; listar tareas/gates.
2. Confirmar checkout/branch/HEAD/WIP y runtime servido. Preservar original/untracked;
   no usar checkout anidado o `/app` como candidato por defecto.
3. Localizar la ruta exacta en el [registro fuente-componente](registro_fuentes_componentes.json)
   y abrir el componente/anchor. Inspeccionar imports/llamadas RPC, SQL/includes, tablas,
   endpoints/config y workflows consumidores en ambas direcciones, en candidato y original
   de solo lectura; usar Git local para reconstruir historia cuando ayude.
4. Seleccionar los contratos y la ruta de cambio descritos en la ficha del módulo. Si la
   fuente o la relación no están detalladas, investigarlas antes; arista no demostrada no
   equivale a ausencia.
5. Comparar [pruebas y evidencia](../componentes/pruebas_evidencia.md): suite/caso, input,
   fixture, runner, grado y resultado preservable. Renovar solo las validaciones afectadas.
6. Presentar ficha breve en conversación; guardarla después en evidencia del ciclo, no
   crear otro plan equivalente. No pedir `continua` adicional para cada lectura del mismo
   ciclo; sí esperar señal funcional y autorizaciones protegidas cuando correspondan.

### Ficha previa mínima

```text
Objetivo/criterio cliente:
Archivos y dominios:
Cambio de contrato (K) o solo implementación/tooling:
Dependencias y consumidores directos/inversos:
Comportamiento que debe preservarse:
Pruebas concretas / grado / fixtures:
Evidencia preservada y evidencia a renovar (causa):
Transición expand -> compatibilidad -> deploy -> contract y rollback:
Permisos: autoría local vs SQL/recursos/remotos/protegidos:
Desconocidos e hipótesis todavía no demostradas:
Gate de cierre y siguiente decisión si FAIL:
```

Plantilla no es evidencia completada. Antes de cerrar rellenar con resultados reales;
no conservar prompts/pendientes como resultados en un PR.

## Durante implementación/validación

- Cambio mínimo compatible; no añadir componentes por intuición o reconstruir legacy.
- Si cambian scope cliente/baseline/secreto/ambiente/ruta protegida, detener y consultar.
- Docker para npm/python/tests; sin instalar/arrancar stacks ni usar DB cloud por defecto.
- SQL/writes/grants/backup/restore, recursos protegidos, retry, secrets, Auth/reset,
  schedules/workflow_dispatch/Git/deploy conservan aprobaciones separadas. Agrupar scope
  coherente y exacto con operaciones/retries/límites, nunca un permiso ilimitado.
- Diagnosticar primero el componente fallido con caso pequeño y salida sanitizada útil.
  No repetir pipeline/drill completo cuando snapshot/runtime no arranca.
- Runners/fixtures son código con riesgos, no exentos de revisión. Puede pasar revisión
  estática y fallar runtime; declarar cada grado separado.
- No leer `.env*`, documento cliente privado ni raw tokens al inventariar contratos.
  Nombres de variables/identidades permitidas, nunca sus valores secretos.

## Después del cambio

1. Revisar aristas nuevas/eliminadas y actualizar el JSON del [registro fuente-componente](registro_fuentes_componentes.json), su vista generada, ficha/anchor y documentos de dominio afectados. Crear, mover, eliminar o cambiar un contrato deja el gate documental pendiente hasta que paths, anchors, consumidores, datos, tests/evidencia y permisos vuelvan a concordar.
   Donde el registro declare `inline_comment: required` o `optional`, el source lleva solo `StudIAMatch-Docs: ruta#anchor`; no se copian allí definiciones ni listas de consumidores. `none` cubre migrations históricas, evidencia sellada, generado y dependencias: su relación se mantiene en el registro externo. Al mover o retirar la sección destino, actualiza o retira el marcador junto con su asignación.
2. Ejecutar gates autorizados; registrar grado/candidato/inputs/resultados/límites.
3. Clasificar PASS anterior: vigente, histórico o revalidación requerida por cambio;
   preservar logs/manifiestos consumidos. No invalidar todo por un cambio de prosa.
4. Reviewer independiente según AGENTS; convertir findings en tareas, corregir/revalidar.
   Waivers con causa/evidencia/owner/riesgo/vencimiento/aprobación humana.
5. Estado vivo resume resultado/gate siguiente; índice enlaza entrada actual; historia va
   bajo heading fechado, no sustituye implementación actual. Evitar duplicar prompts.
6. Revisar seis pilares: funcionalidad, escalabilidad, seguridad, mantenimiento, calidad,
   rendimiento. Declarar no aplicables con causa; no inventar mediciones.
7. Si ready PR: validar diff/scope guard, completar plantilla real, lista inclusión y
   manifest. Documentación global aquí solicitada viaja con H3 bajo permiso de PR futuro.
8. Push/PR/merge/deploy/promoción no automáticos; vincular issue/PR trabajado a sesión.
   GO local PR no es GO Development y no habilita Certification/Production.

## Nomenclatura y cambios de ruta

- La navegación Obsidian activa usa nombres de dominio y responsabilidad (`indice.md`, `frontend.md`, `componentes/admin_runtime.md`); no se crea un índice paralelo por cada corte.
- Una nota o evidencia nueva propia de H3REQ1 usa `h3req1_<proposito_corto>_YYYY-MM-DD.<extension>`. Las fichas mantenidas conservan nombres del dominio, no el prefijo del hito. Las evidencias con nombre sellado o consumido conservan su ruta.
- El código mantenido conserva las convenciones del runtime y los paths especiales de frameworks. Los módulos JavaScript usan `.mjs` cuando son módulos independientes; los tests/runners nombran el contrato o proceso y usan su extensión ejecutable vigente. Las migrations históricas no se renombran.
- Una fuente mantenida enlaza su ficha con un marcador breve `StudIAMatch-Docs: ruta#anchor` cuando su política de grupo lo permite. El registro JSON canónico guarda las relaciones; el comentario no duplica la definición.
- No se renombra por estética. Antes de proponer un rename se registra ruta origen/destino y se buscan consumidores en Markdown/anchors, marcadores, registro, imports, tests, runners, workflows, manifiestos y referencias históricas de ambos checkouts. Se presenta el alcance encontrado y el impacto antes de aplicar; los artefactos sellados, archivos especiales, migrations y rutas de contrato permanecen intactos.
- En el corte de navegación histórica 2026-10-13 no se propone rename: `h3req1_c03_integrated_r37_preparation_2026-10-10.md` expresa requerimiento/proceso, revisión y fecha; su ruta se enlaza desde el catálogo C03, sin alterar la evidencia.

## Clasificación documental y resolución de contradicciones

| Clase | Uso |
|---|---|
| VIGENTE_IMPLEMENTACION | Mapa/contrato contrastado con fuentes del candidato; no indica adopción remota |
| VIGENTE_OPERACION | Estado y próxima acción bajo autoridad humana; NO-GO si falta gate |
| PROPUESTA | Diseño no acreditado; contrastar decisiones posteriores antes de implementar |
| HISTORICO | Resultado/plan fechado con candidato/alcance; no heredar GO, permiso ni tests |
| DESCONOCIDO | Investigación pendiente; no convertir en «no existe» ni «ya está» |

Si dos notas discrepan: consultar autoridad/evidencia/código. No declarar histórica una
falla no resuelta solo para pasar. Guardar causa de supersession y links al corte actual.
Un informe de septiembre puede conservar READY_LOCAL para sus bytes, pero no es readiness
del BFF candidato de octubre. Una migración existente no prueba que esté aplicada remoto.

### Grado de evidencia

| Grado | Acredita | No acredita |
|---|---|---|
| SOURCE | Código, imports, símbolo, contrato/config local observado | Correctitud de ejecución o adopción |
| STATIC | Sintaxis, tipos, forma, assertions leídas, hashes/manifiestos | Resultado dinámico del contrato |
| UNIT/COMPONENT | Ejecución aislada con mocks/fixtures indicados | Servicio real, datos operativos o ambiente remoto |
| LOCAL_RUNTIME / LOCAL_INTEGRATED | Ejecución del runtime/servicios locales identificados y sus casos | Adopción remota, salvo evidencia independiente por ambiente |
| REMOTE_ACCEPTANCE | Host, SHA/config/servicios y casos del ambiente observados en fecha | Promoción a otro ambiente ni vigencia después de cambiar inputs |

La relación entre una fuente y su prueba puede estar verificada aunque el resultado de
ejecución conste como `NO-EJECUTADO`; el registro debe decirlo explícitamente. No convertir
presencia de suite, manifest o commit en PASS.

## Gate documental de esta capa

El constructor debe poder responder quién consume su cambio, contratos/pruebas afectados,
datos y efectos, fallos/recuperación, evidencia invalidada/preservada y permisos. Validar
registro, paths/anchors, comentarios, enlaces/recorridos, consistencia de estado y pruebas
docs/cliente en Docker cuando aplique.
Este gate orienta desarrollo; no prueba bugs ausentes ni reemplaza cierre funcional.

El chequeo local se ejecuta dentro de `studiamatch-dev` mediante
`bash scripts/security/run_documentation_integrity.sh --self-test`. El JSON del registro
es la autoridad; la vista Markdown se genera con `--render`. El descubrimiento dinámico
debe fallar con `SOURCE_UNASSIGNED` ante cualquier fuente nueva no registrada.

Para el trabajo actual, seguir el [estado operativo](../estado_del_proyecto.md) y el [índice principal](../indice.md).
La [ruta EXEC-01–06 del 2026-10-06](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md)
se conserva como historia de un NO-GO anterior a R178/R181/R182; no es una referencia operativa vigente.
