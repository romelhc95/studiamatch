# Flujo Release Minimo

> Esta nota no crea alcance ni autoriza ejecucion por si sola. La autoridad viva
> esta en `estado_del_proyecto.md`; `../../REDEFINICION.md` queda como soporte
> temporal sin autoridad independiente hasta el GO para nuevos pedidos.

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
- H2-H5 requieren un nuevo pedido explicito; los Work Packages/digests
  historicos quedan superseded.
- `REDEFINICION.md` se conserva temporalmente hasta el GO del cliente y luego se archiva o elimina por PR normal.

## Stop Conditions

- Secretos o credenciales en archivos, logs o diffs.
- Ruta protegida distinta del baseline sin autorizacion separada.
- DB, deploy, schedule, writer o accion remota solicitada implicitamente.
- Fallo de `security-audit` o validacion local sin remediacion posible.
