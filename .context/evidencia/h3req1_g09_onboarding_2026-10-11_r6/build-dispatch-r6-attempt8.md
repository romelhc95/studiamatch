# Mock build R6 — intento 8

- Candidato: feat/h3req1-sync-20261002 at baseline 4eb4d877a50b012bb630a129bd0c74482c33be9c.
- Exit del runner: 1. Fase: isolated-mock-build. Error: BUILD_NETWORK_IDENTITY_MISMATCH.
- Preflight PASS. Proxy identity, dos redes exactas y deny probe PASS; el proxy registró allowed=11, rejected=2, upstream_failed=0. La conexión a fuentes llegó a operar.
- El build quedó en ejecución y su log inició “Creating an optimized production build ...”. El runner lo detuvo al no aceptar la proyección textual de NetworkSettings.Networks; no se dispone de exit de Next, por tanto no se clasifica como fallo de aplicación.
- Cleanup: build y proxy retirados por ID exacto; redes internas/egress vacías retiradas por ID. R12 continuó HTTP 200.
- Evidencia sanitizada: mock-build-r6-attempt8.log, build-container-r6-attempt8.identity.txt, font-egress-proxy-r6-attempt8.log, font-egress-proxy-r6-attempt8.identity.txt, font-build-networks-r6-attempt8.identity.txt.
- Corrección: validar modo, cantidad de redes del contenedor y el ID/label/modo del objeto de red por separado, evitando comparar la serialización del mapa completo.
