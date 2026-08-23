# ADR-0039 - Attestations Section-Aware Fail-Closed

## Estado

Aceptada localmente como candidate CI10.

## Contexto

PR #441 publico CI9 a `desarrollo@17d383291a5f2877074b54b66f2a0ff48a643667`, pero el push post-merge fallo en run `32666126533` con `POST_MERGE_ATTESTATION_DUPLICATE`. El pre-merge habia pasado porque `validate_change_governance.py` parseaba solo `## Governance Attestation`; el post-merge fallo porque `validate_work_package.py` parseaba todo el body y detectaba como duplicados los labels compartidos con `## Promotion Attestation`.

## Decision

Las attestations se parsean por seccion H2 exacta. No existe fallback al body completo cuando falta una seccion. Cada validador usa solo la seccion aplicable a la ruta: PR normal hacia `desarrollo` usa Governance; O2-O5 HOM-010 usa Promotion. Los duplicados se detectan dentro de la seccion aplicable y los valores no inertes en la seccion equivocada bloquean la ruta.

`Promotion Attestation` vacia o con placeholders heredados se trata como inactiva para PR ordinarios a `desarrollo`, permitiendo que el body historico de PR #441 clasifique `NOT_APPLICABLE`. En promociones reales esos placeholders siguen fallando por las validaciones estructurales de grant, digest, tree, approval y expiry.

## Consecuencias

- PR #441 no se edita ni se reintenta; queda como evidencia historica de fallo post-merge.
- HOM-009 queda superseded por HOM-010 antes de cualquier O2.
- El template elimina placeholders no vacios en secciones inactivas.
- CI10 debe pasar regresiones con el body de PR #441, O2-O5, direct push, upper branches y secciones malformadas.
- Crear rulesets remotos, promover a `certificacion`/`main`, DB Sync, Cloudflare Production y cualquier R3 siguen requiriendo grants JIT separados.
