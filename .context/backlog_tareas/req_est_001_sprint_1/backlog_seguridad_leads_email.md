# BK-F9.5-05 - Seguridad Leads Y Email

Estado: `DEFERRED_NO_IMPLEMENTATION`.

Esta nota detalla el item existente `BK-F9.5-05`. No crea tarea, subtarea, criterio, owner, fecha, compromiso ni autorizacion de implementacion.

## Alcance Futuro Requerido

Un requerimiento futuro de reactivacion debe cubrir:

1. Threat model.
2. Consentimiento y textos de privacidad.
3. Retencion, eliminacion y solicitudes del titular.
4. Ingreso server-side de leads.
5. Validacion y normalizacion server-side.
6. Idempotencia y deduplicacion.
7. Rate limiting y antiabuso.
8. CAPTCHA o mecanismo equivalente.
9. RLS, ACL y service identities.
10. Outbox o cola de entrega.
11. Eleccion del proveedor de email.
12. Verificacion de dominio y remitente.
13. Gestion y rotacion de secretos.
14. Reintentos, dead-letter y observabilidad.
15. Kill switch.
16. Auditoria e incident response.
17. Supply-chain y dependencias.
18. Pruebas por rol.
19. Gates Free y Pro separados.
20. Proceso formal de reactivacion.

## Regla De Reactivacion

La reactivacion exige nuevo ciclo `INTAKE -> EST -> REQ -> TASK`, aprobacion humana, migration forward-only y gates Free/Pro separados. No puede hacerse por variable de entorno, grant manual, deploy aislado de Edge Function ni edicion de ledger.

## Referencias

- [Backlog F9.5](backlog_f9_5_known_findings.md)
- [ADR-0005](../../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- [Plan del corte](../../operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md)
