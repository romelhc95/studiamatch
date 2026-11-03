# Limpieza selectiva de redes integradas H3

- Evidencia previa/inventario: [network inventory](h3req1_c03_integrated_network_inventory_precleanup_2026-10-10.txt), SHA-256 `f24a56db5351911a8bfe971bc72e29a6e091c01849cfee2acf9072ac0f1b2ac3`.
- R16 había fallado antes de iniciar servicios porque el pool IPv4 local estaba lleno.
- El primer script de retirada revalidó y eliminó nueve redes `data` de IDs exactos, luego se detuvo ante una línea vacía del inventario (`cleanup-stop=inventory_shape_rejected`). Exit 1 del wrapper; no alcanzó redes `edge` ni tocó otros tipos de recursos.
- Se corrigió el lector para omitir filas vacías/ABSENT y seleccionar únicamente `edge`. La segunda operación revalidó ID, nombre allowlisted, etiqueta de JIT/manifiesto/nonce, `Internal=true` y cero adjuntos; eliminó los diez IDs `edge` exactos.
- Total retirado: 19 redes internas vacías R5, R6, R8–R11, R13–R16, incluyendo solo las redes existentes de cada corrida. No se encontraron redes H3 etiquetadas restantes en la comprobación posterior.
- Recursos preservados: todos los contenedores (incluido `studiamatch-dev`), 27 volúmenes H3, todas las imágenes, logs y source snapshots. `studiamatch-dev` siguió `healthy`. No hubo prune, engine/config change ni acceso remoto.

Esto recupera capacidad de red para la siguiente corrida; no completa ni avanza G07.
