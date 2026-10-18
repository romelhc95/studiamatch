# G09 onboarding R8 e INV-008 — 2026-10-11

## Resultado

El recorrido sintético R8 terminó **PASS, 10/10 casos, cero retries**. INV-008 confirmó que una invitación aceptada sin password inicial termina en /admin/accept-invite/, muestra “Definir password” y no llega al panel antes de completar el setup. Después de definir el password, el usuario sintético llega al panel; el caso continúa con MFA y permisos según el runner.

Casos: INV-013, INV-008, INV-001, INV-002, INV-009, INV-007, INV-003, INV-004, INV-005, INV-012. El runner exige el conjunto y orden exactos, pacing mínimo 20,100 ms entre invitaciones, diez capturas y el vídeo del flujo principal. El resumen sanitizado está en run-r7/onboarding-r8/onboarding-summary-r8.json; SHA-256 del resumen 8121c7b4aa0c0afadcaf67385e3dfd876286f48f76ce2fb5d51910cf6b39bea9. Manifiestos verificados:
- run-r7/onboarding-r8/onboarding-screenshots-r8.sha256: SHA-256 22d134a9ea4f388a14847f6d52b772b8a94625dbf290de31aab6d0884d43fdcd; 10/10 PNG.
- run-r7/onboarding-r8/onboarding-videos-r8.sha256: SHA-256 c1d0c278775c6b5c2b5a69647808e337c2b663735815449384e647fdba7e94c5; video 366,847 bytes, SHA-256 d3bcc728cdac293c85a591edaf34d2b819038a3ba131cdb94ffbc1a917d142d3.

## INV-008 diagnóstico y corrección ya aplicada

La reproducción local posterior sí clasificó el caso rojo: después de aceptar la invitación, el BFF devolvía sesión activa con rol authenticated mientras el miembro seguía password_pending. admin/page.tsx lo rechazaba hacia /admin/login/; admin/login/page.tsx interpretaba cualquier sesión como lista y la redirigía a /admin/. Esto producía un ciclo autenticado Admin → login → Admin. No fue un problema de Auth, base ni de sincronización del test. El diagnóstico está en run-r6/onboarding-r6-diagnostic-v2/result.json; la captura roja previa se conserva en run-r6/onboarding-r6-inv008-diagnostic-v2/screenshots/INV-008-admin-guard.png.

La corrección vigente en web/src/app/admin/login/page.tsx consulta el estado de onboarding para distinguir una sesión pendiente de una sesión lista: el pendiente va a aceptar invitación/setup; una sesión ready o legacy sigue a /admin/. tests/h3_invitation_uat.mjs ahora comprueba URL, heading, texto y CTA, y que el panel no sea accesible antes de definir password. La prueba R8 actual PASS valida el comportamiento afectado; no se tocaron MFA, roles ni la sesión HttpOnly.

La primera ejecución R6 que falló tenía un wrapper sin clasificación; la salida V1 OUTPUT_REJECTED fue un filtro del runner, no resultado de producto. La V2 R6 10/10 anterior se conserva, pero no tapa el rojo de guard reproducido después ni se usa sola para afirmar estabilidad. R8 renueva la evidencia tras el arreglo funcional.

## Servidor, navegador y Windows

R8 usa el export mock actual (126 archivos), Pages/workerd + mock Auth/BFF y PostgreSQL 17.11 sintético en Docker Desktop. Playwright Chromium 1228 corre **headless, sin ventana visible**. Los secretos del fixture se generan en memoria y solo se pasan como variables a los contenedores; no se almacenan en el resultado ni se muestran.

Acceso de lectura desde Windows: http://127.0.0.1:3334/. Windows PowerShell Invoke-WebRequest -UseBasicParsing recibió HTTP 200 (18,891 bytes); desde WSL también HTTP 200. El proxy acepta solamente GET/HEAD, rechaza POST con 405 y tiene destino fijo al contenedor R8. No sirve de proxy abierto ni expone credenciales.

