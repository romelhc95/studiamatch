# H3REQ1 — aceptación funcional integral local

Fecha: 2026-10-10, America/Lima. Estado: **criterios solicitados; ejecución y resultados pendientes de conciliación**.

Esta nota incorpora el pedido humano de probar el funcionamiento de la aplicación con datos sintéticos antes de cerrar localmente. No registra PASS, no reemplaza el encabezado de [estado vigente](../estado_del_proyecto.md) y no autoriza servicios remotos. Este es el corte de aceptación anterior al GO local; la navegación actual está en el [índice](../indice.md), la evidencia en la [ficha de pruebas](../componentes/pruebas_evidencia.md) y el contexto histórico en el [plan de cierre](plan_cierre_integral_h3req1_2026-10-04.md).

## Ficha de impacto y permisos

- Objetivo: acreditar los recorridos públicos, pipeline y Admin sobre el candidato final, con datos sintéticos y casos negativos, sin ampliar funcionalidades de negocio.
- Dominios/consumidores: listado y detalle públicos, comparador, filtros, asesoría, procesamiento de cursos, lector efectivo, edición/auditoría/publicación, BFF, Auth/MFA, membresías, Edge, cuotas, gateway, PostgreSQL/PostgREST y runtimes locales.
- Cambio de esta nota: planificación de aceptación. No cambia código, SQL, runners ni outputs. Añade una ruta documental al WIP; cualquier preflight que cuente WIP debe reconciliar ese delta documental esperado, sin ignorar deltas desconocidos.
- Evidencia: conservar outputs anteriores; reutilizar solamente si inputs, contratos, entorno y grado de prueba siguen aplicando. La existencia de una suite o un marcador no demuestra ejecución.
- Permiso vigente: ciclo local concedido por el usuario; Docker, fixtures y PG17 desechable dentro de su alcance. Sin secretos, datos/cuentas/correo reales, cloud operativo, checkout original, Git de escritura, PR/merge, configuración CI remota, deploy o limpieza global.
- Transición: preservar contratos legacy requeridos y documentar expand → compatibilidad → deploy → contract. Esta aceptación cubre la compatibilidad local; deploy y contract remoto siguen pendientes. Recuperación y rollback solo en fixtures identificados.
- Gate: integrar esta cobertura en G07–G09 sin cambiar sus pesos ni cerrar G10 remoto.

## Preparación obligatoria del catálogo

1. Inventariar rutas reales, componentes, controles visibles, endpoints, RPCs, estados y acciones por rol. No asumir que el catálogo H3 de 48 casos cubre la aplicación pública y el pipeline completo.
2. Cruzar criterios cliente sanitizados y este pedido humano con casos existentes. Marcar grado: estático, unitario, contrato, integración, navegador funcional, visual, rendimiento local.
3. Clasificar cada fila: cobertura vigente, histórica, parcial, faltante o no aplicable con razón verificable. Las pruebas omitidas no cuentan como PASS.
4. Cubrir toda ruta y acción funcional inventariada mediante casos positivos y negativos pertinentes. Para filtros, inventariar cada filtro real, su valor límite, limpieza y combinaciones que interactúan; no prometer probar todas las combinaciones matemáticas posibles.
5. Reutilizar runners y fixtures existentes. Agregar casos y regresiones mínimas; no crear otro framework ni rediseñar producto.
6. Congelar candidato funcional antes de la pasada de aceptación final. Cada corrección cambia sus inputs: revalidar por impacto y conservar la historia. No declarar GO de un snapshot anterior para un candidato cambiado.

## Matriz de cobertura exigida

Todas las filas empiezan **pendientes de conciliación**. El agente ejecutor debe asociar IDs concretos, fuente, runner, fixture y resultado por fila, sin atribuir PASS por esta tabla.

