# Presentación web compartida

## Propósito y límites

Agrupa tres responsabilidades transversales distintas: primitivas visuales reutilizadas por público/Admin, un renderer de ficha de curso compartido por detalle y vista previa, y el helper de composición de clases. No posee sesión, autorización, consultas Supabase ni persistencia. La cola Admin, la política de contraseñas y el transporte Supabase tienen fichas propias.

## Primitivas UI

| Fuente | Responsabilidad y consumidores comprobados |
|---|---|
| `web/src/components/ui/badge.tsx` | Badge y variantes; comparación pública, renderer de curso y cola Admin. |
| `web/src/components/ui/button.tsx` | Botones y variantes Base UI; Home, comparación, onboarding, edición, usuarios, cola Admin y `MfaRequiredCard`. |
| `web/src/components/ui/card.tsx` | Contenedor visual; páginas públicas, detalle de curso y superficies Admin. |
| `web/src/components/ui/input.tsx` | Input HTML con estilos compartidos; Home, edición, login/usuarios, cola y componentes de contraseña/MFA. |
| `web/src/components/ui/label.tsx` | Label Radix; edición, usuarios, cola y MFA. |
| `web/src/components/ui/select.tsx` | Select Radix; filtros de edición, miembros y cola. |

Los módulos aceptan props/children y `className`; no deciden reglas de negocio ni son dueños de estado persistente. Al cambiar una prop, variante, interacción, foco o estilo se revisan los imports de ambos dominios, el mapa de consumidores y los contratos de accesibilidad del caller.

## Renderizado de curso

`web/src/components/courses/CoursePublicRenderer.tsx` define `PublicCourse` y recibe el curso, pestaña activa, callbacks, lista de comparación, cursos relacionados y opciones de preview. El detalle público lo usa para leer la ficha. `web/src/components/admin/CourseLivePreview.tsx` lo reutiliza con el draft del editor y `activeField` para resaltar el campo modificado; el renderer no guarda ni publica ese draft. También importa `cleanSlug` desde `web/src/lib/supabase.ts`, por lo que este módulo compartido depende de un módulo que pertenece al cliente de datos público. Al cargarlo se evalúan las comprobaciones de entorno y la inicialización del cliente Supabase; ese import no inicia por sí mismo una petición. La ruta exige conservar la configuración pública en el build/runtime que incluya el renderer. Extraer el helper o cambiar esa inicialización sería un cambio funcional fuera de esta reorganización documental.

El componente presenta información y requisitos, normaliza texto estructurado con fallback legible, formatea precio y solo habilita enlaces con esquema HTTP/HTTPS. Si cambia un campo, su significado o forma, revisar el contrato fuente, ambos consumidores, el editor/preview, el catálogo exportado y las pruebas que afirman la reutilización. La exportación estática puede requerir reconstruir para reflejar cambios públicos; el cache/CDN remoto no se verificó.

## Utilidad de clases

`web/src/lib/utils.ts` exporta `cn(...inputs)`, que combina condiciones mediante `clsx` y resuelve conflictos Tailwind con `tailwind-merge`. Lo importan los primitives, Header, Home, comparación y renderer de curso. Es una transformación síncrona en memoria: no recibe datos de producto ni tiene efectos externos. Cambios pueden afectar muchas rutas aun cuando no alteren un contrato de negocio.

## Datos, fallos, dependencias y pruebas

- Los primitives reciben estado/valores del caller; el renderer recibe el objeto de curso o un draft; `cn` recibe class values. El renderer no realiza llamadas de red ni escribe DB; su import de `cleanSlug` sí carga el módulo del cliente Supabase y sus validaciones/inicialización, sin que ese import por sí solo envíe una petición.
- El renderer maneja texto JSON malformado como texto normal y convierte URL inválida/no HTTP(S) en contenido no enlazable. Los errores de carga pertenecen al caller.
- UI se construye con Base UI, Radix, `class-variance-authority`, `clsx`, `tailwind-merge` y Tailwind; versiones/rangos se mantienen en los manifests y locks de `web/`.
- `tests/test_h3_admin_queue_ux_contract.py` afirma que detalle público y `CourseLivePreview` usan el mismo renderer. La matriz de relaciones documenta que no localizó tests dedicados por archivo para los primitives ni para `cn`; las suites de catálogo/Admin ejercitan consumidores de forma indirecta. Ese vínculo no demuestra ejecución ni cobertura exhaustiva.
- El corte funcional R178 preserva sus casos y límites. Esta documentación no ejecutó suites nuevas ni atribuye PASS a cada primitive. Al cambiar interacción compartida, renovar lint/typecheck/build y los casos de consumidor afectados; si el cambio modifica layout/teclado/foco, revisar snapshots/UAT de las superficies implicadas.

## Cómo modificarlo con seguridad

1. Identificar el export que se cambia y seguir sus imports directos/indirectos en la tabla fuente→consumidor del [registro canónico](../trazabilidad/registro_fuentes_componentes.md#presentacion-web-compartida).
2. Para primitives y `cn`, revisar usos en `web/src/app/`, `web/src/components/AdminCourseQueue.tsx`, `web/src/components/admin/`, `CourseLivePreview` y `CoursePublicRenderer`.
3. Para el renderer, revisar `CourseDetailClient.tsx`, `CourseLivePreview.tsx`, `PublicCourse` y el campo efectivo correspondiente en [Database](../database.md).
4. Ajustar la prueba de contrato/superficie que corresponde, sin confundir una assertion estática con ejecución del build o del browser.
5. Ejecutar en Docker lint/typecheck/build según el impacto; una dependencia UI requiere lockfile y scanner por impacto. No se necesitan permisos DB para cambios puramente presentacionales.

## Navegación relacionada

[Frontend](../frontend.md#componentes-principales) · [Portal Admin](admin_portal.md#componentes-compartidos) · [Base de datos](../database.md) · [Pruebas](../pruebas.md) · [Tecnologías](../tecnologias.md) · [Índice](../indice.md)

## Fuentes y relaciones

Los seis primitives, `CoursePublicRenderer` y `cn` tienen grupos separados en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md#presentacion-web-compartida). La matriz R10 conserva la clasificación anterior; la corrección de ownership, los consumidores confirmados en ambos checkouts y los límites de búsqueda constan en el [addendum de reclasificación R11](../evidencia/h3req1_reclasificacion_componentes_web_2026-10-13_r11.md).

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [Frontend público y UAT](../catalogos_historicos/frontend_publico_uat.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
