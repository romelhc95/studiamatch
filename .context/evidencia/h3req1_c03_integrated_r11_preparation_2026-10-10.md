# G07 R11 — diagnóstico sanitizado de login y continuación integrada

## Estado al 2026-10-10

R10 completó snapshot y verificación de caches, Pages/workerd `healthz`, PostgreSQL 17.11,
los tres fixtures SQL y readiness PostgREST. Al llegar a `/control/login`, el control devolvió
`AssertionError`; el contrato R10 no preservaba qué predicado falló. La evidencia completa y
sanitizada se conserva en
[R10 run](h3req1_c03_integrated_run_2026-10-10_r10.log), SHA-256
`67957f6f5006f668a31ea7fc70f2bbf14c37e62f79b50c10b45cc033198d153b`, exit 1. No se atribuye
causa a BFF, Auth local, cookies, Edge, SQL ni Docker. Failure-stop detuvo los cuatro servicios
R10 de esa ejecución; los contenedores y recursos detenidos se conservaron. `studiamatch-dev`
permanece healthy.

## Corrección de diagnóstico

Se agregó `tests/h3req1_c03_login_result.mjs`, que clasifica exclusivamente cuatro predicados
ordenados: status HTTP 200, AAL2, cookie de autenticación y cookie de actividad. El runtime
mantiene esos cuatro requisitos estrictos y, ante el primero que falla, solo emite uno de cuatro
códigos cerrados. No registra cuerpos, mensajes, cookies, tokens, correo ni metadata de Auth.
El test R11 comprueba éxito, los cuatro casos negativos y que valores privados no se reflejen.
No se modificó el BFF ni su política de cookies, gateway, cuota o roles.

## R11 fijado

- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Manifiesto integrado: `tests/h3req1-c03-integrated.sha256`, 65/65; SHA-256
  `fde8f4096b4d142a728180527fc722ad74e5a0bb73df0e6a3107aa995e9e97a5`.
- Runner R11: SHA-256 `685cd674d35d96ce371745179432992dd57e6641fb681758e5feb423ff830d29`.
- Runtime: SHA-256 `8d418f149e0287f9ef2dac737f977c715ac0ee46ff6abec1f43a64be93faa9a3`.
- Clasificador: SHA-256 `54e71923dd96041cc6f05bc540e776a219238cd8b95a8647af7cfb3ab1bd1080`.
- Contrato: SHA-256 `971e457eb77ab45374d025484c8f8ef1e960ad5f363aca70bc9ef259f42d225d`.
- SQL fixture R11: SHA-256 `5d5c600b872178c1bf5367d0bf042d06294d5efd7fd9a62867bb4c04faa6d2f2`.
- El manifiesto R10 previo se preservó byte por byte en
  [manifest R10](h3req1_c03_integrated_manifest_r10.sha256), SHA-256
  `fad4478bbcb89524db4efd78081bc57253c85ec05cf7278a7ec65196daf6805b`.

El preflight estático ejecutado dentro de Node fijado pasó Bash `-n` y 14/14 pruebas del contrato
R11, con `network=none`, rootfs read-only y tests montados read-only. ShellCheck 0.11.0
`--severity=warning` terminó exit 0 en la imagen ya disponible. `git diff --check` pasó. El log
[estático R11](h3req1_c03_integrated_r11_static_validation.txt), SHA-256
`ccd29968fa6883b2a6960d5433fdc8110f0fc69704ba99cea978a4b8e7cca98b`, conserva los resultados.
El manifiesto actual verifica 65/65. El delta respecto del input R10 incluye el runtime con el
clasificador, el nuevo módulo, runner/contrato R11 y fixture SQL R11; R10 y sus recursos no se
reutilizan ni modifican.

La revisión independiente estática R11 concluyó PASS sin findings concretos. Cubrió integridad del
manifiesto y pines, los cuatro requisitos de login, clasificación cerrada sin mensajes/valores,
ownership de containers/redes, aislamiento de PG17 y preservación de R10. No ejecutó runtime ni
Docker.

## Ejecución R11

Pendiente al preparar esta nota. Comando exacto autorizado por el ciclo local:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=15s 1800s \
  /bin/bash tests/h3req1_c03_integrated_drill_r11.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R11 \
  --manifest-sha256 fde8f4096b4d142a728180527fc722ad74e5a0bb73df0e6a3107aa995e9e97a5
```

El runner utiliza nombres R11 nuevos, imágenes locales fijadas sin pulls, redes internas, PG17
desechable en tmpfs y caches de dependencia read-only. Ante error detiene solo servicios de su
nonce/manifest y conserva evidencia; la retirada exacta de recursos ocurre solo al completar C03.

## Resultado y recuperación

G07 continúa parcial, sin puntos nuevos mientras falte PASS de C03 integrado. G03 y G01 mantienen
sus evidencias previas. Si R11 falla, registrar su phase/exit y código sanitizado, corregir el
predicado demostrado y crear una versión siguiente con recursos nuevos. No reintentar R11 ni
alterar R10.