| ID | Área | Casos y criterio observable |
|---|---|---|
| LOCAL-01 | Inventario y fixtures | Datos deterministas con IDs estables; instituciones/categorías/modalidades/tipos diversos; cursos completos/incompletos, precio cero/nulo/normal, fechas válidas/vencidas, publicaciones y estados distintos; identidades admin/user/anon sintéticas; dataset suficiente para paginación y filtros. Fixture fiel al schema; no activar writers cloud. |
| LOCAL-02 | Navegación pública | Home, listado, detalle, comparador, cabecera/footer y rutas informativas existentes; navegación directa/recarga/back-forward/deep link; ruta desconocida, institución/slug inexistentes y estado de carga/error/vacío sin página en blanco ni error inesperado. |
| LOCAL-03 | Muestreo y detalle | Muestra estratificada de cursos por estados y datos; título/institución/precio/moneda/modalidad/duración y campos editoriales que realmente se presentan; ausencia de null/undefined crudos; links y assets locales; lector efectivo respeta elegibilidad/publicación. |
| LOCAL-04 | Filtros, búsqueda y orden público | Cada filtro visible: categoría, institución, modalidad, tipo, precio, duración, objetivo u otros reales; búsqueda, orden, conteos y paginación; mínimos/máximos/límites, combinaciones relevantes, reset, resultados vacíos y persistencia URL/recarga donde el contrato lo exige. Caso priceMin explícito. Seguimientos existentes no sustituyen evidencia ni waiver. |
| LOCAL-05 | Comparación | Agregar/retirar/limpiar, duplicados, límite implementado, cero/uno/múltiples cursos, persistencia y URL, datos faltantes, curso inexistente/no elegible; atributos coinciden con detalle/listado del mismo curso. Storage de comparación no se confunde con material Auth prohibido. |
| LOCAL-06 | Asesoría | Inventariar el canal existente: formulario, enlace u otro contrato real. Ejecutar la acción; validar payload/destino, campos obligatorios si existen, confirmación, rechazo y error/timeout según el flujo. Interceptar o sustituir destino externo por receptor sintético. No enviar mensajes reales ni inventar un canal nuevo para la prueba. |
| LOCAL-07 | Descubrimiento | HTML/sitemap/fuentes locales sintéticas; URLs elegibles/excluidas, duplicadas, recursos no HTML, contenido ausente/malformado y fallos controlados. Verificar gates institucionales vigentes con fallback documentado; trazabilidad de URL/institución e idempotencia. Sin crawling externo. |
| LOCAL-08 | Procesamiento completo | Ejecutar lógica real de descubrimiento/cleansing/enrichment/sync mediante fixtures/adaptadores mínimos aislados. Simular respuestas de IA/embeddings/red externos, no reemplazar las transformaciones por un resultado precargado. Verificar staging→cleansed→enriched→courses, estados, validaciones, errores/recovery y no duplicación. Confirmar que datos descartados no se publican. |
| LOCAL-09 | Sesión y MFA | Login/errores, callback, sesión/refresh/logout, caducidad/inactividad y reautenticación; cookie ligada a session_id y rebind MFA; flags y chunks por ambiente; sin JWT/refresh token en JS/storage/respuestas; sesión A no renueva B; cuenta/MFA operativos intactos. |
| LOCAL-10 | Roles y membresías | Matriz admin/user/anon y membresía inactiva; UI y servidor rechazan acciones no autorizadas; cambio de rol, activación/desactivación, último admin y operaciones concurrentes pertinentes; razón/actor/auditoría y no auto-bloqueo accidental. |
| LOCAL-11 | Invitaciones y onboarding | Invitación sintética por UI, validación, roles, aceptación, establecimiento/recuperación de contraseña según rutas reales, MFA sintética, duplicado/reenvío, expiración, replay, reserva/recovery y efectos únicos; onboarding 10/10 vigente o ampliado por contratos nuevos. Sin correo real ni reset de cuenta existente. |
| LOCAL-12 | Cola Admin | Todos los estados y filtros reales, incluidos pendiente/completado; combinaciones con búsqueda, orden, conteos, paginación y reset; acciones por estado/rol; consistencia entre filas, totales y DB. Comprobar comportamiento, no solo presencia del control. |
| LOCAL-13 | Edición, ownership y auditoría | Cada campo permitido y tipo/límite; admin completa/corrige; user respeta ownership; guardar, recargar y leer persistencia; actor/origen/valor previo/nuevo; auditoría atómica y no modificable por usuario; guardar sin cambio, cancelación y conflicto de versión/concurrencia sin pérdida silenciosa. |
| LOCAL-14 | Vista previa | Abrir editor y visualizar valores efectivos; editar y comprobar preview antes de guardar; guardar, recargar y confirmar; cancelar no persiste; datos parciales y límites de texto/layout; correspondencia con el detalle público cuando el curso sea elegible. |
| LOCAL-15 | Disponibilidad y publicación | Evidencia válida/ausente/inválida/futura/vencida; límite de 90 días y fronteras temporales del contrato; publicar/despublicar, motivos, permisos y auditoría; datos no elegibles no filtrados al lector público; preservar compatibilidad legacy autorizada sin eludir el nuevo contrato. |
| LOCAL-16 | Reflejo entre consumidores | Edición guardada y publicada se refleja en lector efectivo, listado, detalle, comparador y filtros aplicables; verificar requests/datos y recarga/cache según arquitectura. Una exportación estática requiere identificar y probar su mecanismo real de actualización; no prometer publicación instantánea si el contrato exige rebuild. |
| LOCAL-17 | Seguridad y contratos | Entrada inválida, XSS/inyección con payloads de prueba, escaping, errores sanitizados, CSRF/origen/host, endpoints/métodos/destinos allowlisted, permisos SQL/RLS, firma gateway/HMAC, replay/nonce, cuotas/concurrencia y fail-closed. Scanner, scope guard y revisión independiente del candidato. Sin explotación externa ni secretos reales. |
| LOCAL-18 | Runtimes e integración | Snapshot completo/imports transitivos, dependencias fijadas, healthz con petición real al worker y negativo control-up/worker-down. C03 real local Pages/workerd + Edge + PG17 + PostgREST: normal→reserva→suspend→rechazos→cookies→finalización única→preservación→drift→resume→recovery→smoke. |
| LOCAL-19 | Fallos, persistencia y recuperación | Timeouts/error de DB/Auth/Edge/worker simulados, respuestas vacías/malformadas, desconexión/reinicio de fixtures, refresh concurrente y errores de guardado; sin éxitos falsos, corrupción ni pérdida de auditoría. Reintentos solo según contrato idempotente; reproducción independiente del caso fallido. |
| LOCAL-20 | Responsive y accesibilidad funcional | Desktop/tablet/mobile según viewports vigentes; teclado, foco, labels, feedback/errores, dialogs y navegación; tablas/forms/preview/comparador sin controles ocultos o solapamientos bloqueantes. Capturas acompañan assertions de comportamiento. No equivale a certificación global de accesibilidad. |
| LOCAL-21 | Calidad/builds/dependencias | Pytest pertinente y suite completa aplicable, TypeScript, ESLint, ShellCheck/actionlint, scanner, guards, H2 writer scan, audits dev/prod y builds normal/mock; lockfiles/vendor/runtime identificados; registrar warnings/skips sin contarlos aprobados ni inventar waivers. |
| LOCAL-22 | Rendimiento y recursos locales | Medir recorridos representativos, límites de memoria/CPU, colas/cursos suficientemente numerosos, eventos de bloqueo, requests sin límite y paginación. Comparar con baseline reproducible disponible, guardar método/dataset/entorno y variabilidad. Duración de runner no es latencia de producto; no afirmar carga/escala global ni SLA remoto. Sin degradaciones bloqueantes observadas. |
| LOCAL-23 | Evidencia y aceptación | Matriz criterio cliente→caso→resultado→candidato; cuatro ajustes H3 y seis pilares; fuente/build/outputs con manifiestos separados; revisión independiente; artefactos recuperables, fallos históricos y estado vivo consistente. |

