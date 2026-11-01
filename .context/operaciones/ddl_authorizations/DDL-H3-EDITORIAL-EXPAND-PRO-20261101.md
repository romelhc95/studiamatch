# DDL-H3-EDITORIAL-EXPAND-PRO-20261101

Status: DRAFT_NOT_AUTHORIZED

## Alcance propuesto

- Ambiente propuesto: Supabase Pro `xwhtiqmboljkshrtviyw`.
- Manifest propuesto: `h3-editorial-expand`, únicamente mediante el workflow
  existente `DB Sync to Production` desde `main`.
- Migraciones: el conjunto H3 Pro cerrado de
  `scripts/maintenance/pro_h3_migration_manifest.py`, con orden y hashes que
  el preflight del workflow vuelve a verificar. Este borrador no selecciona ni
  aplica archivos SQL.
- No incluye backfill manual, datos operativos, cuentas, Auth, Edge Functions,
  writers, schedules, Pages/Access, configuración, secretos ni deploy.

## Condiciones que siguen pendientes

Este archivo sigue en `DRAFT_NOT_AUTHORIZED`; los datos de autorización que
dependen de una persona o de comprobaciones futuras no se rellenan ni se
presentan como satisfechos.

1. El guard quedó integrado mediante PR #521 en Certification, candidato
   `605a6ecca29e20ade8cac3874d380758d18e6a11`.
2. En ese SHA se completó el run #91 (`41338753002`) `operation=verify` para
   `h2-expand-compat`: SUCCESS; dry-run con cero pendientes; Apply NO-OP;
   `Apply migrations to Pro` SKIPPED; `Verify target schema` SUCCESS. La
   evidencia auténtica conserva su etiqueta histórica `operation=apply`, sin
   convertirla en afirmación de que se aplicó SQL. Run 89 queda como registro
   histórico, no como cobertura de este candidato.
3. La evidencia autenticada del run 91 se copia en el JSON canónico junto con
   las relaciones, documentación y verificaciones de este paquete antes de
   congelar el futuro payload H3 `P`. H2 candidate/payload `C` no es `P`.
4. Después de las integraciones protegidas y de validar el árbol real, derivar
   `auth_base`, `P`, el digest no-auth, el manifest, la cohorte y gates
   Backup/PITR/Production. Para H2, `C` debe ser ancestro del candidato final
   `M` y `diff(C,M)` debe pasar `disallowed_after_candidate`. Para H3,
   `auth_base` debe ser ancestro de `P`, `P` de `M`, y `diff(P,M)` solo puede
   cambiar este archivo de autorización. No se impone `C` ancestro de `P` sin
   una condición del workflow que lo exija. Deben preservarse merge commits,
   sin squash ni rebase.
5. Solo tras esos gates se presenta la decisión humana de autorización. Si se
   aprueba, se completan en este mismo archivo los campos exactos que exige
   el workflow y `Status` cambia de `DRAFT_NOT_AUTHORIZED` a
   `APPROVED_FOR_PRODUCTION_DDL`. Este archivo será el único path modificado
   después de `P`; el cambio no se limita a la línea `Status`. No se rellenan
   aquí valores futuros ni se anticipa esa autorización. El gate mantiene sus
   verificaciones y rechazará cualquier otro path en `diff(P,M)`.

## Comprobaciones requeridas por el workflow

La solicitud final deberá cumplir, con valores derivados del candidato real,
el manifest y SHA de payload autorizados, base ancestral, digest del contenido
no-auth, conteo y digest H2, verificación de Backup/PITR y aprobación del
environment Production. El workflow existente conserva sus controles de
ancestría, hashes del manifest, controles productivos y verificación posterior.
El nombre de esta ruta debe coincidir con el ID exacto que seleccione el
workflow; admitir el path en el scope guard no reemplaza ninguna comprobación
de contenido ni concede permisos.

## Recuperación propuesta

Si una aplicación autorizada falla parcialmente, detener la secuencia y cotejar
el ledger y schema antes de decidir el siguiente paso. No borrar auditoría,
snapshots ni marcar migraciones a mano. Mantener el código compatible y el
schema expandido; recuperar aplicación mediante rollback protegido del código.
Cualquier corrección SQL forward-only o repetición de apply requiere un JIT
propio y una nueva lectura del estado real.