| Recurso | Nombre | ID / imagen | Función |
|---|---|---|---|
| App | h3req1-g09-onboarding-app-20261011-r8 | 9921c96524bf6b97e567248a77198651caf1199b143d9af1ed2327b6032fab07; studiamatch-h3req1:20261009-v3 | Pages/workerd y mock Auth/BFF del candidato |
| PostgreSQL | h3req1-g09-onboarding-pg17-20261011-r7 | 9c872daa7928dd5aee82fd88fad1fef1ca3ef15c2210068853a531aa30c37e66; PostgreSQL 17.11 fijado | DB h3_final_uat_onboarding_g09_20261011_r7, fixture sintético retenido |
| Proxy | h3req1-g09-onboarding-localhost-proxy-20261011-r8 | 2a41eca839325bc612a49753ad0a662b09b0a676e29aa01d3831b9a13f25febd; misma imagen | loopback 127.0.0.1:3334, GET/HEAD al app |
| Red interna | h3req1-g09-onboarding-net-20261011-r7 | 6a30b00505160d5ee8858e206d1dde6a7624747d6e08614da1c1883a46913473 | DB, app, proxy; internal=true |
| Red de acceso | h3req1-g09-onboarding-access-20261011-r8 | a4026b6ddcfc5d109e82fd5865086291c56af87121650578ae71d6b9968e9bcd | Proxy solamente, binding loopback |

El app se ata a 0.0.0.0:3330 solo en su contenedor de fixture para que el sidecar alcance el runtime por la red interna. El runtime no publica ese puerto al host. La red de acceso del sidecar es una bridge Docker no-internal porque Docker Desktop no publica puertos host de una red internal; el host binding es exclusivamente loopback. El código del proxy limita método y host upstream.

## Fallos del bootstrap y distinción de causa

Se preservan estos intentos; ninguno corrió onboarding salvo R8:
1. R7 preflight detectó que el node --check recibió una ruta WSL que no existe dentro de Docker. Se corrigió al path montado /app/.context/...
2. R7 inició PG17 y Pages, pero Docker Desktop no materializó el port binding del sidecar en una red internal (NetworkSettings.Ports=[]; docker port sin puerto); el runner detuvo antes del UAT. El PG17 y sus datos se conservaron.
3. R8 reemplazó solo app/proxy fallidos por IDs exactos, conservó el PG17 y separó red interna y red loopback de acceso. El primer guard confundió los tres volúmenes de dependencias read-only con datos propios; se cotejó y acotó a esos tres mounts conocidos, sin borrar volúmenes.
4. El primer proxy R8 todavía tenía destino DNS R7: app directo desde el proxy respondió 200, la ruta proxy respondía 502. Se corrigió el destino fijo a R8; nueva pasada de acceso confirmó 200/405 y permitió ejecutar UAT.

Las causas fueron de rutas/topología y una referencia del sidecar, separadas de la causa funcional INV-008. Se preservan scripts, identidades, runtime logs, capturas rojas y verdes; no se hicieron prune, se borraron volúmenes ni recreación de PG.

## Artefactos revisables

- Captura de INV-008 aceptada: run-r7/onboarding-r8/screenshots/INV-008.png.
- Capturas INV-001, INV-002, INV-003, INV-004, INV-005, INV-007, INV-008, INV-009, INV-012, INV-013 en el mismo directorio.
- Vídeo del recorrido principal: el original se conserva solo en R18/local y se excluye de este paquete público; véase [la nota de sanitización visual R19](h3req1_visual_evidence_redaction_2026-10-18_r19.md#inventario-local-de-originales).
- Identidad y topología: run-r7/onboarding-r8.identity.txt.
- Runner y helpers: onboarding_local_runner_r8.sh, onboarding_r8_finish.sh, h3_local_runtime_server_r8.mjs, localhost_readonly_proxy_r8.mjs; SHA-256 en el historial/manifiestos de ejecución.

## Límites

Esta aceptación cubre el onboarding local sintético y el INV-008 corregido; no cierra las otras áreas LOCAL-01..23, G08, revisión final ni G09 completo. No se usaron cuenta real, correo real, tokens de cloud ni escrituras remotas. No se ejecutaron CI, PR, merge ni despliegues.

