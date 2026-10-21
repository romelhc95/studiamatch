# H3REQ1 — el preflight V2 detuvo la invocación por pin discordante

Fecha: 2026-10-09. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. En el instante de
la invocación, el candidato registraba 232 entradas WIP y el checkout original 78; ambos se
preservan.

## JIT consumido y resultado

El usuario aprobó `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-FIX-AND-R9-ONCE-20261009-V1`,
SHA-256 `1cb4ad0dbf3f3928c88a62441c2806c8eff2358ff3970c1f07d5a787d8fd29b5`. Se ejecutó una vez
como `romel` en Ubuntu WSL con TTY, sin `sudo`. Resultado sanitizado:

```text
phase=classifier-v2-r9-preflight|error_code=DIAGNOSTIC_RUNNER_HASH_MISMATCH
```

Exit del wrapper: **1**. La comprobación externa del SHA del runner combinado pasó; el runner
combinado confirmó checkout/rama/HEAD y falló verificando el pin del runner diagnóstico. No
alcanzó el endpoint Docker, las pruebas sintéticas, la lectura de imagen/contendor F1 ni r9. No
se hizo ninguna llamada Docker API y no se repitió la invocación.

## Predicado, causa y corrección

El predicado fallido fue la igualdad SHA-256 previa a ejecutar el runner interior. El combinado
esperaba `1fe0f175e6164e31e1562bac7c85604cc8e0711c7a2f47a6fdd476aa7f870a9b`; el archivo
`run_wsl_f1_read_classification_v2_once.sh`, que el JIT declaraba pinneado, tiene SHA
`97b5e9e0e3493594bad68022be40035880d01d12d6947104f0eadf22445d5452`. El helper, fixture
sintético, proyector, helper de endpoint, runner r9 y manifiestos comprobados conservaban los
SHA declarados.

Se corrigió únicamente `DIAGNOSTIC_RUNNER_SHA256` en el runner combinado para que coincida con
el artefacto incluido en el paquete. La corrección está revisada por comparación estática; no
se ejecutó todavía. No se cambió lógica de diagnóstico, prueba, Docker, imagen, contenedor F1,
ni el contenedor `studiamatch-dev`.

El usuario había reportado que `studiamatch-dev` (`115d4041…`) indica divergencia entre los
manifiestos `web/package.json`/`web/package-lock.json` y la imagen staged. La lectura estática
de `init-container.sh` confirma que ese mensaje se emite cuando los hashes de ambos manifests
en el bind mount difieren del marcador staged de la imagen, y recomienda `docker compose build`.
No se leyó el marcador ni se consultó Docker; no se inició/reconstruyó el contenedor y no se
infiere que cause este error de pin.

## Siguiente invocación preparada

El JIT anterior está consumido y no se repite. Se preparó una nueva invocación agrupada que
prueba primero los casos V2, lee F1 una vez solo tras synthetic `OK` y ejecuta r9 solo si pasan
las cuatro fases y la allowlist. La discrepancia del pin está corregida en el runner; aún no hay
prueba runtime de esa corrección.

[JIT con pin corregido + F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v2_pin_corrected_and_r9_once_2026-10-09.md).
No hay retry ni permiso heredado del JIT consumido. La invocación nueva no reconstruye ni toca
`studiamatch-dev`.

## CI, aceptación y gates

El patch Protected Workflow Integrity V3 sigue aislado y sin aplicar: SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`. Su salida previa `git
apply --check` y revisión estática se preservan; no se ejecutaron pytest, actionlint, Docker ni
checks remotos. GitHub sigue exigiendo solo `security-audit`, Pages mantiene Production `main`
y watch include `*`; no hubo publicación ni cambio remoto.

G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta cero. D01–D14=0/14. Los parciales
previos de SQL C03 (41/41 inputs), r4 (20/20), scanner r7, UAT BFF r2 (60 checks/10 casos de
cuota), UAT histórico (144/144) y onboarding histórico (10/10) permanecen separados y no
cierran gates del candidato actual. No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
