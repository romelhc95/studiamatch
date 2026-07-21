# Reglas para Antigravity (aplican en cada consulta)

## Contexto obligatorio
Antes de ejecutar cualquier tarea de codigo, la IA DEBE leer estos archivos en orden:
1. `.context/00_INDICE.md`
2. `.context/prompts/system_prompt_base.md`
3. El archivo de arquitectura relevante (DB, Pipeline, Frontend)

## Restricciones
- NUNCA modificar archivos de arquitectura en `.context/` sin aprobacion explicita
- NUNCA exponer credenciales — leer de `.env.local` o `.env.gitprod`
- SOLO ejecutar tareas de una fase con aprobacion explicita: "Ejecuta las tareas pendientes de la Fase XX"
- USAR el contenedor Docker `studiamatch-dev` para todo — no ejecutar en el host
- TODO cambio debe registrarse en `.context/changelog/`
- Las tareas del backlog SIEMPRE van en `.context/backlog_tareas/<requerimiento>/`, nunca planas en la raiz

## Flujo estandar
1. Llega requerimiento → leer `.context/` completo
2. Generar estimacion en `.context/estimaciones/est_XXX.md`
3. Esperar aprobacion
4. Crear tarea: `python .context/crear_tarea.py --est EST-XXX --requerimiento req_XXX --fase NN --titulo "..."`
5. Ejecutar
6. Actualizar changelog
