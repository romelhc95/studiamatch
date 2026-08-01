# Anexo Cliente - Riesgos CA2 Y Control De Accesos

| Campo | Valor |
|---|---|
| ID | `ANNEX-H1-CA2-RLS-001` |
| Estado | `DRAFT` |
| Disposicion | `DEFERRED_TO_HITO_2` vigente |
| Impacto Hito 1 | Ningun cambio funcional CA2 en produccion |

## Resumen

CA2 cambia la forma de guardar, proteger y administrar datos editoriales,
campos faltantes, leads y procesos internos. Las validaciones encontraron que
aplicar solo una parte puede producir controles inconsistentes entre ambientes.

No existe evidencia de un incidente. El hallazgo significa que todavia no se
puede certificar el nuevo modelo CA2 con el nivel de confianza requerido. Por
eso se evita un despliegue parcial y se traslada CA2 completo a Hito 2.

## Riesgos En Lenguaje No Tecnico

| Riesgo | Nivel | Que significa | Posible efecto |
|---|---|---|---|
| Accesos mas amplios de lo necesario | Alto | Algunos perfiles tecnicos conservan mas permisos que los previstos por el nuevo modelo | Lectura o cambio de informacion fuera del uso esperado |
| Reglas aplicadas de forma desigual | Alto | Una accion puede estar bloqueada por una via y disponible por otra | Resultados distintos segun el canal de acceso |
| Mecanismos internos con alto privilegio | Alto | Herramientas administrativas pueden realizar operaciones amplias | Un error operativo puede afectar mas informacion de la prevista |
| Flujo historico de leads/email | Alto | Persisten componentes que deben revisarse como una sola unidad | Procesamiento, notificacion o tratamiento inconsistente |
| Diferencias entre ambientes | Medio-Alto | Local, certificacion y produccion pueden no tener exactamente la misma configuracion | Algo validado localmente puede comportarse distinto al desplegarse |
| Aplicacion remota incompleta | Alto | El mecanismo final de despliegue/recuperacion aun requiere cierre | Cambio parcial, rollback complejo o indisponibilidad temporal |
| Pruebas por perfil pendientes | Alto | Falta demostrar que cada tipo de usuario solo pueda realizar lo autorizado | No se puede certificar todavia el principio de acceso minimo |

## Como Puede Afectar

- Privacidad: acceso tecnico mas amplio que el estrictamente requerido.
- Integridad: cambios no previstos o bloqueo de cambios legitimos.
- Disponibilidad: interrupcion temporal si una migracion queda parcial.
- Operacion: mayor soporte por diferencias entre ambientes.
- Reputacion: experiencia inconsistente en leads, emails o publicacion.

## Controles Adoptados

- CA2 no se promueve parcialmente con Hito 1.
- Produccion conserva su funcionalidad actual durante Hito 1.
- Secrets permanecen fuera del browser y del repositorio.
- Los cambios DB continuan versionados y con aprobacion separada.
- Hito 2 prueba permisos por perfil y rollback/replay.
- La entrega real-time de leads/email permanece fuera de Sprint 1.
- La evidencia cliente no publica detalles que faciliten explotacion.

## Trabajo Hito 2

1. Unificar schema, reglas y permisos CA2.
2. Validar perfiles publico, autenticado, pipeline y administrador.
3. Certificar la aplicacion primero en ambiente controlado.
4. Ejecutar backfill separado para no ocultar catalogo existente.
5. Probar recuperacion y promocion antes de produccion.

## Criterio De Resolucion

Cada riesgo se clasificara como `MITIGATED`, `ACCEPTED`, `DEFERRED` o
`BLOCKING` solo con evidencia. Este anexo no cambia el estado DB ni autoriza una
operacion remota.
