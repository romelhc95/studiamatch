# Resultado V13 — wrapper rechazó salida de diagnóstico

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Autorización consumida

- JIT `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V13-LABEL-CLASSIFIER-AND-R9-ONCE-20261009-V1`,
  SHA-256 `5019c8cd6aab75d18d3f4e369744470fee16ad91398855f6d3c18c781250aa25`.
- El usuario aprobó una invocación. Se ejecutó como `romel` no-root en Ubuntu WSL con
  `require_escalated`, sin `sudo`, después de comprobar nuevamente el hash del JIT.
- Wrapper SHA-256 `59781a6607da28918536e57698e683051967e3407ec30e09a148692675d9ddb7`; helper SHA-256
  `e2cb61472552dab4165014347f63232a3f8d1d888efa7b75aea918a02c71d073`.

## Salida sanitizada

```text
phase=f1-v11-output|error_code=OUTPUT_REJECTED
exit=1
```

El wrapper rechazó la salida del proceso diagnóstico y paró antes de r9. El wrapper V13 comparte
un límite de 2048 bytes para esa salida y rechaza cualquier línea que no sea `phase/error_code`;
el único código conservado no distingue cuál de esos predicados falló. No se persistió stdout
crudo, stderr, contenido de etiquetas, metadata, valores ni logs del contenedor.

No se puede determinar con esta evidencia si el runner llegó a las dos lecturas F1 o si falló
antes, porque la salida de fases no fue emitida. El runner contiene limpieza temporal en `finally`,
pero el resultado no permite acreditar si alguna limpieza falló. No se ejecutó r9: el wrapper solo
lo invoca después de que todo el output diagnóstico coincide exactamente con el contrato.

## Límites y siguiente corrección

La autorización V13 queda consumida; no se reintenta. No hubo pull/build/install, cambios de Docker,
lecturas de DB/SQL, operaciones remotas ni acceso intencional a `studiamatch-dev`. V14 deberá:

1. Capturar una secuencia diagnóstica acotada a 8192 bytes, mantener el filtro de líneas sanitizadas
   y emitir fases válidas anteriores a cualquier línea rechazada, sin imprimir la línea cruda.
2. Convertir toda salida inesperada con status 0 en exit no-cero y bloquear r9.
3. Antes de crear nuevos temporales, hacer una lectura read-only limitada al prefijo de nombres
   V12; si detecta alguno, reportar solo presencia y detener, sin inspeccionarlo ni limpiarlo.

G01/G02 siguen 10/10; G03–G10 siguen 0/10; total 20%, delta 0; D01–D14 0/14. F1/r9 no se
acreditan. El resultado no prueba error del daemon ni defecto del candidato.
