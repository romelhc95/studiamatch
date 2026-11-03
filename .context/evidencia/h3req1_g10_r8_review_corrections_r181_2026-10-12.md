# H3REQ1 G10 — correcciones y validación del paquete R8 — R181, 2026-10-12

## Candidato y alcance

Checkout `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. Se preservan el checkout original,
los cambios ajenos y R6/R7/R180. No hubo operaciones remotas, PR, commit, push,
merge, deploy, lecturas cloud ni cambios funcionales.

## Revisión independiente inicial R8

La revisión read-only inicial no halló HIGH/CRITICAL ni bloqueos de
código/configuración. Validó entonces 91 paths propuestos, 156 evidencias y 247
archivos únicos, incluidos hashes/tamaños/modos, ausencia de solapamiento,
WIP/diff, diez encabezados de plantilla y enlaces. Sus cuatro correcciones
documentales/tooling fueron:

1. Precisar que se excluyen `.env*` operativos y que `.env.example` sí está
   incluido explícitamente.
2. Atribuir a R7 los seis paths no admitidos y el permiso innecesario de Stage
   2; atribuir el caso de review sobre base no protegida a la pasada semántica
   independiente posterior que motivó R180.
3. Enlazar separadamente los checkers de scope y transición.
4. Emitir el `PASS` del scope checker solo después de completar todas las
   aserciones.

La conciliación posterior encontró un quinto punto: el cuerpo citaba la
atestación cliente sanitizada, pero no la enlazaba ni la incluía en el inventario
del paquete R8. Se agregó como la única nueva ruta propuesta:
`.context/evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md`.
El cuerpo ahora la enlaza de forma relativa. Es evidencia sanitizada; no contiene
documento privado, contrato, precio, PII ni detalle confidencial.

## Validación del scope checker y scanner

La reproducción final se ejecutó después de los cambios R181 de estado/índice en
Docker con imagen local
`studiamatch-h3req1:20261009-v3` (ID
`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`),
red `none`, rootfs read-only, capabilities retiradas, `no-new-privileges`,
256 MiB y 1 CPU. No se montó el checkout completo ni secretos.

- Scope válido, contenedor
  `h3req1-r181-scope-allowlist-final-go-20261012` (ID
  `ec724d1b5398654fd1e7981f7e6caf6790e144b990fbc9516eaf8209a084ab62`), exit 0:
  `scope_allowlist=PASS|proposed=92|regex=72|exact=20|review_fixes=6/6|missing=0`.
- Scope negativo anterior con el mismo checker, contenedor
  `h3req1-r181-scope-allowlist-negative-v2-20261012`, fixture
  `foreign-untracked.ts`, exit 1 y sin línea de `PASS`. El primer fixture
  negativo había usado `README.md`, permitido por Stage 1, por lo que se
  sustituyó antes de aceptar el resultado.
- Credential scanner sobre los 92 paths propuestos del inventario final:
  exit 0, sin hallazgos. Snapshot allowlisted de 92 paths, 2,385,920 bytes,
  SHA-256 `e5206b50b6fbb0d245b92de57061b920158591c5a81417dc489616d15771385f`.
  Contenedor `h3req1-r181-credential-scan-final-go-20261012` (ID
  `071db8909bd8838abfeed7bd22c58c3eb967936fb62105ae95432fd09975efc4`), sin
  red, rootfs read-only, usuario `65534:65534`, 256 MiB y 1 CPU. Esta corrida
  finaliza después de cambiar estado/índice; las corridas preliminares quedan
  preservadas, pero no se usan como evidencia final.

La salida sanitaria y configuración verificable de los contenedores se conserva
en [evidencia de scope y scanner R181](h3req1_g10_scope_scan_r181_2026-10-12.txt).
El primer fixture negativo inválido y sus motivos quedan como historia; no se
cuenta como PASS ni como hallazgo del checker.

## Validaciones del bootstrap conservadas

- Stage 1 exacto, variante sintética Stage 2, PWI y DB Sync pasaron actionlint
  1.7.7 en Docker en R180; los inputs de workflow/patch no cambiaron en R181.
- El transition checker R180 pasó sus 9 casos sintéticos; Stage 1 conserva el
  agregado `security-audit`, y Stage 2 permanece separado e inactivo hasta la
  precondición remota de instalar PWI.
- ShellCheck del bloque de clasificación de base/evento pasó. La extracción
  completa sin expandir expresiones GitHub falló por el formato del harness y no
  se cuenta como PASS.
- R180 escaneó 91 paths; ese resultado es histórico. Esta nota acredita el scan
  renovado de los 92 paths actuales.

## Revisión independiente y límites

La revisión independiente completa de R8/R181 devolvió **PASS**, sin
HIGH/CRITICAL ni hallazgos bloqueantes. Revisó el manifest SHA-256
`951162c4623d617e3c87b68cb84efbf95c866b1488d69a1a182979248762e678` y confirmó
250 paths, hashes/modos/tamaños, WIP, diez encabezados, links, los cinco fixes,
Stage 1 y Stage 2. El cuerpo revisado tenía SHA-256
`ec5a15cee25b8676686dde22a2b7a584b1ce52f10f4e6871c16f0e5b1067f694`.

Después del dictamen se conciliaron el encabezado vigente e índice para registrar
el resultado. Por eso se regeneraron el snapshot y el scanner sobre el contenido
final (92/92, cero hallazgos) antes de fijar el manifest/cuerpo R8 definitivo.
El dictamen independiente sobre el código, configuración y contenido propuesto
sigue aplicando; la integridad final de los pins se valida por separado. No se
modificó el workflow activo en R181; Stage 2 sigue como patch separado. G10 remoto —lectura de protecciones,
instalación/enforcement, PR, workflow run, revisión humana y despliegue— no se
ejecutó ni se declara efectivo.

Una comprobación independiente read-only de la versión R181 del paquete,
completada antes de la reconciliación R182, devolvió **PASS** sin hallazgos:
confirmó 92 paths propuestos, 158 evidencias y 250 archivos únicos, cada
hash/tamaño/modo, solapamiento cero, WIP `61/894/20388/0`, digests de estado/diff,
secciones de plantilla, enlaces relativos, test protegido, atestación y log del
scanner. No ejecutó suites ni operaciones remotas. El log R182 añade un único
path untracked; su WIP y status digest se recalculan en el manifiesto final.

## Delta de documentación R182 y renovación del scanner

Al cerrar R181 se detectaron encabezados inferiores que aún llamaban “vigentes”
a los cortes R179, R178, R144 y al corte del 2026-10-09. R182 los marca como
históricos/supersedidos sin modificar sus resultados ni reorganizar Obsidian.
El estado e índice forman parte del scope propuesto, por lo que se renovaron
ambos controles sobre el candidato actualizado: scope checker 92/92 permitido
(72 regex, 20 exactos, seis fixes revisados y cero faltantes), exit 0; scanner
de credenciales 92/92 sin hallazgos, exit 0. La salida y los IDs de contenedor
están en el [log de validación R182](h3req1_g10_scope_scan_r182_2026-10-12.txt).

R181 se conserva como evidencia histórica anterior al ajuste de encabezados; R182
es la ejecución vigente para esos dos paths modificados. La imagen local
`studiamatch-h3req1:20261009-v3` y `studiamatch-dev` no se cambiaron. Los
contenedores R182 terminaron y permanecen preservados. La revisión independiente
completa del contenido R8/R181 no halló bloqueantes; los pins del paquete se
regeneran para incluir esta nota y el log R182.
