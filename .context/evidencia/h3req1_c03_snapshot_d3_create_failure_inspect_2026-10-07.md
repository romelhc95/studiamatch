# Resultado J1 — lectura de error de creación/inicio D3

Fecha: 2026-10-07. Recurso: solo contenedor D3 con ID
`81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf`.

## Permiso y ejecución real

- Manifiesto JIT aprobado: `.context/operaciones/manifiesto_jit_h3_close03_d3_create_failure_inspect_2026-10-07.md`.
- SHA-256 aprobado del manifiesto: `1ec96b5a1820e519625bce113777e99fb1e2e693c8317f27625358ec08b241f1`.
- El manifiesto se conserva intacto como snapshot aprobado pre-ejecución; su estado
  inicial de propuesta no sustituye este resultado consumido.
- Permiso consumido: una invocación del query read-only `docker inspect --type container`
  por el ID exacto, luego de validar rama/HEAD, hashes D3 y socket Unix local.
- No se consultó por nombre, no se leyeron logs ni se ejecutó ninguna operación de ciclo
  de vida sobre el contenedor.

## Resultado y límite

El `inspect` devolvió exit 0, con salida dentro del límite de 8 KiB y socket estable antes/
después. El parser/sanitizador falló cerrado con el resultado visible
`NO-GO: identity/schema/sanitizer failed; raw output discarded`. No se expuso ni persistió
la respuesta cruda. No se pudo distinguir si falló la identidad/schema del objeto o el
sanitizado de `.State.Error`; por lo tanto, no se recuperó el motivo de create/start y no se
puede afirmar que el campo `.State.Error` estuviera vacío.

La salida temporal quedó en memoria del proceso y se descartó al terminar. No hay raw
output, credenciales, `.Config.Env` ni datos secretos en esta evidencia. El último estado
observado del recurso fue `created` en D3; J1 no cambió el recurso, pero no se hizo una
segunda lectura para confirmar su estado actual.

## Preservación y siguiente gate

J1 está consumido: no se repite con el mismo permiso. D3, D2 y S1 también siguen consumidos.
No se ejecutaron tar, snapshot, npm, Pages/workerd, Edge, SQL, PostgREST, Auth ni remoto.
C02 v4 y C03 SQL v3 conservan su vigencia por hashes/alcance.

J2, lectura acotada solo de `.State.Error`, se aprobó y consumió una vez. Resultado y
alcance están en [evidencia J2](h3req1_c03_snapshot_d3_state_error_read_2026-10-07_j2.md):
Docker informó que el logging `local` no admite compresión habilitada con `max-file=1`.
La causa del create/start D3 queda demostrada; el fixture tar nunca corrió, por lo que
ownership sigue sin probarse. El recurso no se modificó.

Siguiente: runner D4 independiente con la corrección mínima `--log-opt compress=false`,
sin cambiar `max-size=1m`, `max-file=1`, identidad, permisos ni límites; nuevo manifiesto
y JIT requerido antes de crear/iniciar cualquier contenedor. No declarar causa de S1.
