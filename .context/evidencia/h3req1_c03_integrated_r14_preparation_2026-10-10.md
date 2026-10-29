# G07 R14 — adaptador same-origin y clasificación CSRF cerrada

## Tareas y gates

1. Confirmar rama, HEAD, estado de trabajo, recursos previos y manifiesto R14: PASS previo al runtime.
2. Reproducir el login integrado con Pages/workerd, Edge, PostgREST y PG17 locales: pendiente del comando R14.
3. Si login pasa, completar el contrato C03 y su recuperación; solo exit 0 completo cierra G07.
4. Registrar el resultado real y mantener G08/G09 pendientes hasta sus pruebas propias.

## Ficha de impacto

- Componente: adaptador del runner integrado que genera la solicitud Pages/workerd de login y clasifica respuestas de login.
- Consumidores: `tests/h3req1_c03_integrated_drill_r14.sh` y sus pruebas contractuales; no modifica el BFF ni el comportamiento de producto.
- Contratos preservados: BFF/HttpOnly, same-origin CSRF, gateway firmado, cuotas, roles, MFA, SQL y runtime fijados.
- Evidencia preservable: R13 completo, PASS estáticos R14, C03 SQL 41/41 y snapshot/workerd S9.
- A renovar: ejecución integrada G07 porque el adaptador de request/classifier forma parte de los inputs de runtime.
- Recuperación: el runner usa recursos etiquetados por JIT, manifiesto y nonce; failure-stop detiene solo servicios del intento y conserva log/recursos. No toca el checkout original, `studiamatch-dev`, `.env*`, secretos ni servicios remotos.

## Estado previo

- Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`; rama `feat/h3req1-sync-20261002`; HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP amplio conservado; no staged ni reset. `studiamatch-dev` healthy en la última consulta segura.
- R13 terminó exit 1 en `/control/login` con `LOGIN_HTTP_STATUS_403`; la secuencia previa había llegado hasta Edge activo. No se atribuyó el resultado al producto.
- R14 construye un objeto `Request` HTTPS usando el mismo hostname que su header Origin, fija `Sec-Fetch-Site: same-origin` en mutaciones y entrega ese Request a `worker.fetch`. El clasificador solo emite `LOGIN_CSRF_REJECTED` para status 403 y código exacto `csrf_rejected`; todo código desconocido conserva el resultado genérico por status.

## Inputs y revisión estática

- Manifiesto: `tests/h3req1-c03-integrated.sha256`, 65/65, SHA-256 `2d7a88458de45f70941c256263c51118eb5e02fc71163324c987603e6e05e8a0`.
- Runner R14: SHA-256 `60ac11ca7cb17a871941241096741c2eab22ccd5081c76a1b9f2009fbb5bd78a`.
- Adapter runtime: `8768586492318ebe33e3d461e5ec86ca06b336c72eb5d2248b84aba99a75b41f`.
- Login classifier: `ee7cb8b7d2e5df826bef00d071a626b87bd17ccab7715a5673ef52b970464f77`.
- Tests contractuales: `8d5403810c3c8d6102ff01ff095924364eee498037a7706325124464164cd52c`, 15/15 PASS.
- Runner: Bash syntax PASS; ShellCheck 0.11.0 warning-level PASS; `git diff --check` PASS.
- Revisión independiente estática: PASS sin bloqueantes; no ejecutó runtime.
- Evidencia detallada: [R14 static validation](h3req1_c03_integrated_r14_static_validation.txt).

## Próximo ensayo local

Una ejecución con timeout externo 1800 s, JIT local identificado como `H3-CLOSE-03-INTEGRATED-2026-10-10-R14` y SHA fijado del manifiesto. El runner crea resources R14 únicos, usa imágenes locales fijadas, redes internas, Postgres desechable, caches read-only y fixtures sintéticos; stop-on-failure, sin reintentos. No se inicia hasta que el preflight del propio runner vuelva a confirmar los pins y el daemon esperado.
