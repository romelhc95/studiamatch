# Resultado V11 — smoke combinado del template FAIL

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Autorización e invocación

- JIT `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V10-GATED-READ-AND-R9-ONCE-20261009-V1`, SHA-256
  `7775d8df1a71fe00f27e78e6a4e73599eab0a62bc064b438932adfb2dcd660b7`.
- El usuario aprobó una invocación. Se ejecutó una vez como `romel` no-root en Ubuntu WSL,
  con `require_escalated`, sin `sudo`. Runner fijado:
  `run_wsl_f1_v11_then_r9_once.sh`, SHA-256
  `fbd5f3da45c0a5b1f50c6f7f158745f2b0c886c4eac1fb1e579e54e8ac63f4dd`.
- Exit del runner: **1**. Se conservaron únicamente registros phase/error y el exit code; no
  se guardó stderr, metadata, ID, secretos ni texto crudo.

## Resultado sanitizado

```text
phase=prior-v10-evidence|error_code=OK
phase=prior-endpoint-attestation|error_code=OK
phase=f1-template-synthetic-inspect|error_code=INSPECT_TEMPLATE_EVALUATION_ERROR
exit=1
```

El smoke combinado falló antes de emitir `f1-template-synthetic-check`. Por orden fail-closed,
no leyó la imagen F1 ni el contenedor F1 y no ejecutó r9. La autorización V11 queda consumida.

## Diagnóstico acotado

El error conserva la fase y la clase, pero no identifica cuál de las dos variantes del smoke
(labels/tmpfs presentes o ausentes) produjo el fallo. V10 aprobó las 25 expresiones por separado
en su fixture sintético; eso no prueba el mismo formato combinado ni los mapas ausentes. No se
deduce que Docker, la imagen o F1 estén defectuosos. La siguiente corrección debe instrumentar
solo las dos variantes con códigos cerrados, sin repetir V11 ni inspeccionar datos reales; luego
se requiere una autorización nueva antes de cualquier invocación Docker.

No hubo pull/build/install/retry, modificación Docker, acceso a `studiamatch-dev`, lectura F1,
r9, base de datos ni operaciones remotas. G01/G02 permanecen 10/10; G03–G10 permanecen 0/10;
el total sigue en **20%**.
