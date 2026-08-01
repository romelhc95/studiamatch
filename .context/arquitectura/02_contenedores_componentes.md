# Contenedores Y Componentes

Vista derivada de [Frontend](../estructura_frontend.md),
[Pipeline](../arquitectura_pipeline.md) y codigo versionado.

```mermaid
flowchart LR
    subgraph CI["GitHub Actions"]
        FG1["FG1 inventario"]
        FG2["FG2 Golden Pipeline"]
        FG3["FG3 integridad"]
    end

    subgraph Core["Python backend"]
        Orchestrator["master_orchestrator.py"]
        Harvester["universal_harvester.py"]
        Cleansing["cleansing_worker.py"]
        Enrichment["enrichment_worker.py"]
        Sync["sync_vector_worker.py"]
        Integrity["integrity_ping.py"]
    end

    subgraph Data["Supabase por ambiente"]
        Catalogs[("Catalogos y perfiles")]
        Queues[("staging / cleansed / enriched")]
        Courses[("courses")]
        API["PostgREST Data API"]
    end

    subgraph Web["Next.js static export"]
        Build["Server Components y build"]
        Home["Home y /courses"]
        Detail["Detalle"]
        Compare["Comparacion"]
        Admin["/admin\nPENDING_HITO"]
    end

    FG1 --> Catalogs
    FG2 --> Orchestrator
    Orchestrator --> Harvester --> Queues
    Queues --> Cleansing --> Enrichment --> Sync --> Courses
    FG3 --> Integrity --> Courses
    Catalogs --> Orchestrator
    Courses --> API
    API --> Build
    API --> Home
    API --> Detail
    API --> Compare
    Admin -. "writer server-side o RPC no definido" .-> API
```

## Rutas Frontend Actuales

| Ruta | Contenedor | Estado |
|---|---|---|
| `/` | Home, busqueda y listado | `ACTUAL` |
| `/courses/` | Reutiliza la experiencia de Home | `ACTUAL` |
| `/courses/{institution}/{slug}/` | Detalle estatico con carga cliente | `ACTUAL` |
| `/compare/` | Comparacion de hasta tres programas | `ACTUAL` |
| `/privacidad/`, `/terminos/` | Contenido legal | `ACTUAL` |
| `/admin/` | Panel CA4 | `PENDING_HITO` |

No existe una ruta separada `/resultados/` en el baseline. Hito 5 define la
vista contractual de Resultados sin decidir por esta nota una ruta nueva.

## Responsabilidades

- Workflows: scheduling, guards de rama, environments, concurrencia y timeout.
- Python backend: discovery, ETL, persistencia, auditoria e integridad.
- Supabase: schema, RLS, RPC, catalogos y datos operativos por ambiente.
- Frontend: export estatico y lecturas publicas permitidas.
- Browser: filtros, navegacion y comparacion local; nunca secret keys.
