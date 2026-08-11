# F10.10 M3 Reader - Evidencia Preflight Local Passwordless

| Campo | Valor |
|---|---|
| Subfase | `F10.10/M3` |
| Resultado | `M3_READER_PREFLIGHT_PASS_DDL_GATE_PENDING` |
| Gate consumido | `APPROVE_F10_10_M3_READER_PREFLIGHT_FREE` |
| Payload canonico | `sha256:68fd845808dbe694984ffbdd087b44e19754b4c76c14da862d74dad232971613` |
| Resultado local canonico | `sha256:9ea235083a5c7e32df30c62a462fefb96bc91d19295e1339a3e9112b2d3a41b1` |
| Ejecutado | `2026-08-11T20:09:22Z` |
| Valido hasta | `2026-08-11T23:00:23Z` |
| Decision | `PASS` |
| Gates posteriores consumidos | Ninguno |

## Resultado Sanitizado

```text
mode = LOCAL_PASSWORDLESS_ONLY
network = none
password_consumed = false
remote_read = false
remote_ddl = false
remote_dml = false
reason_codes = []
candidate = ea3adaf6fd9847fc5cf98f4d0ed6449a41fae1a1
candidate_tree = 1929c3cc6dd3ab0f5b822a530ee2d08285ff9345
payload_merge = 47100311a10731ea6297af5c8c1e2e64f5d100b2
query_set_digest = sha256:e18d56ae0cbae4e547c1e4e9706db8306a24e3a748da1ce167c54f8b808c84b7
target_binding_digest = sha256:013972e22906ea23d2aa6d4f7caaa9a92f93d6c4618d5e44e93f49c897ae0f01
```

El [resultado sanitizado canonico](./m3_reader_f10_10_preflight_result_2026_08_11.json)
permite reproducir publicamente su digest sin inspeccionar artifacts privados. El
preflight valido el [payload promovido](./m3_reader_f10_10_preflight_payload_2026_08_11.json),
vigencia, candidate/tree, query set, blobs package/compensacion, CA y binding. La
configuracion privada y el CA permanecieron en `local/f10_10/m3/`, gitignored; no
se versiono ni imprimio URL, project ref, host, usuario exacto, ruta CA o password.

## Envelope De Ejecucion

La ejecucion exitosa uso la imagen local `studiamatch-f4-local:3e2b672`, un
contenedor efimero con `--network none`, checkout bind-mounted read-only y
`PYTHONPATH=/app`. El runner verifico que la unica interfaz fuera `lo`. El modo
offline recibio un `connection_factory` centinela bloqueante que habria lanzado
`STOP_NETWORK_ATTEMPT`; no debe describirse como ausencia literal de factory.

Dos intentos de bootstrap anteriores abortaron antes del preflight y no produjeron
resultado: el primero por quoting invalido del codigo inline y el segundo por
`PYTHONPATH` ausente. No leyeron configuracion completa, no validaron payload y no
abrieron red. El tercer intento fue la unica ejecucion `PASS` del preflight.

## Limites De Evidencia

- El JSON local no esta firmado; su procedencia se apoya en el stdout capturado y
  en el comando de contenedor observado. Su copia sanitizada canonica queda
  versionada para reproducir el digest, no para afirmar una firma inexistente.
- El bind read-only es propiedad del comando externo y no puede demostrarse solo
  desde el JSON resultante.
- El runner usa `assert` y fue ejecutado con Python normal, sin `-O`.
- Los digests completos de package, compensacion, CA y provisioner permanecen
  ligados por el payload canonico; el resultado publica solo lo necesario.

## Decision

```text
M3_READER_PREFLIGHT = PASS
APPROVE_F10_10_M3_READER_PREFLIGHT_FREE = CONSUMED_ONCE
APPROVE_F10_10_M3_READER_DDL_FREE = NOT_CONSUMED
APPROVE_F10_10_M3_READER_Q0_FREE = NOT_CONSUMED
APPROVE_M3_FREE_READONLY = NOT_CONSUMED
APPROVE_F10_10_M3_READER_TEARDOWN_FREE = NOT_CONSUMED
```

Este PASS no concede conexion Free, DDL/DML, password, Q0, lectura ni teardown.
El siguiente paso permitido es preparar un payload DDL Free separado para revision
humana; ejecutarlo requiere su gate literal independiente.

El CI post-merge de PR #358 detecto una carrera independiente del harness local:
`pg_isready` aceptaba el servidor temporal del entrypoint PostgreSQL antes de que
este lo apagara para iniciar el servidor final. El PASS preflight permanece
inalterado, pero DDL queda bloqueado hasta promover una espera explicita de fin de
init y readiness final estable.

Enlaces: [estado](../estado_del_proyecto.md) |
[rebaseline](./m3_reader_f10_10_rebaseline.md) |
[scope](./m3_f10_10_scope_por_ambiente_target.md)
