# H3REQ1 — validación BFF y acceso al Docker local

Fecha: 2026-10-08. Candidato `feat/h3req1-sync-20261002`, baseline HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Ficha de trazabilidad

- Componente: `web/functions/_lib/admin-bff.ts` y sus helpers de cuota/transporte.
- Consumidores: rutas Pages `/api/admin/*`; el workflow de seguridad incluye la UAT
  sintética `tests/h3_admin_bff_mock_uat.mjs`.
- Contrato a validar: si la clave HMAC de cuota coincide con la del gateway RPC, el BFF
  responde `503 server_configuration_error` antes de admitir cuota o llamar RPC. Logout
  local conserva su limpieza de cookies.
- Impacto de este ciclo: solo paquetes de validación y evidencia documental. No se editó
  código, SQL, configuración de servicios ni despliegue.
- Evidencia preservada: resultados históricos r3 y F2b/F2c/F1; paquete r4 sigue separado.
- Transición: sin cambio funcional, por lo que no hubo `expand -> compatibilidad -> deploy
  -> contract`. Rollback documental: retirar solo esta nota; preservar los paquetes y el
  resultado fallido.

## Paquete BFF r1 — intento consumido, sin prueba

Paquete: `/tmp/h3req1-bff-validation-20261008-r1`; SHA-256 de `inputs.sha256`:
`41d3372b7e17c2f5c09f4edbe254e3334fb4e24ec8652859bc598416d9e13290`. Sus ocho entradas
verificaron antes del intento. Se recibió autorización para una ejecución única.

El runner terminó con exit 1 y el mensaje `permission denied` al acceder al endpoint
Docker local `unix:///var/run/docker.sock`. No produjo salida de versión de Node/TypeScript
ni resultado de la UAT; no hay contenedor de prueba acreditado. El permiso r1 se considera
consumido por el intento y no se reutilizará.

## Paquete BFF r2 — UAT aprobada y consumida

Paquete: `/tmp/h3req1-bff-validation-20261008-r2`; SHA-256 de `inputs.sha256`:
`c2c62c156d4fec0dcdecaee6db4af9077b680ca9bc1aee74a4abde61d8f49f58`. Sus ocho entradas
verifican. Sustituye expresamente r1: comprueba la definición local del contexto `default`
y requiere acceso elevado del sandbox anfitrión para poder crear el único contenedor. El
contenedor no monta el socket Docker.

El alcance aprobado fue una sola ejecución de 180 s, sin reintentos, con imagen local
fijada `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, `--pull=never`,
red y raíz desactivadas, paquete solo lectura, UID 1001, capacidades descartadas, límites
de recursos y eliminación automática del contenedor temporal. No incluyó `.env*`, DB/SQL,
servicios remotos, F2d/F1 ni limpieza de recursos existentes; no instaló ni descargó
dependencias. El runner comprobó que Node y TypeScript fijado estuvieran disponibles antes
de la prueba.

Resultado de la única ejecución: contexto `default` identificado como Unix local; Node
`v20.20.2`; TypeScript `5.9.3`; `node --check` sin error; UAT
`{"result":"PASS","checks":60,"quotaCases":10}`; exit 0. El permiso r2 queda consumido,
sin reintentos. La UAT cubre la respuesta 503 genérica y confirma cero admisiones de cuota
y cero RPC ante claves HMAC iguales, además del resto de contratos sintéticos incluidos.
El contenedor fue efímero (`--rm`). Este resultado valida los archivos fijados de r2; si
cambia cualquiera de ellos, se requiere revalidación. No acredita bindings desplegados,
integración C03 ni el gate G08 completo.

Comando anfitrión ejecutado: `bash /tmp/h3req1-bff-validation-20261008-r2/bin/run-bff-uats.sh`.
El runner completo y sus límites están preservados en ese paquete bajo el manifiesto
indicado; el acceso elevado del sandbox se usó solo para el contexto local y la ejecución.

## Otros bloqueos y tablero

- r4: paquete helper independiente, 13/13 hashes verificados; aprobación de una ejecución
  sigue pendiente. No se ejecutó.
- F2d: el manifiesto vigente verifica 16/17; el único delta es el helper Python. SHA fijado
  anterior `f117a1c4d6f769d161c1401daa78de166746729ad84a2e1431ca26967aa5612d`; SHA actual
  `c0b3820d920015325b2d91ed8e50215f3a1ba967d79a1d3abda62c702b460ac0`. No se ejecutó F2d
  ni se consultó el recurso F1.
- No se cerró ningún gate: G01–G02 siguen acreditados (20%); G03–G10 siguen abiertos. G08
  ya tiene UAT BFF HMAC PASS en r2, pero faltan los checks finales y la revisión del
  candidato completo. La matriz remota Development permanece en 0/14; no se habilita
  `GO_LOCAL_PR`.
