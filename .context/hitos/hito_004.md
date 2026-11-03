# HITO-004 - Home Publica

| Campo | Valor |
|---|---|
| Estado | `PLANNED_AFTER_H2_CONTRACT_STABLE` |
| Work package | `SUPERSEDED` |
| Criterios | `H4-CA5`, `H4-CA6`, `H4-CA7`, `H4-CA13H` |
| Gate | Contrato H2 estable |

## Alcance

Home publica fiel a `SRC-UI-HOME-001`: instituciones, destacados, inscripciones abiertas, exploracion por pais, Inter, paleta/gradiente, jerarquia visual, conteos reales cuando exista fuente backend, CTA visual sin captura y ROI ausente.

## Contrato Visual Exacto

- 6 programas patrocinados.
- 3 programas abiertos organicos.
- 3 paises.
- Tipografia Inter.
- Paleta y gradiente del HTML aprobado.
- Logos reales con fallback estable.
- Conteos reales desde backend cuando existan; placeholders no cierran criterio.
- CTA visible sin `POST /leads`, almacenamiento, email, webhook ni egress.
- ROI oculto.
- Responsive desktop/mobile.

## Documentacion CA7

Debe actualizar documentacion tecnica de datos, pipeline, operacion, gates y evidencia vinculada. CA7 no autoriza cambios de pipeline ni schedules.

## Handoff Vigente — 2026-10-29

**Estado: `PREPARATION_ONLY_PENDING_H2_CONTRACT_AND_SEQUENCE`.** H4 se mantiene
en preparación hasta acreditar el contrato H2 en Pro y definir su orden respecto
del cierre H3. Las lecturas SELECT-only actuales no acreditan la cohorte ni
resuelven la discrepancia entre ledger y objetos H2. No ejecutar cambios H4,
pipeline, writers ni schedules en este corte.

Siguiente gate: obtener la evidencia agregada de H2, resolver/validar la
compatibilidad y documentar la secuencia H2 → H3 → H4 antes de solicitar una
promoción. Esta nota no autoriza DDL, workflows, despliegues ni activación.

### Diagnóstico anterior del paquete productivo — superado por el preflight local actualizado, 2026-10-29

El preflight Pro confirmó H2 parcial fuera del ledger y la cohorte agregada
quedó pendiente. En ese corte el reporte local aún se detenía ante el drift;
esa limitación fue corregida después y ahora produce agregados `REVIEW_REQUIRED`
sin habilitar apply. La lectura de cohorte real continúa pendiente de un
workflow `report` con JIT. H3 sigue aceptado hasta Certification, el paquete
productivo local no está publicado y el gate documental integral conserva
FAIL. H4 permanece en preparación. No cambiar UI/datos de H4 ni activar
pipeline, writers o schedules hasta acreditar H2, estabilizar H3 Pro y decidir
la secuencia H2 → H3 → H4 en un ciclo protegido separado.

## Navegación

### Handoff H2 actualizado — 2026-10-29

El lector H2 local ya distingue estados incompletos y produce agregados sin
modificar el gate de aplicación. La lectura remota de cohorte sigue pendiente
de un workflow `report` autorizado, porque usa el service key Production y
evade RLS; no se ejecutó en este paquete. H4 permanece en preparación hasta
revisar esa evidencia, verificar el contrato H2 y acordar la secuencia
H2 → H3 → H4. No cambiar H4 ni activar writers, pipeline o schedules.

[Matriz del hito](../matrices/matriz_hito_004.md) · [Frontend público](../frontend.md#rutas) · [Estado operativo](../estado_del_proyecto.md)
