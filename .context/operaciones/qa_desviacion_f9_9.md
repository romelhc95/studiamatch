# QA-F9.9-DEVIATION-001 - Definicion QA De La Desviacion Certification

| Campo | Valor |
|---|---|
| ID | `QA-F9.9-DEVIATION-001` |
| Estado | `REVIEWED_PASS` |
| Evidencia objetivo | `EVID-H1-015` |
| Subfase | `F9.9` |
| Candidate runtime | `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17` |
| Decision relacionada | [ADR-0007](../decisiones/ADR-0007_desviacion_canary_certification_f9_9.md) |

Esta nota define la revision QA independiente de la desviacion `DEVIATION_ACCEPTED_FAIL_CLOSED`. El resultado sanitizado queda registrado en [QA-F9.9-DEVIATION-001-RESULT](./qa_desviacion_f9_9_resultado.md) como `PASS`, lo que permite marcar `EVID-H1-015=VERIFIED`. No declara resultado positivo de Certification y no autoriza F9.10, F10, Production, schedules, Supabase, Cloudflare, DDL/DML, backup/restore, writers ni nuevas ejecuciones Certification.

## Alcance

La revision determina si la evidencia primaria disponible sostiene que F9.9 fallo de forma cerrada ante condiciones no exitosas de Certification y que ese resultado puede conservarse como desviacion aceptada. La revision no valida success path, FG2 downstream, FG3, Production ni cierre de Hito 1.

Runs a revisar:

| Run | Rol QA |
|---|---|
| `30777088545` | Confirmar `NOT_EXECUTED`: cancelado esperando aprobacion, sin ejecucion ni secretos. |
| `30781870451` | Verificar fail-closed por inventario invalido y cleanup/idempotencia. |
| `30782109395` | Verificar fail-closed por source no configurado y cleanup/idempotencia. |
| `30782242009` | Verificar FG1 PASS, FG2 HTTP 403 no-cero, downstream/FG3 skipped y cleanup/idempotencia. |
| `30782360475` | Verificar FG1 PASS, FG2 HTTP 403 no-cero, downstream/FG3 skipped y cleanup/idempotencia. |

## Provenance Requerida

La atestacion QA debe registrar fuera de Git el bundle primario y publicar solo evidencia sanitizada:

| Campo | Umbral |
|---|---|
| Run ID y attempt | Coinciden con GitHub Actions. |
| Workflow | `F9.9 - Certification Canary`. |
| Ref y SHA | `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`. |
| Fecha UTC | Presente por run y artifact. |
| Artifact name | Presente por run con retencion vigente o copia privada autorizada. |
| Artifact digest | SHA-256 registrado en privado; version sanitizada puede truncarse. |
| Candidate tree | Registrado desde Git, sin depender de logs. |
| Revisor | Rol, ID opaco, fecha UTC y declaracion de independencia. |

Digests publicamente conocidos al definir esta nota:

| Run | Artifact sanitizado | Digest publicado por GitHub Actions |
|---|---|---|
| `30781870451` | `f9-9-certification-canary-manifests-30781870451-1` | `sha256:1c1966e65b11be43e4109586a3dc296b38dc63df40a0277ab33ffc8384f9a84e` |
| `30782109395` | `f9-9-certification-canary-manifests-30782109395-1` | `sha256:26e4694af6f9ae54c94c30af9b89b042b7925e6745c10786c7afc348978c4202` |
| `30782242009` | `f9-9-certification-canary-manifests-30782242009-1` | `sha256:69220c666671ca94481b55dbbb132dda770b7484badd73dfd358bfc1177efeba` |
| `30782360475` | `f9-9-certification-canary-manifests-30782360475-1` | `sha256:cf853dcd7ea6cb9335d5b581aaa167fcf03b73d232822190cca1ad6d374ba0ca` |

Los artifacts primarios permanecen fuera de Git. No se deben copiar URLs privadas, UUIDs operativos, project refs, hosts, secrets, payloads, rutas locales privadas ni logs completos a la documentacion.

## Aserciones Fail-Closed

Para aprobar, QA debe verificar:

1. El job no concluyo en success en los runs negativos.
2. Los guards de target y limites pasaron antes de cualquier mutacion.
3. En los runs HTTP 403, FG1 paso y FG2 harvest fallo no-cero.
4. Cleansing, enrichment, sync y FG3 quedaron skipped cuando fallo FG2 o FG1.
5. El post-manifest se genero aun despues del fallo controlado.
6. Restore mutable canary state se ejecuto y concluyo success.
7. La verificacion de idempotencia concluyo success.
8. Un fallo de cleanup o idempotencia habria mantenido outcome `FAIL`.
9. El bundle sanitizado no contiene secretos ni identificadores prohibidos.
10. Las cohortes F9.9 quedan sin markers residuales segun evidencia primaria.
11. Los datos no-cohorte solo pueden afirmarse con el nivel demostrado: conteos sin cambio salvo que QA registre digest de contenido privado.
12. Ningun documento o reporte reclasifica la desviacion como resultado positivo de Certification, success path, FG3 validado, Production, schedule observado ni cierre de Hito 1.

## Independencia

El revisor QA debe ser independiente del implementador, operador de canaries, aprobador de PR #277, aprobador de ADR-0007 y redactor del cambio de estado. Si no existe segregacion real, el resultado obligatorio es `BLOCKED_INDEPENDENCE_UNAVAILABLE`.

La revision debe registrar:

| Campo | Requisito |
|---|---|
| Rol | `INDEPENDENT_QA_REVIEWER` u otro rol aprobado. |
| ID opaco | Registrado sin datos personales publicos innecesarios. |
| Conflicto | Declaracion explicita de no participacion en implementacion, operacion o aprobacion. |
| Acceso | Solo lectura sobre evidencia primaria. |
| Fecha UTC | Obligatoria. |

## Outcomes

| Outcome | Efecto |
|---|---|
| `PASS` | Puede habilitar un PR documental posterior para verificar `EVID-H1-015`; no habilita F10 por si solo. |
| `FAIL` | La desviacion no queda aceptable para readiness; debe remediarse o exigirse canary Certification positivo. |
| `BLOCKED` | La evidencia, independencia o artifacts son insuficientes; `EVID-H1-015` permanece `PENDING/BLOCKED`. |

## Stop Conditions

- Artifact expirado o digest no verificable.
- SHA/ref distinto de `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`.
- Secreto, URL privada, UUID operativo, host privado, project ref o payload en evidencia sanitizada.
- Job success, falso verde, downstream ejecutado despues de fallo, cleanup fallido o idempotencia fallida.
- Afirmacion de causa raiz exclusiva del egress sin evidencia primaria suficiente; solo se permite `observado desde egress de GitHub-hosted runners`.
- Intento de usar esta QA para autorizar Production, schedules, PR a `main`, DDL/DML, backup/restore o F9.10/F10.

## Salida Esperada

La salida de QA debe ser una atestacion sanitizada enlazada desde [Paquete de evidencia Hito 1](../evidencias_cliente/sprint_1/paquete_hito_001.md) y [PLAN-H1-CA1-ONLY-001](./plan_cierre_hito1_ca1_only.md). Esa atestacion debe conservar la evidencia primaria fuera de Git y publicar solo resumen, outcomes, digests seguros, reviewer opaco y limites de claim.
