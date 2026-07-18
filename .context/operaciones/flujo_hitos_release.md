# Flujo operativo de hitos y releases

## Objetivo
Permitir desarrollo continuo por hitos sin desplegar a produccion cambios no aprobados para la fecha de entrega vigente.

## Ramas

| Rama | Proposito | Regla |
|---|---|---|
| `feat/hito-N-*` | Implementacion del hito o subtarea | Nace desde `desarrollo` y entra por PR. |
| `desarrollo` | Integracion continua de trabajo activo | Puede contener hitos futuros. No se promueve completo si hay alcance no liberable. |
| `release/hito-N` | Alcance congelado para QA y entrega | Nace desde el commit exacto aprobado para el hito. |
| `fix/hito-N-*` | Correcciones del release congelado | Nace desde `release/hito-N`; luego se propaga a `desarrollo`. |
| `certificacion` | QA del release aprobado | Recibe solo `release/hito-N`, no todo `desarrollo` si contiene hitos futuros. |
| `main` | Produccion | Recibe solo releases aprobados explicitamente. |

## Flujo normal

```text
1. feat/hito-N-* -> PR -> desarrollo
2. validar CAs en desarrollo
3. crear release/hito-N desde el commit aprobado
4. release/hito-N -> certificacion
5. validar QA, seguridad y datos del hito exacto
6. release/hito-N -> main con aprobacion explicita
```

## Desarrollo paralelo de hitos

```text
desarrollo
  |- feat/hito-1-* -> PR -> desarrollo
  |                    `- release/hito-1 -> certificacion -> main
  |
  `- feat/hito-2-* -> PR -> desarrollo
                       `- no entra a main hasta su propio release
```

## Correcciones despues del congelamiento
Si QA o el cliente reportan un faltante en un hito ya congelado:

```text
release/hito-N
  -> fix/hito-N-ajuste
  -> release/hito-N
  -> certificacion
  -> main
```

Luego propagar el fix:

```text
release/hito-N -> desarrollo
```

Se puede usar merge-forward o cherry-pick, segun minimice el riesgo de arrastrar cambios no relacionados.

## Regla de alcance
- `desarrollo` no equivale a entregable completo.
- El entregable se define por `release/hito-N`.
- Ningun cambio de `HITO N+1` entra a `main` junto con `HITO N` salvo aprobacion explicita del usuario.
- Si un fix del hito toca archivos modificados por hitos futuros, se resuelve primero en `release/hito-N` con el cambio minimo necesario.

## Validacion de criterios de aceptacion
Antes de considerar listo un hito:

- Los CAs del hito estan mapeados contra tareas y evidencias.
- El hito fue validado en `desarrollo` durante implementacion.
- El alcance congelado fue validado desde `release/hito-N`.
- `security-audit` pasa en PR.
- Las validaciones tecnicas aplicables fueron ejecutadas en el contenedor `studiamatch-dev`.
- Si toca frontend: lint, typecheck y revision responsive.
- Si toca pipeline Python: `py_compile` y prueba controlada segun alcance.
- Si toca Supabase: migracion versionada, RLS/grants revisados y verificacion de paridad/configuracion.

## Base de datos
El flujo de datos mantiene la politica DB-as-Code:

- Catalogos y configuracion versionable viajan en migrations: `institutions`, `institution_site_profiles`, `categories`, `category_rules`, `market_salaries`, RPCs, triggers, RLS y grants.
- Tablas operativas por ambiente no se promueven como flujo normal: `staging_raw`, `cleansed_programs`, `enriched_programs`, `courses`.
- Si Pro tiene la version mas actual de configuracion/schema, primero se audita el drift Pro -> Free y luego se documentan/aplican ajustes controlados en Free.
- Si se requiere copiar datos operativos Pro -> Free para pruebas, se trata como snapshot/backfill excepcional con aprobacion explicita.

## Riesgo actual de ambientes
Actualmente `desarrollo` y `certificacion` usan Supabase Free. Esto permite operar rapido, pero no aisla totalmente QA si otro hito modifica schema o datos en la misma base.

Opciones de mitigacion:

- Congelar cambios DB no liberables mientras se certifica `release/hito-N`.
- Usar un proyecto/branch Supabase separado para certificacion por release critico.
- Restaurar un snapshot controlado antes de QA, solo si el alcance lo justifica.

## Checklist de corte de release
- [ ] CAs del hito cumplidos en `desarrollo`.
- [ ] Commit exacto de corte identificado.
- [ ] Rama `release/hito-N` creada desde ese commit.
- [ ] No hay cambios de hitos futuros dentro del release.
- [ ] Migrations requeridas estan versionadas.
- [ ] Validaciones tecnicas ejecutadas en contenedor.
- [ ] `security-audit` aprobado.
- [ ] Evidencias de QA registradas.
- [ ] Aprobacion explicita para promover a `certificacion`.
- [ ] Aprobacion explicita para promover a `main`.

## Checklist de fix sobre release
- [ ] El defecto pertenece al hito congelado.
- [ ] La rama `fix/hito-N-*` nace desde `release/hito-N`.
- [ ] El cambio es minimo y no arrastra trabajo futuro.
- [ ] Se valida nuevamente el CA afectado.
- [ ] El fix se integra a `release/hito-N`.
- [ ] El fix se propaga a `desarrollo`.
