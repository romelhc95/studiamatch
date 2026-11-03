# G07 — preparación de integración R19

## Candidato e inputs

- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`; HEAD baseline:
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP en esta preparación: 529 entradas resumidas por `git status --short`; no se
  staged, reseteó ni retiró ningún cambio del candidato. El checkout original permanece intacto.
- Manifiesto integrado R19: 69 inputs, SHA-256
  `6bed68f48085fa69992f4fecd32f6c6014ac8fe6c12809d4ce8688535a987d1a`.
- Runner R19 SHA-256
  `f439671c221fdd7440243ec09a56c63d75c37259a0d6b04516cae56d3f25d349`;
  contrato SHA-256
  `0244e86232402a9cd3015c68af83939c351d45a1b092b878b2ffebd6ad6c4e07`;
  runtime SHA-256
  `11dd1bb70bad3e8f19eee01f5683482e8d0da912042ddb1f0c4810c1274896c6`.

## Análisis y corrección mínima

R18 aisló `TLS_UNKNOWN_ISSUER` dentro del Edge Runtime antes de que el mock Auth o el
gateway recibieran una solicitud. El CA sintético no declaraba restricciones de CA; el
certificado leaf sí tenía hostname correcto y OpenSSL lo verificaba. La corrección queda
limitada a `createSyntheticTls()` del harness: CA v3 `CA:TRUE`, `keyCertSign`/`cRLSign`
y `subjectKeyIdentifier`; antes de arrancar servicios se verifican extensiones del CA y
leaf, EKU, SAN y `openssl verify`. No cambia Edge de producto, Auth, gateway, TLS de un
servicio real ni controles de confianza.

El runtime R18 quedó archivado sin cambios en
`.context/evidencia/h3req1_c03_integrated_runtime_r18.mjs`, SHA-256
`2027f2a04c9c1906b8e14cbc1c618922498e1bcdb346337ab2fb069aa01cf381`.
El diff R18 → runtime candidato contiene solo la generación y comprobación del CA/leaf.
El runner R19, normalizado de `R19/r19` a `R18/r18`, es byte por byte igual al runner
R18. La prueba de contrato R19 añade cobertura de esas propiedades; ya pasó 21/21 en
contenedor Node fijado, `network=none`, rootfs read-only, mounts de tests read-only y
tmpfs aislado. `node --check`, `bash -n`, `git diff --check` y verificación 69/69 del
manifiesto pasaron.

## Recursos y recuperación

R18 dejó evidencia durable en `h3req1_c03_integrated_run_2026-10-10_r18.log`, el resultado
R18, los scripts V1/V2 de clasificación, el runtime archivado y su manifiesto. El snapshot,
CA sintética y cuatro cachés R4 continúan en volúmenes con mounts read-only para sus usos;
ningún volumen se elimina. El runtime R18, Edge y PG17/PostgREST solo contenían el fixture
sintético de la corrida; la evidencia ya está fuera de ellos. Se retiraron siete contenedores
R18 por sus IDs exactos, sin `-v`, y las redes edge/data por ID después de verificar `internal=true`
y cero adjuntos. Se conservaron todas las imágenes y volúmenes del snapshot, CA y cachés.

La invocación local autorizada para este ciclo permite ejecutar el runner R19 una vez con
el manifiesto anterior. El runner fija branch/HEAD, Docker Desktop/endpoint, imágenes por
digest, cachés R4 de solo lectura, límites y nombres R19 únicos; crea snapshot completo,
workerd, PG17 desechable, PostgREST y Edge en redes internas. Los fixtures usan datos y
credenciales sintéticos y no montan `.env*`. Ante fallo se detienen servicios de esa corrida;
la evidencia permanece en el log sanitizado, y no se retiran snapshots, CA ni cachés.

## Estado previo al runtime R19

- G07 sigue parcial; este paquete no suma puntos ni acredita integración.
- Métricas: histórico G01–G10 **60%**; cierre local G01–G09 **6/9 = 66.67%**.
- Limpieza R18: siete contenedores y dos redes internas retirados por ID exacto; volúmenes e
  imágenes preservados.
- Siguiente operación: `tests/h3req1_c03_integrated_drill_r19.sh --jit
  H3-CLOSE-03-INTEGRATED-2026-10-10-R19 --manifest-sha256
  6bed68f48085fa69992f4fecd32f6c6014ac8fe6c12809d4ce8688535a987d1a`.
- Sin push/PR/merge, CI remoto, servicios remotos, deploy, datos operativos o Production.
