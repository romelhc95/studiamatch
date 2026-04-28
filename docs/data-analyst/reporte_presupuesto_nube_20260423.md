# Informe de Análisis: Proyección de Costos de Nube para StudIAMatch

**Fecha**: 2026-04-23
**Analista**: Subagente @data-analyst
**Estado**: Finalizado
**Objetivo**: Analizar la eficiencia del "Golden Pipeline" actual y proyectar costos para escalamiento masivo (1k y 10k cursos/día) en AWS, GCP y Azure.

---

## 1. Análisis del Tiempo de Ejecución (Golden Pipeline - Desarrollo)

Basado en los logs de ejecución local (`.github/log/local/log_18042026_harvesting_SUCCESS.log`), se ha analizado un ciclo completo de procesamiento para la carga actual de **100 cursos/día**.

### Tiempos Promedio por Fase
| Estación | Proceso | Tiempo Promedio (100 cursos) | Observación |
| :--- | :--- | :--- | :--- |
| **Fase 0** | Inventario de Instituciones | 0.5 segundos | Proceso ultra-ligero de descubrimiento. |
| **Fase 1** | Massive Harvesting | 262 minutos (4h 22m) | Cuello de botella principal. Incluye BFS Crawl y Playwright. |
| **Fase 1.5**| High Fidelity Cleansing | ~5 minutos | Limpieza de HTML y normalización. |
| **Fase 2** | AI Enrichment (14 Pillars) | ~15 minutos | Procesamiento paralelo vía Gemini/CF AI. |
| **Fase 3** | Integrity & Sync | ~2 minutos | Sincronización de vectores y slugs persistentes. |
| **Fase 4** | ROI & QA Audit | ~3 minutos | Auditoría financiera y taxonómica final. |
| **TOTAL** | **Pipeline Completo** | **~287.5 minutos (4.8h)** | **Promedio: 2.87 min/curso.** |

---

## 2. Consumo de Recursos Estimado (Carga Actual: 100 cursos/día)

El consumo se basa en la ejecución de scripts Python con motores de navegación headless (Playwright/Chromium).

- **CPU**: 0.8 vCPU-horas por día. (Picos de 1.5 vCPU durante el renderizado de páginas pesadas).
- **Memoria (RAM)**: 2.0 GB Peak. (Chromium requiere al menos 1.5GB para estabilidad).
- **Red (Networking)**: 200 MB/día (Ingreso de HTML bruto + Egresos de API Supabase/AI).
- **Almacenamiento (Storage)**: 50 MB/día de data bruta (HTML) antes de limpieza.

---

## 3. Comparativa de Costos Proyectados (Estimación Mensual)

Proyección de costos operativos (Compute + AI + DB) para escalar el volumen de procesamiento.

### Escenario A: 1,000 cursos/día (10x)
- **Tiempo requerido**: ~48 horas/día (Requiere al menos 3 workers en paralelo).
- **AI Tokens**: ~90M tokens/mes (Gemini 1.5 Flash).

| Proveedor | Servicio Sugerido | Costo Compute | AI + DB (Pro) | Total Estimado |
| :--- | :--- | :--- | :--- | :--- |
| **AWS** | EC2 Spot (t3.medium) | $20.00 | $43.00 | **$63.00** |
| **GCP** | Compute Engine (e2-med) | $25.00 | $43.00 | **$68.00** |
| **Azure** | Virtual Machines (B2s) | $28.00 | $43.00 | **$71.00** |
| **Cloud (Serverless)** | Cloud Run / Fargate / ACI | $110 - $220 | $43.00 | **$153 - $263** |

### Escenario B: 10,000 cursos/día (100x)
- **Tiempo requerido**: ~480 horas/día (Requiere ~20 workers en paralelo).
- **AI Tokens**: ~900M tokens/mes.

| Proveedor | Servicio Sugerido | Costo Compute | AI + DB (Extra) | Total Estimado |
| :--- | :--- | :--- | :--- | :--- |
| **AWS** | EC2 Spot Cluster (20x) | $180.00 | $280.00 | **$460.00** |
| **GCP** | GCE Preemptible | $200.00 | $280.00 | **$480.00** |
| **Azure** | VM Spot Instances | $210.00 | $280.00 | **$490.00** |
| **Cloud (Serverless)** | Serverless Scaled | $1,100+ | $280.00 | **$1,380+** |

---

## 4. Conclusiones y Recomendaciones

### ¿Serverless o VM?
- **Serverless (Cloud Run / Fargate)**: Recomendado **solo para la Fase 2 (Enrichment)** y **Fase 1.5 (Cleansing)** debido a su naturaleza intermitente y fácil paralelización. No se recomienda para el Harvesting masivo debido a los tiempos de espera y el alto costo por segundo de CPU comparado con VMs.
- **VM (Instancias Spot/Preemptible)**: Es la opción **más eficiente (80% más barata)** para la Fase 1 (Harvesting). Al ser un proceso por lotes (batch) que puede tolerar interrupciones, las instancias Spot de AWS ofrecen el mejor rendimiento por dólar.

### Proveedor Recomendado
**AWS** se posiciona como el proveedor más eficiente para StudIAMatch por:
1.  **Costo de Instancias Spot**: Tienen la mayor liquidez y precios más bajos para familias `t3` y `t4g`.
2.  **Integración con S3**: Para almacenar folletos PDF masivos (Brochures) a bajo costo.
3.  **Ecosistema**: Facilidad para orquestar los 20+ workers necesarios para el escenario de 10k cursos.

### Acción Sugerida (Fase 43)
Implementar una **Cola de Mensajes (SQS o Redis)** para que múltiples workers puedan procesar instituciones en paralelo, permitiendo reducir el tiempo total del pipeline de 4.8 horas a menos de 30 minutos mediante escalado horizontal.
