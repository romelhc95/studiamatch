# Mock build R6 — intento 5

- Candidato: feat/h3req1-sync-20261002 at baseline 4eb4d877a50b012bb630a129bd0c74482c33be9c.
- Resultado: no se creó el contenedor de build; el despacho se detuvo al conectar el proxy.
- Exit del runner: 1.
- Fase: isolated-mock-build.
- Error: FONT_PROXY_EGRESS_CONNECT_FAILED.
- Causa demostrada: Docker Desktop rechaza conectar un contenedor lanzado con --network none a otra red.
- El proxy sí arrancó en modo none, emitió READY, y la limpieza verificó y retiró su ID exacto. Ambas redes etiquetadas quedaron vacías y se retiraron por ID. No hubo requests upstream ni build.
- Evidencia sanitizada:
  - font-egress-proxy-r6-attempt5.log
  - font-egress-proxy-r6-attempt5.identity.txt
  - font-build-networks-r6-attempt5.identity.txt
- La app, el PG17, el proxy loopback R12 y studiamatch-dev siguieron en ejecución; 127.0.0.1:3333/ respondió HTTP 200.
- Corrección para el intento 6: arrancar el proxy únicamente en la red interna y después conectarlo a la red egress con gateway priority 1. La app de build permanece solo en la red interna.
