# H3REQ1 G07 — resultado e inventario R46

## Identidad y resultado

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD baseline: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- R46: ejecución única, timeout externo 2400 s, cero retries; resultado **PASS local sintético**. El runner emitió su línea final `C03 integrated drill: PASS` después de validar cleanup y log.
- Manifiesto archivado: 126 inputs, SHA-256 `1b4047f29e75fca65935b4984b0c9c3023e1944c3f2f8b1f2abe363aeeb23445`.
- Runner SHA-256 `073950df2ff3e0a6744cf53e0024b0cb31b711decd6a3bc2f8cbc22cf867825e`.
- Setup SQL local SHA-256 `2157f16d793613aa4d8bafe6fe2a7d3601c5c11a049752d0641458afaa0f5459`.
- Log sanitizado [R46](h3req1_c03_integrated_run_2026-10-10_r46.txt), SHA-256 `0fefdb22984226124a2847c8f9f4a01923a2396569b01309db8239f30b4f1a00`.

## Predicados integrados

La cadena completa pasó en PG17.11, PostgREST 13, Pages/workerd y Edge Runtime aislados:

| Predicado | Resultado |
|---|---|
| Snapshot/caches e inputs | 126/126; digests R4 fijados |
| Bootstrap H2→H3, setup y fixture | PASS; setup PG17 incluye role `service_role` con `BYPASSRLS` asertado |
| Pages/workerd health y login | PASS; AAL2 y cookies sintéticas |
| Reserva anterior a Auth/suspensión | PASS; estado persistido |
| Rechazo de iniciadores y dispatcher suspendido | PASS; 503/403 y nonce preservado |
| Finalizador in-flight durante suspensión | PASS una vez; una llamada Auth sintética; auditoría y cuota verificadas |
| Resume y SQL recuperado | PASS por conexión nueva |
| Lectura PostgREST de reserva | HTTP 200, una fila; request ID/actor/email/rol/user ID coinciden; entrega COMPLETED, sin reconciliación pendiente |
| Replay Edge | PASS; misma invitación, sin segundo correo Auth; sesión AAL2 y rol admin |
| Assertions SQL finales y smoke | PASS |

El cambio R46 corrigió el fixture, no el producto: `service_role` estaba creado como NOLOGIN sin `BYPASSRLS`, lo que ocultaba la fila al PostgREST sintético pese a SELECT y al registro observado por `postgres`. La configuración ahora refleja el rol administrado de Supabase solo en el PG17 desechable. No se tocaron policies ni servicios remotos.

## Recursos del run

Los datos siguientes provienen de la salida de `record_container` y del registro de cleanup del log; no se leyó `Env`.

| Recurso | ID | Imagen | Estado al limpiar / límite |
|---|---|---|---|
| `h3req1-c03-source-snapshot-20261010-r46` | `7561dc00756f29989f689faf1dbd6c97a3a8ba2c9c4219b0c1867882a73db84f` | Node fijado | completed; 512 MiB / 1 CPU |
| `h3req1-c03-dependency-cache-verify-20261010-r46` | `aa9ddb7ba80a6502b2c2cb49e351ad92258c4ca6d26206c311550b872889814d` | Node fijado | completed; 512 MiB / 1 CPU |
| `h3req1-c03-integrated-runtime-20261010-r46` | `73da42d757a6b9425e602561224b031c455ee06aa9ae76c4f412c5a643849271` | Node fijado | removed after PASS; 4 GiB / 2 CPU |
| `h3req1-c03-integrated-pg17-20261010-r46` | `4834ee55fffc59329632bc5210e77e9a3c6e0c758884e0bb334cf30752b9cea0` | PostgreSQL 17.11 | stopped after PASS; 2 GiB / 2 CPU; PGDATA tmpfs |
| `h3req1-c03-integrated-postgrest-20261010-r46` | `78c1195e080841cc5d309ed4c8238f8e15323382be7bd3a32658ccf2375a942d` | PostgREST 13 fijado | detenido tras PASS; 512 MiB / 1 CPU |
| `h3req1-c03-integrated-edge-active-20261010-r46` | `dfb4e5525b236153b24fad750b21f76e3f3b623bf7f3118ee85ef34dddffd15c` | Edge Runtime v1.74.3 fijado | detenido tras PASS; 1 GiB / 1 CPU |
| `h3req1-c03-integrated-edge-suspended-20261010-r46` | `990fecd61f2a7c157b839a29cd111ff4a8465ea059fb10602b0064a48057fb33` | Edge Runtime v1.74.3 fijado | detenido tras PASS; 1 GiB / 1 CPU |
| Red Edge `h3req1-c03-integrated-edge-20261010-r46` | `e65fc7901925e7f05d70330246f7ce1d75c11d13abdd391be4db39d78e6a3c24` | interna | cero adjuntos al retirar |
| Red data `h3req1-c03-integrated-data-20261010-r46` | `592b62cf5e855d5f48e10c3b1b857a2739c8f20df937c6769e78b28ae2a47300` | interna | cero adjuntos al retirar |

El runner verificó JIT/manifiesto/nonce por etiqueta, y retiró siete contenedores y ambas redes por IDs inmutables. No eliminó volúmenes ni imágenes. Se preservan `h3req1-c03-integrated-source-snapshot-20261010-r46`, `h3req1-c03-integrated-tls-20261010-r46`, caches R4 e imágenes. Tras el run, no queda contenedor ni red R46; `studiamatch-dev` sigue healthy con `studiamatch-h3req1:20261009-v3`, ID `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, montando el candidato. No se accedió al checkout original ni a servicios/credenciales remotos.

## Gate y métricas

G07 completo. Tablero histórico G01–G10: 60% → **70%**, delta +10 puntos porcentuales. Cierre local G01–G09: 6/9 (66.67%) → **7/9 (77.78%)**, delta +11.11 puntos. G08/G09 siguen pendientes; G10 remoto y revisión humana sigue fuera de este cierre local. No se declara `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
