# Revisión estática del diagnóstico F2b — H3REQ1

Fecha: 2026-10-08. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Estado

El JIT F2b recibió aprobación para una ejecución y ambos residuales MEDIUM fueron aceptados.
La ejecución única terminó **NO-GO, exit 1, fase `context-config`**. Se consultaron el
contexto y endpoint local con el cliente Docker; la ruta del socket no pasó el gate de
canonicalidad (`realpath` no coincidió con la ruta seleccionada). La ruta concreta se
descartó y no se registró. No se llamó al helper de `/proc`, no hubo petición al daemon,
no se leyó la imagen ni el contenedor F1 y no se hicieron mutaciones, cleanup ni retry.
F1 queda intacto y su control discrepante sigue desconocido. Esta nota no convierte F1,
F2, F2a ni el snapshot en PASS.

## Evidencia preservada y revalidación por hashes

- C02 v4: se revalidaron por hash los 72 inputs no-C03 esperados. Coinciden; las suites SQL,
  PostgREST, cuotas, gateway, replay y concurrencia no se reejecutaron. La comparación amplia
  de 74 filas incluye dos inputs propios de C03 y por eso no corresponde a C02 no-C03.
- C03 SQL v3: coinciden los 41 inputs fijados. No se ejecutó SQL.
- Se mantienen separados los fallos previos: R4 healthz antes de DB/PostgREST/SQL; S1 antes
  de npm/workerd; D3 por logging inválido; D4/J3 por falso negativo de `.Mounts` frente a
  `HostConfig.Tmpfs`. Ninguno se usa como causa de F1.
- F1 conserva su reporte original y NO-GO: `docker create` terminó 0 para el ID/nonce
  fijados, el runner abortó antes de `start`, y el nombre del control discrepante no quedó
  registrado. F2b no llegó a la inspección exacta; la causa de F1 permanece desconocida.

## Corrección local preparada

- `tests/h3req1_c03_docker_inspect_projection.sh` compara 27 campos individualmente; valida
  tmpfs desde `HostConfig.Tmpfs`, acepta listas persistentes nulas/vacías y compara `.Image`
  contra el ID inmutable local de la imagen digest.
- `tests/test_h3req1_c03_docker_inspect_projection.sh` cubre la forma observada en D4/J3
  (`HostConfig.Tmpfs` configurado, `.Mounts=[]`), tmpfs ausente, mount inesperado, ID de
  imagen distinto y campo duplicado. La prueba no se ejecutó todavía.
- `tests/h3req1_c03_docker_daemon_identity.py` exige que el socket Unix corresponda a un
  único listener local `dockerd`, ejecutable protegido y PID namespace local. Si la lectura
  de `/proc` no es completa o aparece proxy/desconocido, F2b termina antes de cualquier API
  Docker. La prueba no se ejecutó todavía.
- F2b hace una sola lectura del ID de imagen local y una sola inspección al ID F1. No incluye
  cambios de estado, cleanup, retry, logs, exec, pulls ni acceso remoto.

## Corrección y siguiente gate

- F2b se conserva sin cambios: su hash sigue identificando el runner ya consumido.
- El resultado demuestra un defecto de compatibilidad en el gate de ruta: una ruta Unix
  seleccionada puede resolverse a una forma canónica diferente. No demuestra que el endpoint
  fuera symlink, proxy o un daemon distinto; esa metadata no se registró.
- Siguiente paso local preparado: runner F2c que resuelva la ruta a su destino canónico,
  confirme que el destino es socket local y ejecute el mismo peer proof antes de cualquier
  API. Requiere JIT nuevo; no se reintentará F2b.

## Pins F2b

| Artefacto | SHA-256 |
|---|---|
| JIT F2b | `81ec2589705535d4ded58916c69978f86b5937dd496071e17ce2b75e0e7e5703` |
| Runner F2b | `69ce78f0e597f069f5ffcc5138af18dc0718ad1aa7824628519a3ed343210379` |
| Sidecar F2b | `10e5a797a1a06c86b364eb8f4d8c53034d2477142fc517e3812106aaa997a939` |
| Manifiesto de inputs | `4d2a20555d8d5a861f8fdc19512553bcd391832cf1340b4bf85ee1cfb15a4cdd` |

`sha256sum --check` pasó antes de la ejecución para el sidecar F2b y los 10 inputs del
manifiesto. El comando aprobado terminó exit 1 en `context-config`; el reporte sanitizado
quedó en `.context/evidencia/h3req1_c03_f1_daemon_diagnostic_f2b_2026-10-08.md`. El JIT
queda consumido. `git diff --check` no informó whitespace errors en los cambios rastreados;
no analiza archivos untracked. La prueba parser, scanner, shellcheck, actionlint, Docker,
SQL y stack no se han ejecutado.
