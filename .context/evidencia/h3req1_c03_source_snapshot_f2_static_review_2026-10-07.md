# Revisión estática F2 — lectura metadata post-NO-GO F1

Fecha: 2026-10-07. Scope exclusivo: evaluar la propuesta F2 de lectura read-only; no ejecutar
Docker, JIT, comandos de inspección, servicios remotos ni cambiar recursos.

## Artefactos considerados

| Artefacto | SHA-256 reportado/verificado localmente |
|---|---|
| JIT F2 `.context/operaciones/manifiesto_jit_h3_close03_source_snapshot_f1_metadata_read_2026-10-07_f2.md` | `79f68000f20ddcf31724fdf3c7397cf828225c5181bc62dc3a7902108e61ce1f` |
| Atestación de aprobación F1 | `9f0027bb3b6ec85347349f3dace69952719d2931f10de5b47f76e753828e9626` |
| Reporte factual F1 | `c28338c811b305428126ea7bea9fa5d4f9f9e3cfd09e8a26aeb370f032a41913` |

Branch/HEAD del candidato permanecen `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Remediaciones locales y comprobaciones

- F1 aprobado/consumido fue reconciliado con una atestación separada que conserva la decisión
  humana; el JIT histórico F1 se deja intacto. F2 fija hash y marcador de esa atestación.
- El reporte futuro no guardará ID/nombre/nonce ni estado/exit/OOM ni metadata raw; reportará
  solo PASS/NO-GO, nombres de controles discrepantes y marcadores de descarte/preservación.
- Se añadió conteo exacto de 25 campos, `umask 077`, validación/canonicalización de directorios
  de entrada y manejo de salida que escribe NO-GO sanitizado ante error tras crear el reporte.
- Bash syntax del bloque de comando F2 y `git diff --check`: PASS. No se ejecutó Docker.
- Revisión estática independiente posterior a esas correcciones encontró **1 HIGH, 1 MEDIUM,
  0 LOW adicional** en el alcance revisado; el formato/evidencia y los LOW de permisos/rutas
  de la revisión inicial ya no aparecieron en el resultado final.

## Hallazgos bloqueantes

1. **HIGH — identidad del daemon no demostrada.** F2 exige endpoint `unix:///...`, y el socket
   coincide en `stat`/`realpath`, pero eso solo prueba un socket Unix local. Ese socket podría
   ser un proxy local que reenvía a un daemon remoto; el `inspect` consultaría entonces un
   recurso fuera del alcance autorizado. No hay path/peer/proceso confiable fijado. No se
   acepta este riesgo: el alcance explícitamente excluye remotos.
2. **MEDIUM — procesamiento transitorio completo de inspect.** Docker Engine entrega el
   objeto entero al CLI antes de aplicar `--format`. F2 lo documenta como waiver propuesto;
   los valores no seleccionados pueden transitar por memoria, aunque el script no los emite ni
   persiste. El waiver F2 aún no está aprobado.

La aprobación previa de F1 y su waiver no autorizan F2. El JIT F2 permanece **propuesto, NO
aprobado, NO ejecutado**; por el HIGH el resultado es **NO-GO**. No se hizo otra llamada Docker
tras el NO-GO F1.

## Siguiente gate

Determinar y fijar una identidad verificable del Docker daemon directo y local, compatible con
el entorno real. No inferir una ruta/daemon ni aceptar un socket arbitrario. Si no se puede
establecer sin ampliar el alcance, mantener F2 NO-GO. Después: actualizar F2, revalidar pins y
pedir auditoría/aprobación humana independiente para ese JIT exacto. Cualquier autorización
debe aceptar expresamente el residual MEDIUM de procesamiento de inspect y no puede cubrir
un daemon remoto.
