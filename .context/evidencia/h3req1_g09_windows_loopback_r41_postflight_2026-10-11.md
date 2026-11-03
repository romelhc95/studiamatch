# H3REQ1 — postflight loopback Windows R41 — 2026-10-11

GET-only smoke from Ubuntu WSL against the already running Docker Desktop
services. No app, database, build output, or container was recreated.

| URL | HTTP | Meaning |
|---|---:|---|
| `http://localhost:3335/` | 200 | R41 app shell through the new loopback sidecar. |
| `http://localhost:3335/admin/login/` | 200 | R41 login page; same app container and PG17 R12 synthetic database used by H3-UAT-040. |
| `http://localhost:3335/admin/users/` | 200 | R41 Admin route shell. No session or membership contents were read by this smoke. |
| `http://localhost:3335/courses/ulima/analitica-aplicada-60000000/` | 404 | This course is in PG17 R12 but not in the static route set mounted by R41. The snapshot contains the separate legacy build fixture. |
| `http://127.0.0.1:3335/admin/login/` | 421 | Expected rejection: the sidecar accepts the configured `localhost:3335` Host only. |
| `http://127.0.0.1:3333/courses/ulima/analitica-aplicada-60000000/` | 200 | Existing R12 public runtime still serves the pipeline course from the shared synthetic PG17 R12 dataset; this is a different mounted static bundle from R41. |

Active resources observed:

- `h3req1-g09-localhost-proxy-r41`, ID
  `2d579168976e07fe66799900b072b226ec72428e7dd6568f4c99835c3e2dd316`, image
  `studiamatch-h3req1:20261009-v3`, running, published only on
  `127.0.0.1:3335`.
- `h3req1-g09-uat-app-20261010-r12`, ID
  `0e3f4b56fff870062788c53879a538efa31963f81ad1be5dbfb49af8cde12fc7`, running,
  Pages/workerd internal port 3350 and the R41 static output mounted read-only.
- `h3req1-g09-uat-pg17-20261010-r12`, ID
  `4e2891cfad4a6e5acb875fcb0b890db19c1f096acf5c4370c6fc47cc23d644e7`, running,
  PostgreSQL 17.11 synthetic fixture; no host port published.
- Existing R12 public proxy `h3req1-g09-localhost-proxy-r12` remains on
  `127.0.0.1:3333` and was not modified.

No response body, cookie, credential, or secret was saved. This postflight does
not make LOCAL-03/16 complete: R41 and R12 expose different static bundles even
though their Admin/runtime checks share the R12 PG17 synthetic data.

La primera pasada del verificador auxiliar de capturas resolvió las rutas
container-relative del JSON (`../evidence/...`) como paths del checkout y acabó
`exit=1` con `FileNotFoundError`; no modificó ni perdió archivos. Se corrigió
solo el mapeo a los PNG preservados en el directorio R41 y los tres SHA-256
coincidieron con el manifiesto: desktop
`db4243b8e91a92ac63d24287f60c402e103979877f42a4ba018abee6adce5296`, tablet
`38c4f493c693451a79e387eafcbd57cb81ce25d4b6a6ed26af21eb7c3b1654e3` y móvil
`4a969f86e144c40fa8de7a28938fcd9b86464bf5a168720ea1427754caee87fb`.