## Recorrido integrado imprescindible

Fuente sintética → descubrimiento → limpieza → enriquecimiento con proveedor simulado → sincronización → cola Admin → edición con audit/ownership → preview → disponibilidad válida → publicación → lector público → búsqueda/filtros → detalle → comparación → asesoría hacia receptor sintético.

Comprobar el mismo identificador/procedencia y el dato persistido a través del recorrido; incluir al menos un recorrido negativo que termine en descarte/no publicación, y otro de permiso denegado. Seleccionar adicionalmente los casos de borde representativos del catálogo. El aislamiento debe acreditarse antes de iniciar el pipeline: cualquier intento de destino operativo/remoto detiene el ensayo.

## Resultados, ejecución y cierre

- Crear IDs estables de caso y registrar área, ruta/acción, rol, fixture, precondición, resultado esperado, assertions, candidato/inputs, grado, comando, exit y evidencia sanitizada.
- Las 48×3=144 ejecuciones H3 existentes son un piso de cobertura histórica, no la cifra objetivo de esta aceptación ampliada. Añadir casos necesarios y declarar el nuevo total; mantener cero retries automáticos de UAT. Se autoriza reejecutar casos afectados después de corregir una causa demostrada, preservando cada intento.
- Un mock valida su frontera declarada, no prueba integración real. Una lectura estática de código no sustituye guardar/leer/navegar en runtime. SQL aislado no sustituye C03 integrado.
- G07 no cierra con hashes de un candidato que cambió; G08/G09 deben cubrir los inputs finales. Si la matriz abre cobertura faltante, mantener G09 parcial hasta completarla. La ampliación no cambia el peso histórico de G01–G10 ni el denominador local G01–G09.
- Cada caso local necesario debe pasar. No aplicable requiere razón basada en el inventario funcional; falta de implementación de un comportamiento existente no es no aplicable. Casos con dependencias live se simulan localmente o se declaran límites remotos explícitos, no resultados live.
- Hallazgos HIGH/CRITICAL o funcionales bloqueantes impiden cierre. Cada excepción real necesita aceptación humana con causa, riesgo, owner y vencimiento; el seguimiento de braces/priceMin no es waiver.
- Usar fases acotadas, parar dependientes al fallar, corregir el componente responsable y revalidar por impacto; no repetir ensayos intactos ni añadir infraestructura sin necesidad.
- Antes de GO congelar candidato, verificar estabilidad del tree y conciliar PASS vigentes/históricos. Enlazar esta nota desde estado/índice cuando la sesión ejecutora incorpore el alcance; no mutar concurrentemente esos archivos compartidos desde otra sesión.

**Cierre exigido:** G01–G09 completos y matriz funcional aplicable acreditada sobre el candidato final, sin pendientes locales bloqueantes. Resultado: validación local integral completa para revisión del responsable. G10, GO_LOCAL_PR, configuración/integración protegida, deploy y D01–D14 remotos siguen separados.

La futura reorganización de Obsidian y nomenclatura se ejecutará después de este cierre; esta nota de pruebas no inicia esa reorganización.
