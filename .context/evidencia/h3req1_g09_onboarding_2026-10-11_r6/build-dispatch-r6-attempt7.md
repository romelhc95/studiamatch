# Mock build R6 — intento 7

- Candidato: feat/h3req1-sync-20261002 at baseline 4eb4d877a50b012bb630a129bd0c74482c33be9c.
- Exit del runner: 1. Fase: isolated-mock-build. Error: INTERNAL_NETWORK_PROXY_MEMBERSHIP_MISMATCH.
- El predicado de identidad del proxy y ambas conexiones de red sí pasaron. La prueba CONNECT sintética a example.com recibió 403; el contador final fue allowed=0, rejected=1, upstream_failed=0.
- No se creó el contenedor de build ni se conectó a ningún host upstream.
- El proxy y ambas redes exactas quedaron retirados. R12 y studiamatch-dev siguieron activos; 127.0.0.1:3333/ respondió HTTP 200.
- Evidencia sanitizada: font-egress-proxy-r6-attempt7.log, font-egress-proxy-r6-attempt7.identity.txt, font-build-networks-r6-attempt7.identity.txt.
- El runner detectó una discrepancia al comparar nombres de miembros de la red interna. La conexión del proxy estaba acreditada por su propia inspección estructurada; se reemplazará la comparación de nombres por conteo de endpoints más verificación de conexiones de cada contenedor conocido.
