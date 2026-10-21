# Revisión estática F2d r2 — identidad local del daemon y metadata de F1

Fecha: 2026-10-08. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. Esta revisión
renueva pins tras el cambio del helper y el PASS sintético en Docker r4; no autoriza ni
ejecuta el diagnóstico contra F1.

## Resultado y revisión de alcance

El runner requiere rama/HEAD exactos, ausencia de overrides Docker, inputs hash-bound y
reporte nuevo. Lee el contexto Docker seleccionado y solo continúa con endpoint Unix local
canónico. El helper usa `SO_PEERCRED` para conocer el peer del kernel y revisa exclusivamente
`/proc/<pid>/stat`, `comm`, `exe`, `status` y `ns/pid`; valida estabilidad del proceso y del
socket, PID namespace local, ejecutable `dockerd` root-owned y no escribible por grupo/otros.
Si falla identidad, no exporta `DOCKER_HOST` y no hace llamadas Docker API.

Si pasa, el runner se limita a una lectura local del ID inmutable de la imagen fijada y una
inspección del ID F1 exacto. La proyección compara 27 controles permitidos y reporta nombres
de discrepancia, no valores. Descarta stderr/respuesta cruda y no usa logs, exec, pull,
create/start/stop/rm ni limpia recursos. Tiene timeout total de 120 s, límites por lectura,
salidas acotadas y cero retries. Los resultados F2b/F2c y el recurso F1 se preservan.

## Validación dinámica disponible y límites

El paquete r4 pasó el chequeo de hashes 13/13 y pytest 20/20; ese comando incluía el helper
F2d y los tests sintéticos del proyector. El proyector y scope guard también pasaron sus
regresiones shell. La prueba separada del scanner falló y su fixture se diagnosticó en r5;
no cambia el resultado PASS del conjunto pytest ni valida el daemon real. Las pruebas usan
fixtures y no conectan al socket Docker.

El manifiesto F2d previo coincidía en 16/17 porque pinneaba una versión anterior del helper.
Se renovó únicamente ese pin; `sha256sum --check` ahora pasó 17/17. No se ejecutó `bash -n`
ni ShellCheck/actionlint en este ciclo. El runner no cambió respecto a la revisión estática
anterior; esta nota no atribuye PASS runtime al runner ni al daemon.

## Reconciliación con AGENTS.md

AGENTS exige Docker para comandos de desarrollo y pruebas del producto, y prohíbe esos
comandos en el host Windows. Los fixtures del helper ya se probaron en Docker r4. La
invocación F2d contra el daemon, en cambio, es una lectura diagnóstica del sistema Linux:
para probar el peer real debe abrir el socket Unix local y leer el proceso correspondiente
en el mismo namespace PID. Ejecutar el auxiliar dentro de un contenedor sin socket no
identifica al daemon; montarle socket y `/proc` del host alteraría la exposición y el
alcance. Por eso el JIT propone exclusivamente `/usr/bin/python3` en el host Linux, antes de
cualquier Docker API. No instala dependencias ni ejecuta tests de producto en host. Se
requiere que el usuario apruebe expresamente este contexto host; sin esa aprobación el
runner no se inicia y no se consulta Docker API.

## Pins vigentes

| Artefacto | SHA-256 |
|---|---|
| JIT F2d r2 | `deb429e38070174b7f179ed2c178bf4c5598ef04c0de4b92ba2f87d624b54078` |
| Runner F2d | `23f860e5582f1fefd96b2ccc4cf1b70e782e0d1a70ab72b630115fdf36c7964c` |
| Sidecar F2d | `5dab2330f306941d3d058ee88c3399501db06045c8573257f6e9829c122cbc27` |
| Manifiesto de inputs F2d, 17/17 | `18101dd492dd894d5c5692c204f1a47d3727fb609f75b83ffdbc854bcf0f657a` |
| Helper `SO_PEERCRED` | `c0b3820d920015325b2d91ed8e50215f3a1ba967d79a1d3abda62c702b460ac0` |
| Proyección Docker | `f75222f388b7a0e2fa3a87c6e051fc6473f027e1edadd663530f401d627757aa` |

## Decisión y pendientes

Revisión estática **PASS con límites**: el alcance está restringido al peer local y al ID F1
fijado. El JIT no puede ejecutarse hasta recibir aprobación exacta de su SHA, autorización
del helper Python en host Linux y aceptación expresa de ambos residuales MEDIUM del JIT:
procesamiento transitorio del objeto inspect completo por Docker CLI y bypass procedimental
por el mismo usuario local. No se conoce aún qué control rechazó F1. No se cierra G04, G03
ni ningún gate adicional.
