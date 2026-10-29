# Onboarding R6 — intento 1

- Exit 1, fase preflight, error SOURCE_PROVENANCE_MISMATCH.
- No se crearon ni arrancaron contenedores, redes o base de prueba; Chromium no se lanzó.
- El hash del manifiesto seguía en 7e4349e657591069a7accf7eeaa1fc35b95cea896c449f8b3d40a5bca032ab19. Los 643 paths reales coincidían con los 643 del manifiesto cuando se retiraba correctamente el prefijo SHA-256.
- Causa demostrada: local_runner_guards_r6.sh solo retiraba el hash si el path comenzaba por ./, pero sha256sum registró db/migrations/... sin ese prefijo. Por ello el primer path esperado incluía el digest.
- Corrección mínima: retirar el digest y el separador de dos espacios independientemente del prefijo ./; normalizar opcionalmente ./ después.
- El checkout original, el candidato, R12 y studiamatch-dev quedaron intactos.
