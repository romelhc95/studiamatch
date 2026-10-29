# Validación local de relaciones semánticas Admin — R10

> Corte: 2026-10-13 06:05 UTC. Esta nota acredita ejecuciones locales contra el WIP montado; no declara adopción remota ni reemplaza R178/R181/R182.

## Checkout e inputs

- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El HEAD no representa el WIP local.
- Runtime: contenedor existente `studiamatch-dev`, imagen `studiamatch-h3req1:20261009-v3`, estado healthy antes de las ejecuciones.
- Para Node se usó `env -i` con solo `PATH` y `HOME`. Para Python se añadió `PYTHONDONTWRITEBYTECODE=1`; no se cargaron `.env*` ni credenciales operativas.

| Relación examinada | Hashes SHA-256 actuales cotejados | Resultado local y evidencia |
|---|---|---|
| `web/functions/_lib/admin-bff.ts` → `tests/h3_admin_bff_mock_uat.mjs` | Fuente `691a996fe32c3d75aadece6cfd615ed7ec2230460cdfab4c30b8b7b859fbdeb9`; runner `7c1fefd3f8743a1b3a898bf4a1b200b7c2f486380bc293045760435644065b40`. Host y `/app` devolvieron ambos hashes actuales. | Docker, `node tests/h3_admin_bff_mock_uat.mjs`: PASS, 96 checks; 10 casos de cuota, 6 rechazos de cookie de actividad, 1 rebind MFA, 4 rechazos de origen, 4 rechazos de configuración de firma y 7 cookies Auth expiradas. Exit 0. La prueba usa transportes mock en memoria; no valida Auth, PostgREST ni deployment remotos. |
| `web/functions/_middleware.ts` → `tests/h3_admin_safe_suspend_uat.mjs` | Fuente `237bc47043ed8a7f0604445d43c2ca2042e352373ee165a56cf669dd4821fd9b`; runner `a54344bfd73051e523c3717ac9e3f9348982fb49feb749af5d30e3ac9a3a880d`. | Docker, `node tests/h3_admin_safe_suspend_uat.mjs`: PASS; 5 casos de suspensión Admin, 8 aliases codificados rechazados, páginas públicas preservadas y cookies limpiadas. Exit 0. Es fixture de middleware, no un Worker desplegado. |
| `supabase/functions/admin-invite/index.ts` y `supabase/config.toml` → `tests/test_admin_invite_edge_contract.py` | Edge `1569b90394b313a4b42e4e50158da077cec42d26356c0d713b16535f47053a60`; config `531705c8502ca635a08d2d484368165dc493b71b984a65d4fc249ced138e6857`; test actual `38b7895fad9113204a8b2f9abc40802d05156b2158777dbad40f629dd37b7cb0`. | Ejecutado con `tests/test_h2_pro_migration_controls.py` en el mismo comando Docker: 24 passed en conjunto, exit 0. Son comprobaciones de contrato local; no envían invitaciones ni configuran Supabase remoto. |
| `.github/workflows/db-sync-to-pro.yml` y controles de migración → `tests/test_h2_pro_migration_controls.py` | Workflow `3899f29a026861400707827e7e6c9248446d938451232eb5fee157775b39fda8`; test `0714ba8ff11fa0f7627d2b5585d465a45dc673b1955befa7e3cd1cc38a1c7838`. | Incluido en la corrida Docker anterior de 24 tests. Se comprobaron manifiesto cerrado, dry-run/apply, controles de workflow y rutas permitidas de forma estática; no se leyó ni modificó Pro. |
| Plantillas Auth → callbacks/recuperación | `invite.html` `b4466f598edc65c8c3a9f117bd2180de805f7eb0417b9daf6cf6d065af8b8ff5`; `password-recovery.html` `d29ad2a0aafff8987b5997525b4b43f84a55b34a34e3e966207d04932cf5c4cb`; tests de callback `3264e39c0337e11ec7afc2642855add6067ed171baecb5f5fa7dfbc25198f5b9` y recuperación `67acb41264622b823903fc26efdbb96a651755362f74c2f89d95ea9e9d493842`. | Los cuatro hashes coinciden con el manifiesto fuente R8. R178 documenta el selector `pytest tests/test_*.py`: 337 passed, 4 skipped y 1 warning en Docker. El resultado es agregado; el manifiesto enlaza los inputs de las aserciones exactas sobre placeholders/callback. No afirma entrega de correo ni uso de plantilla en Auth remoto. |

Los hashes de config/Edge/workflow/test se calcularon sobre el checkout candidato después del montaje. Los manifiestos históricos R8 y el informe R178 se conservaron sin cambios.

## Intento de entorno que no ejecutó pruebas

Una primera invocación aisló `PATH` sin conservar `/opt/venv/bin`; `/usr/bin/python3 -m pytest` terminó con `No module named pytest` antes de importar o ejecutar tests. No se contó como resultado. La ejecución corregida usó `/opt/venv/bin/python` dentro del mismo contenedor y pasó los 24 tests.

## Clasificación y límites

- **Implementación local actual:** hashes de los paths anteriores, incluido el WIP BFF. El BFF actual (`691a…`) difiere del input R76 (`0cf11c…`); por eso R76 se conserva como historia y no se reutiliza para el hash nuevo.
- **Validación local acreditada en este corte:** BFF UAT 96 checks; middleware fixture; 24 contratos Python combinados. La relación de plantillas se vincula al resultado agregado R178 solo porque sus cuatro hashes coinciden con R8.
- **Historia:** R76 (96 checks) y el resultado agregado R178 permanecen inalterados; la ejecución focal actual es adicional y no cambia los criterios del cierre funcional.
- **Remoto desconocido y pendiente:** Pages bindings/hostnames/flags/keys, despliegue y configuración de Edge/Auth/templates, `pgrst.db_pre_request`, grants, RPC y baseline Pro. No se hizo consulta remota.
- **Pendiente local del submódulo:** no se renovaron aquí los UAT específicos del Worker/DO de cuota; sus relaciones siguen `pending` hasta cotejar inputs y resultado. El pase de la cuota de invitación en UI no se atribuye automáticamente al Durable Object.

No hubo SQL operativo, escrituras, deploy, consultas cloud ni cambios funcionales. El detalle por grupo y las rutas de mantenimiento están en [runtime Admin](../componentes/admin_runtime.md), [pruebas/evidencia](../componentes/pruebas_evidencia.md#admin-bff-uat-local) y el [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#runtime-admin).

[Estado operativo](../estado_del_proyecto.md) · [Índice](../indice.md) · [Reanudación R10](h3req1_documentacion_semantica_reanudacion_2026-10-13_r10.md)
