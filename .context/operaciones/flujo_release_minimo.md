# Flujo Release Minimo

> Esta nota no crea alcance ni autoriza ejecucion por si sola. La autoridad viva
> esta en `estado_del_proyecto.md` y el plan activo esta en
> `plan_vinculante_nuevo_pedido_2026_08_25.md`.

## Flujo Vigente

```text
feat/* o docs/* desde desarrollo
-> PR protegido a desarrollo
-> PR protegido desarrollo a certificacion
-> PR protegido certificacion a main
```

## Reglas

- `security-audit` permanece como required check.
- Cada PR requiere review humano.
- `web/**`, `db/**`, `supabase/**`, `scripts/core/**`, `scripts/shared/**`,
  `scripts/maintenance/**`, `config/**`, dependencias y Docker permanecen
  protegidos salvo aprobacion explicita posterior.
- `DB Sync to Production` es manual-only y no corre por push.
- Cloudflare Pages automatico se acepta solo como efecto normal de merge a `main`, no
  como autorizacion para mutar producto o DB.
- El nuevo pedido documental activa la secuencia Intake -> H2 -> H3 -> H1 -> H4 -> H5; los Work Packages/digests historicos quedan superseded.
- El soporte temporal raiz fue eliminado definitivamente y no debe recrearse.

## Stop Conditions

- Secretos o credenciales en archivos, logs o diffs.
- Ruta protegida distinta del baseline sin autorizacion separada.
- DB, deploy, schedule, writer o accion remota solicitada implicitamente.
- Fallo de `security-audit` o validacion local sin remediacion posible.
