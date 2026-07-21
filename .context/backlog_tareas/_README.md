# Backlog Por Requerimiento

## Regla
No crear tareas directamente en `.context/backlog_tareas/`.

Cada requerimiento debe tener su propio directorio:

```text
.context/backlog_tareas/<requerimiento_slug>/
├── _index.md
├── tarea_001_<slug>.md
└── tarea_002_<slug>.md
```

## Convencion
- `<requerimiento_slug>` debe ser estable y descriptivo, por ejemplo `req_hito_2_catalogo`.
- Si no se informa `--requerimiento`, `.context/crear_tarea.py` usa la estimacion normalizada (`est_001`) como contenedor.
- Cada directorio tiene un `_index.md` generado por el script para contexto y reglas locales.
- Las tareas one-shot o descartadas no deben quedarse aqui; mover a `desestimado/` si no son recurrentes.
