# Hardening de URLs desde `artifacts/urls_interes`

Este proceso convierte listas temporales de URLs de interes en configuracion persistente para `institution_site_profiles`.

## Regla Principal

Los archivos `artifacts/urls_interes/<slug>.txt` son insumos de analisis. Ningun worker, workflow de FG2 ni runtime productivo debe leerlos para decidir que URLs procesar.

## Flujo Operativo

1. Ejecutar el analizador offline sobre el archivo de la institucion:

   ```bash
   python3 scripts/maintenance/analyze_url_interest_artifact.py <slug>
   ```

2. Revisar las familias de rutas y los candidatos generados.
3. Traducir el resultado a una migration SQL versionada que actualice `institution_site_profiles`.
4. Poblar o endurecer estos campos segun corresponda:

   - `seed_urls`
   - `catalog_url_patterns`
   - `allowed_url_patterns`
   - `exclusion_patterns`
   - `discovery_mode`
   - `catalog_link_selector`
   - `site_type`

5. Validar en Free ejecutando FG2 manualmente para esa configuracion.
6. Promover la migration por el flujo DB-as-Code.

## Criterios

- Preferir patrones por forma de URL, no listas exactas de URLs.
- Anclar los regex (`^...$`) y evitar patrones ambiguos antes de persistirlos.
- `allowed_url_patterns` debe describir URLs de programas reales.
- `exclusion_patterns` debe capturar ruido estructural como blogs, carritos, categorias, etiquetas, legales o paginas institucionales.
- Si una URL nueva comparte la misma forma que una URL valida del `.txt`, debe entrar sin modificar codigo.
- Si aparece una URL basura con forma conocida, debe quedar fuera por patron.

## Validacion de No Dependencia Runtime

Antes de cerrar una institucion, confirmar que los workers y workflows no referencian `artifacts/urls_interes`.
