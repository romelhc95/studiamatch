# Inventario selectivo de recursos R42

Run: `H3-CLOSE-03-INTEGRATED-2026-10-10-R42`  
Manifest SHA-256: `45c77516393942b00709f50ff7a02578a7d33b7f4f5ef798be17f209918ff33d`  
Run label: `1765754-1791657454678255730-14017-22498`  
Log conservado: `h3req1_c03_integrated_run_2026-10-10_r42.txt`, SHA-256
`cec6e2cd7224289e427591560a67c5948e37101ec989e02d5496ae1e665981a4`.

## Resultado y estado observado

R42 pasó snapshot, cache verifier, PG17 17.11, bootstrap H2→H3, setup de cuotas/gateway,
fixture editorial/in-flight, readiness PostgREST, login Pages/workerd AAL2, reserva, suspensión,
dispatcher rechazado con 403/42501, finalización Auth in-flight una vez, safe-resume y
assertions SQL recuperadas. Falló en `edge-first-pages-last-recovery-smoke` con exit 1,
`RECOVERY_EDGE_REPLAY_STATUS`, status 409, código allowlisted
`INVITE_EARLY_RECONCILIATION_REQUIRED`. El runner detuvo cinco servicios activos y preservó
recursos/log. No se atribuye aún el 409 a una causa concreta del producto; falta clasificar
qué condición persistida de la invitación produjo `reconciliation_required`.

## Recursos H3 exactos

| Recurso | ID | Imagen | Estado/exit | Límite memoria / CPU | Función |
|---|---|---|---|---|---|
| `h3req1-c03-integrated-edge-suspended-20261010-r42` | `cce7888e8f3e2eb30b7aa2381bf211e57d6c7a07047b5fce535cd1eda53ee0ce` | Edge Runtime v1.74.3 pinned | exited / 15 | 1 GiB / 1 CPU | Edge suspendido |
| `h3req1-c03-integrated-edge-active-20261010-r42` | `40046264f194564ebaddd117bec606138c2738e97a4c8a0b58aa8620be3f62ba` | Edge Runtime v1.74.3 pinned | exited / 15 | 1 GiB / 1 CPU | Edge activo |
| `h3req1-c03-integrated-postgrest-20261010-r42` | `9b2a8d02cedd47f5f1f2c883011eb954a306a9cc51a0a3d56a11f60ec37575a2` | PostgREST pinned | exited / 255 | 512 MiB / 1 CPU | API local PostgreSQL |
| `h3req1-c03-integrated-pg17-20261010-r42` | `39770dee1c05318bade36cc1c8ee7cfaa1b219f7404b7c82ffe411e0d7d86f8e` | PostgreSQL 17.11 pinned | exited / 0 | 2 GiB / 2 CPU | PG17 de prueba; PGDATA tmpfs |
| `h3req1-c03-integrated-runtime-20261010-r42` | `904173bda72c00906ecb423c74ffca6bf139273372c28fafce7f3cc8a3e1259a` | Node pinned | exited / 143 | 4 GiB / 2 CPU | Pages/workerd driver y mocks sintéticos |
| `h3req1-c03-dependency-cache-verify-20261010-r42` | `bd3fa3794f30984cdb327a850efb13038862991544e5b8fc6b37566695f61075` | Node pinned | exited / 0 | 512 MiB / 1 CPU | Verificador read-only de caches R4 |
| `h3req1-c03-source-snapshot-20261010-r42` | `39bb1eed2485d4b32180d80babf94a30fdc29b198fe32d5bfa16844d192de845` | Node pinned | exited / 0 | 512 MiB / 1 CPU | Snapshot allowlisted verificado |

Todos los contenedores llevan el JIT, manifest y run labels R42 exactos. Las redes
`h3req1-c03-integrated-edge-20261010-r42` (`7b180e300e29443ca9fc0a0ca7851817adb839dae70c510f33514f90df39bee4`)
y `h3req1-c03-integrated-data-20261010-r42` (`c4d9c2fea52645fa5a01caad08618b52739a288278c60cd2818b0c4d5f0f7fef`) son internas, vacías y llevan los mismos labels.

Se conservan sin leer sus contenidos los volúmenes R42 `h3req1-c03-integrated-source-snapshot-20261010-r42`
(copia verificada del candidato) y `h3req1-c03-integrated-tls-20261010-r42` (fixtures TLS sintéticos).
No se retiran caches R4, imágenes, volúmenes ni `studiamatch-dev`. El PGDATA temporal dejó de
estar montado al parar el contenedor y no se recuperan datos de esa base.

## Retirada selectiva

Se retiraron exclusivamente los siete contenedores R42 arriba enumerados y las dos redes internas
vacías, comprobando estado `exited`, labels de JIT/manifest/run y ausencia de attachments. La
retirada fue `docker rm` por IDs exactos, sin `-v`, más `docker network rm` por IDs exactos.
Se preservan los dos volúmenes descritos, todo el checkout/evidencia, imágenes y recursos ajenos.
