# Preparación npm audit classifier V3

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Ficha de impacto

- **Objetivo:** clasificar con códigos cerrados el fallo del auditor npm de la imagen candidata y
  una vez obtener un reporte sanitizado si la solicitud funciona.
- **Dominio/archivos:** tooling de test/auditoría bajo
  `tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/`; `package.json` y
  `package-lock.json` solo son inputs fijados, no se editan.
- **Condición demostrada:** la invocación anterior pasó sintéticos e inspección de imagen, llegó
  al proceso `npm audit`, y terminó con stdout vacío más stderr presente. El stderr crudo fue
  descartado; su contenido y causa siguen desconocidos.
- **Corrección mínima:** en ese caso, buscar únicamente líneas exactas `npm error code CODE` o
  `npm ERR! code CODE`. Códigos conocidos salen solo si pertenecen a la allowlist existente;
  desconocidos o formatos ambiguos devuelven `NPM_ERROR_REPORT`. No se imprime ni persiste el
  texto de stderr. Dos sintéticos nuevos cubren un código permitido y uno desconocido.
- **Comportamiento preservado:** mismo digest de imagen, comando `npm audit --json`, registry
  público fijado, retries cero, timeout existente, filtro de secretos y sanitización del reporte.
  No se instala ni corrige dependencia.
- **Egreso/privacidad:** el contenedor usa Docker bridge; el comando apunta a
  `registry.npmjs.org` y no ejecuta lifecycle scripts. La metadata del árbol de dependencias se
  transmite al servicio npm para la auditoría; no se incluye secreto, `.env*` ni credencial.
  El paquete no aplica una regla de firewall por hostname.
- **Transición/rollback:** operación de auditoría read-only en contenedor `--rm`; no altera imagen,
  manifests, lockfile o checkout remoto.
- **Permiso:** el JIT V2 fue consumido con `EMPTY_STDOUT_STDERR_PRESENT`. V3 requiere una nueva
  aprobación para un request npm y una sola invocación. Sin retry.

## Revisión y comprobaciones locales

- Revisión estática localizada: solo el código clasifica una línea con regex exacta, verifica la
  allowlist y devuelve un valor enum; no devuelve fragmentos, entorno ni stderr.
- `bash -n` del runner V3: PASS.
- Escaneo de whitespace del runner y fuentes V3: sin coincidencias.
- SHA-256 de `package.json` y `package-lock.json` coincide con los pins: PASS.
- Los seis casos del parser Bash y dieciséis sintéticos Python aún no se ejecutan. Quedan como
  gate del JIT en el contenedor fijado, antes de la llamada npm.
- No se ejecutó una nueva auditoría ni hubo egress en esta preparación.

## Gate

G03 continúa abierto; resultado total 10%, delta 0. No se acredita audit PASS o GO. El paquete de
una invocación está en
[`JIT npm V3`](../operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v3_once_2026-10-09.md);
su digest debe comprobarse justo antes de solicitar aprobación.
