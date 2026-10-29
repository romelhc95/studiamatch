# G09 delta R94 — mutación concurrente con dos actores — 2026-10-11

## Alcance

- Recurso: PostgreSQL 17.11 sintético
  `h3req1-g09-uat-pg17-20261010-r12`, database
  `h3_final_uat_g09_20261010_r12`.
- Los dos IDs probados son miembros fixture del entorno (`admin`, `ready`,
  activos), y ambos tienen fila en `auth.users`; no son cuentas reales.
- Se invocó únicamente `public.admin_update_member` dentro de transacciones
  separadas. Cada conexión fijó `request.jwt.claim.sub` a un actor sintético y
  `request.jwt.claim.aal=aal2`. No hubo acceso a Supabase/Cloudflare/GitHub,
  secretos ni datos operativos.

## Ensayo

Las sesiones PSQL se iniciaron en paralelo. La sesión del actor 1 desactivó al
actor 2 y mantuvo su transacción abierta 0,8 s después de la RPC, reteniendo el
advisory transaction lock. La sesión del actor 2 llamó a la misma RPC para
desactivar al actor 1 y esperó el lock. La primera RPC devolvió
`success=true, role=admin, is_active=false` para el actor 2. Una vez liberado el
lock, la segunda devolvió `success=false, error=User is not an active admin`.
Ambos procesos `docker exec` finalizaron con exit 0 y sin retry.

El estado final intermedio se leyó con consulta SQL: actor 1 activo/admin,
actor 2 inactivo/admin; exactamente un admin activo. Se restauró el actor 2 a
`admin/active` mediante la misma RPC autenticada como actor 1 (exit 0). La
consulta posterior confirmó los dos valores originales (`admin/active/ready`)
y el conteo de admins activos volvió a 2. No se borraron filas ni auditorías;
los eventos de prueba son sintéticos y permanecen en el historial local.

## Evidencia y límites

La salida observada fue:

```text
actor1_deactivate_actor2: t|30000000-0000-0000-0000-000000000002|admin|f|
actor2_deactivate_actor1: f|30000000-0000-0000-0000-000000000001|||User is not an active admin
restore_actor2: t|30000000-0000-0000-0000-000000000002|admin|t|
final_members: actor1 admin/t/ready; actor2 admin/t/ready; active_admin_count=2
```

R94 demuestra la serialización/último-admin guard con dos claims de actores
distintos en transacciones PG17 reales; no equivale a un navegador de dos
sesiones. R93 cubre el camino BFF/browser de dos solicitudes simultáneas del
mismo actor. En conjunto, G09-T06/LOCAL-10 queda completo para el fixture
sintético, sin extrapolar a servicios remotos.

