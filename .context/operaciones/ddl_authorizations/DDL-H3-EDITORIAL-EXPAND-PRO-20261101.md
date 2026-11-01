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

Este archivo todavía no contiene autorización ejecutable ni valores para
ningún gate. Antes de que una persona pueda decidir una autorización posterior,
se debe completar la secuencia vigente:

1. Integrar este guard a Development y Certification mediante PRs protegidos.
2. Obtener el SHA real de Certification que contenga el guard; ejecutar en ese
   SHA un reporte H2 y una verificación H2 separados, cada uno con sus JITs y
   gates de ambiente. Run 89 precede al cambio del guard y no acredita este
   candidato.
3. Integrar la evidencia auténtica de H2, JSON canónico, pins y todos los
   documentos relacionados antes de fijar el payload `P`.
4. Derivar de los artefactos y commits reales el SHA del payload, base, digest
   no-auth, conteo/digest de cohorte y ancestría; confirmar de nuevo el schema,
   pendientes y gates de Backup/PITR y Production.
5. Solo después, presentar la autorización humana exacta. Si se aprueba, el
   único cambio posterior a `P` será este archivo. El workflow debe rechazar
   cualquier archivo adicional en `diff(P,M)`.

No se afirman como satisfechos ni se rellenan mediante ejemplos los valores
que dependen de esas verificaciones futuras. El contenido presente no satisface
el check de estado del workflow ni autoriza `apply`.

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
