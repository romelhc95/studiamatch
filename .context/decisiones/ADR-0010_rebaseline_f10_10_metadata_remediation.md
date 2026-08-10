# ADR-0010 - Rebaseline F10.10 Para Remediacion Acotada De Metadata

| Campo | Valor |
|---|---|
| Estado | `APPROVED_EFFECTIVE_PENDING_PROTECTED_MERGE` |
| Fecha | `2026-08-10` |
| Autoridad | Decision superior humana del Hito 1 |
| Subfase creada | `F10.10` |
| Fase preservada | `F10.9=STOP_REQUIRES_REBASELINE` |
| Criterio preservado | Cero cursos activos con syllabus/objectives incompletos |

## Contexto

F10.9 cerro G3/P5 tecnicamente, pero G4 termino en
`STOP_REQUIRES_REBASELINE`. El snapshot diagnostico historico conserva `104/224`
cursos activos incompletos; no es una cohorte vigente ni autoriza escrituras.
P5 es un gate local read-only y no corrige datos operativos.

La correccion potencial exige una fase mutante separada. Reutilizar F10.9,
workers normales, sync/upsert o scripts legacy ampliaria silenciosamente la
frontera runtime CA1 y contradiria el STOP aprobado.

## Decision

Se crea `F10.10 - Remediacion Acotada De Metadata` dentro del Hito 1. F10.10
puede planificar y, solo por gates y autorizaciones separadas, reparar campos
missing de metadata. F10.9 permanece detenida; completar F10.10 no reactiva
G5-G13 automaticamente.

La frontera aprobada es:

- conservar el umbral de metadata cero;
- derivar cohortes nuevas por target fisico; nunca usar `104/224` como allowlist;
- modificar fill-only `courses.syllabus` y `courses.objectives`;
- permitir restaurar `category`, `category_id` y `category_confirmed` solo si el
  trigger de syllabus los altera dentro de la misma fila de cohorte;
- usar fuentes oficiales ya persistidas, sin live fetch;
- usar providers solo para propuestas atribuibles a fuente y con revision humana
  del 100% de sus outputs;
- no derivar objectives automaticamente de graduate profile;
- no escribir `staging_raw`, `cleansed_programs` ni `enriched_programs`;
- no usar `enrichment_worker`, `sync_vector_worker`, upserts ni tooling legacy;
- no crear DDL, RLS, RPC, grants o migrations; una necesidad de schema termina
  `STOP_DDL_REQUIRED`;
- promover aprobaciones Free -> Certification -> Pro sin copiar filas, IDs o
  payloads; las cohortes son independientes por target fisico identificado por
  `(project_ref, host_fingerprint)`. Dos nombres que resuelvan al mismo target
  comparten una sola cohorte/apply y registran dos etapas de aprobacion, no dos
  ambientes de datos;
- ejecutar un pilot maximo de 5 y lotes posteriores maximos de 10, con un solo
  writer secuencial;
- exigir exact-one, compare-and-swap, backup privado y la secuencia
  `apply -> apply NOOP -> restore -> restore NOOP -> apply final -> apply final NOOP`;
- demostrar cero cambios no-cohorte y cero writes en tablas ETL;
- no desactivar cursos para reducir el denominador.

## Fuentes Y Calidad

La precedencia permitida es:

1. valor persistido no mock, atribuible y semanticamente correcto;
2. extraccion determinista desde fuente oficial persistida;
3. sintesis provider sustentada por evidencia persistida y revisada por humano;
4. `HOLD` cuando la fuente sea insuficiente, ambigua, stale o conflictiva.

`objectives` representa objetivos o resultados de aprendizaje respaldados por
fuente oficial. `graduate_profile` no es equivalente automatico. La politica
`metadata-remediation-v1` evalua toda la poblacion activa: completitud P5,
lineage same-target, fuente oficial por campo, mock=false y semantica correcta.
Un HOLD, conflicto, output no atribuible, mock, placeholder o residual metadata
impide declarar salida cero.

## Consecuencias

- F10.10 empieza en M0 documental y no tiene capacidad remota heredada.
- Cada gate remoto requiere autorizacion separada y target binding.
- Los writers y schedules permanecen pausados durante ventanas remotas.
- Una mutacion ambigua nunca se reintenta a ciegas; se reconcilia read-after-write.
- La correccion de categoria posterior al PATCH de syllabus es una unidad logica
  de dos PATCH, no una transaccion. Cada PATCH usa CAS/exact-one y existe un
  estado intermedio posible. Un timeout o estado mixto termina
  `HOLD_AMBIGUOUS_WRITE`; si se exige invisibilidad atomica, termina
  `STOP_DDL_REQUIRED`.
- El artifact privado conserva preimagenes y propuestas; Git recibe solo
  proyecciones sanitizadas sin UUID, URL, host, texto ni payload.
- Si M9 demuestra cero, M10 entrega evidencia a una nueva decision superior sobre
  F10.9/G4. No se salta a schedules ni observacion.

## Estado De Adopcion

Este ADR queda efectivo como decision superior, pero M0 solo se considera
integrado despues de merge protegido y checks post-merge del paquete documental.
Hasta entonces no se implementa M1 ni se realiza acceso remoto.
