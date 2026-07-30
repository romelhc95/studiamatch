# BK-F9.5-07 - Exec Sql Control Plane

Estado: `DEFERRED_NO_IMPLEMENTATION`.

Esta nota detalla el item `BK-F9.5-07`. No crea tarea, subtarea, criterio, candidate, capability, fecha, compromiso ni autorizacion de implementacion.

## Riesgo Registrado

`public.exec_sql(text)` ejecuta SQL arbitrario como `SECURITY DEFINER`. En el contrato vigente solo `service_role` puede ejecutarlo; no es accesible desde navegador, `PUBLIC`, `anon`, `authenticated` ni `authenticator`.

El canal se conserva temporalmente porque `db_migrate.py`, `db-sync-to-pro.yml` y `check_db_parity.py` dependen de el para aplicar o verificar paquetes administrativos de base de datos. Es control-plane administrativo, no una ruta data-plane de la aplicacion.

Una secret key administrativa o pipeline comprometidos podrian alterar schema, ACL, RLS, funciones o datos. El impacto potencial es alto; la exposicion queda reducida por secret manager, environments, branch protection, review humano, ACL exacta, secret scan y auditoria.

## Sustitucion Recomendada

Una fase futura deberia sustituir este RPC por una conexion DB dedicada via CLI, identidad temporal acotada o executor firmado/digest-bound que acepte solo paquetes esperados.

## Criterio De Cierre Futuro

- Ningun RPC expuesto por Data API acepta SQL arbitrario.
- Los workflows de migration siguen funcionando mediante el nuevo canal administrativo.
- La sustitucion conserva auditoria, rollback, hashes y separacion Free/Pro.

Este residual no bloquea `GO_FOR_LOCAL_PR` ni autoriza su implementacion.

## Comunicacion Al Cliente

La plataforma conserva temporalmente un canal administrativo restringido para aplicar actualizaciones de base de datos. No esta disponible para usuarios ni para el sitio publico. Si la credencial administrativa protegida fuera comprometida, el impacto podria ser elevado; por ello su sustitucion por un mecanismo mas limitado queda registrada como hardening futuro.

## Referencias

- [Backlog F9.5](backlog_f9_5_known_findings.md)
- [ADR-0005](../../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- [PLAN-F9.7-CIERRE-001](../../operaciones/cierre_definitivo_f9_7.md)
