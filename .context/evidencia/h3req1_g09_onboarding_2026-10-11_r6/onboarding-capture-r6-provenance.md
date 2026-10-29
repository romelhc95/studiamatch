# Instrumentación de capturas de onboarding R6

- Prueba de producto preservada, sin cambios: tests/h3_invitation_uat.mjs, SHA-256 f006db83cd578ad6a40302ae2d43aa3cffc11574bbe7760e4ac3dc272e4caa2e.
- Copia instrumentada de evidencia: h3_invitation_uat_capture_r6.mjs, SHA-256 f8b243c3ff6867bc263fe7929d35f611468fee30e9ef000575432f8c25633bc2.
- La única lógica agregada crea un PNG al finalizar cada caso PASS y limpia inputs tipo password en el DOM antes de capturar. No cambia requests, datos, pasos, asserts ni pacing de invitaciones.
- Los diez identificadores cubiertos son INV-001, INV-002, INV-003, INV-004, INV-005, INV-007, INV-008, INV-009, INV-012 e INV-013.
- Los casos y capturas se ejecutan con Chromium 1228 headless dentro del contenedor R6 basado en studiamatch-h3req1:20261009-v3. No se abre ventana de navegador.
- Los PNG quedan en run-r6/onboarding-r6/screenshots/, con manifiesto SHA-256 separado.
- No se produce video ni trace de red: esa traza puede guardar tokens de invitación y cuerpos de autenticación. Las capturas se toman después de cada caso y no contienen valores de campos de contraseña.
