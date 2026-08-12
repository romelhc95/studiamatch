# F10.10 M3 - Evidencia DDL Free V2

Atestacion sanitizada manual: registra la decision humana y el resultado
observado, pero no contiene un recibo remoto firmado ni concede capacidad.

## Resultado

```text
decision = STOP_BROAD_PUBLIC_DATABASE_PRIVILEGES
gate = APPROVE_F10_10_M3_READER_DDL_FREE_V2
migration = fase10_10_m3_free_reader_free_ddl_v2
apply_migration_calls = 1
retry_calls = 0
execute_sql_calls = 0
transaction_result = FAILED_ROLLBACK
reader_created = NO
q0_consumed = NO
read_consumed = NO
teardown_consumed = NO
```

La unica llamada autorizada a `apply_migration` alcanzo las precondiciones del
package y termino con SQLSTATE `P0001`: el target conserva privilegios de base de
datos efectivos para `PUBLIC` que el contrato cerrado exige endurecer por una
remediacion separada. La excepcion ocurrio antes de `CREATE ROLE`; la transaccion
de la migracion fallo y fue revertida por el envelope de `apply_migration`.

No se hizo retry, cambio de migration name, fallback a `execute_sql`, lectura
remota adicional, Q0, teardown, DML, Pro, Certification ni M4+.

## Baseline Congelado

```text
protected_merge = d6f2570816b6a69bf5e5aad5e37a6dd004e0e0d2
protected_tree = a54b57e361be3fbed86ccee820128a1d71303498
candidate = c04c7c951f74e07f1813704fb0852987fd3e40c5
candidate_parent = bc268f119e04791bc17439aaa096e9e06c8b5e8b
pr = 364
approval = PASS
applicable_checks = PASS
```

## Bindings Verificados Antes De La Llamada

```text
package = sha256:d68d44c6ae61bac120f460955f86547082c0e42b70868a35a330fda8fb7883aa
query_set = sha256:d3bc8fddf7d0d8b39497e4f184c7669bec3cbc4537dde7aeb3757d4afe53957a
applied_query = sha256:a13e0e814185f756d612d8b092561a5baa71442a2cff2e83db081eb32ddd2f3f
compensation = sha256:609a5b22202021de44ff1fa484ddb1a35fbb7bb15f495bc9afe304542d288fe0
target_binding = sha256:68fa6d9566799eb19c99b2415fabad472a8a3a4e51eefb54510c93afbfe91715
provisioner_fingerprint = sha256:e8bb3d66f6efdfb2699307759b8729d9b586bd42856c3600e43d93e78bcd9381
private_artifacts = REGULAR_0600_LINK_COUNT_1_NOT_SYMLINK
password_present = NO
window = VALID_AT_CALL
```

## Ledger

```text
APPROVE_F10_10_M3_READER_PREFLIGHT_FREE = CONSUMED_ONCE_PASS
APPROVE_F10_10_M3_READER_DDL_FREE = CONSUMED_ONCE_FAILED_ROLLBACK_SUPERSEDED
APPROVE_F10_10_M3_READER_DDL_FREE_V2 = CONSUMED_ONCE_FAILED_ROLLBACK
APPROVE_F10_10_M3_READER_Q0_FREE = NOT_CONSUMED
APPROVE_M3_FREE_READONLY = NOT_CONSUMED
APPROVE_F10_10_M3_READER_TEARDOWN_FREE = NOT_CONSUMED
```

La identidad v2 no es reutilizable. El siguiente paso requiere diagnostico y
remediacion separados para los privilegios `PUBLIC`, con nueva identidad,
payload, binding y aprobacion humana; no existe continuidad automatica.
