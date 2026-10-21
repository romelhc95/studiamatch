# Mock build R6 — intento 6

- Candidato: feat/h3req1-sync-20261002 at baseline 4eb4d877a50b012bb630a129bd0c74482c33be9c.
- Resultado: el proxy inició y Docker aceptó las dos conexiones, pero el preflight estructurado rechazó la identidad combinada. El contenedor de build no llegó a crearse.
- Exit del runner: 1.
- Fase: isolated-mock-build.
- Error: FONT_PROXY_IDENTITY_MISMATCH.
- El proxy emitió READY y fue detenido con código 0; no se registraron conexiones permitidas, rechazadas ni fallidas upstream.
- La limpieza verificó y retiró el ID exacto del proxy y dos redes etiquetadas vacías. R12 y studiamatch-dev permanecieron activos; 127.0.0.1:3333/ respondió HTTP 200.
- Evidencia sanitizada:
  - font-egress-proxy-r6-attempt6.log
  - font-egress-proxy-r6-attempt6.identity.txt
  - font-build-networks-r6-attempt6.identity.txt
- No hay indicio de fallo del producto; sigue pendiente determinar cuál campo del predicado de identidad no coincide.
