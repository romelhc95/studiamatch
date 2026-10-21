# Procedencia del build mock — onboarding R6

## Candidato e inputs

- Checkout: /home/romel/src/studiamatch-h3req1-sync-20261002
- Rama: feat/h3req1-sync-20261002
- HEAD baseline: 4eb4d877a50b012bb630a129bd0c74482c33be9c
- Fuente allowlisted: 643 archivos; manifiesto source-inputs-r6.sha256 SHA-256 7e4349e657591069a7accf7eeaa1fc35b95cea896c449f8b3d40a5bca032ab19.
- web/package.json SHA-256 dfdd9a7ea0ff192c7eda7c33d9a2141b5b761fb0c53c472d8209e4fa2c309ab2.
- web/package-lock.json SHA-256 d526163caba9300baf9329121979b9c9bc1bd24dfc10b1b4159d0ee8a36334db.
- Volumen web/node_modules h3req1-g08-web-node-modules-r1, digest ea36c13c72f0b1c13f2791118b4eb7ad89c17ba9ecbce44d413b794e6837e625.
- Fixture de build sintético mock_build_fixture_server_r6.mjs SHA-256 8c00031c173a556e468e53d1045883890d2683c60bae30dd53fba28ce7266ccf.

## Ejecución

- Imagen local studiamatch-h3req1:20261009-v3, image ID sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63, Node v20.20.2, Next.js 16.3.8.
- Runner R6 SHA-256 ef080679af3052ef62bdb5dfbaab71bb9e6f082cff450089b54985e6262a1eda.
- Build output: npm run build:mock, NEXT_PUBLIC_H3_MOCK_URL=http://127.0.0.1:3211.
- Datos del fixture: curso sintético Synthetic H3 Mock Course; no cuentas ni datos operativos.
- Límites del build: 4 GiB RAM, 2 CPU, 256 PIDs, rootfs read-only, /source read-only, dependencias read-only, output separado; no .env*, credenciales ni volumen de base de datos.
- La app de build solo estuvo conectada a h3req1-g09-font-build-internal-20261011-r6 (672a81aab082b9cf6c5be4ed4e14454f052e0a2d3a1eee4d57e8b0f6b58fd26e). El proxy h3req1-g09-font-proxy-20261011-r6 (ebf261b95a568dbed36c449162999a9545a28861ede7325d689fcb1c420f8dbc) fue el único miembro de la red de egress h3req1-g09-font-build-egress-20261011-r6 (323f21082b126c937aad85e0eb9d934467e5405f8401a97bc36c20616ddca388).
- Proxy CONNECT con script preexistente revisado, SHA-256 e0bbc3b27178de254d7142a952dba2a24f2fa12d76cb4bbd01c28518a3801d79; hosts permitidos fonts.googleapis.com:443 y fonts.gstatic.com:443, con validación de IP pública. Sin descifrado TLS.
- Sintéticos del proxy PASS; conexión no allowlisted a example.com:443 fue rechazada HTTP 403 antes del build. La app de build tuvo solo la red interna y variables proxy; no tenía ruta egress directa.
- Resultado de contadores: allowed=12, rejected=2, upstream_failed=0. Una denegación fue la sonda negativa conocida; la causa de la otra denegación no se registra por separado. Ambas fueron cerradas por el proxy; ninguna solicitud rechazada llegó upstream.
- Cuatro intentos anteriores se preservan en los logs mock-build-r6-attempt1..4.log y en build-dispatch-r6-attempt5..8.md; cada rechazo del runner ocurrió antes de validar el producto. El intento 9 fue PASS.
- Contenedor de build 9af2d773ee82dec86694665189c9af8745ab6f8ec2aedcf1de2bc46d16df9635, salida 0. El proxy y ambas redes se detuvieron/eliminaron por IDs exactos; no se eliminaron imágenes ni volúmenes.
- La app R12, PG17 R12, proxy de localhost Windows y studiamatch-dev permanecieron activos; http://127.0.0.1:3333/ devolvió HTTP 200 después del build.

## Artefactos verificados

- Salida mock-out-r6/; 126 archivos. Ruta verificada courses/mock/mock-course/index.html contiene Synthetic H3 Mock Course.
- Salida incluye 11 fuentes WOFF2 descargadas bajo la regla allowlist.
- Manifiesto SHA-256 mock-out-r6.sha256: d5cc70219d27a573f39a1e6b374def51187bb61fc25d9612fe51e07fba2a905c; sha256sum --check --strict PASS.
- El build mock acredita exclusivamente el bundle sintético y no sustituye el build normal, runtime Pages/workerd, C03 integrado ni onboarding.
