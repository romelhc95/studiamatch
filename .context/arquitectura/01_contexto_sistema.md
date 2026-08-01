# Contexto Del Sistema

Vista derivada del sistema y sus dependencias. Ver [Mapa](./00_mapa.md).

```mermaid
flowchart TB
    Visitor["Visitante publico"]
    Operator["Operador de pipeline"]
    AdminUser["Administrador futuro\nPROPOSED_PENDING_APPROVAL"]
    SourceSites["Sitios institucionales"]
    AIProviders["Proveedores AI"]
    GitHub["GitHub Actions y Environments"]
    CloudHost["Hosting estatico"]
    System["StudIAMatch"]
    Supabase["Supabase Free / Pro"]

    Visitor -->|consulta catalogo| System
    Operator -->|workflow autorizado| GitHub
    GitHub --> System
    SourceSites -->|contenido publico| System
    AIProviders -->|enriquecimiento| System
    System --> Supabase
    System --> CloudHost
    CloudHost --> Visitor
    AdminUser -. "CA4 pendiente" .-> System
```

## Actores Y Fronteras

| Actor o sistema | Interaccion autorizada | Limite |
|---|---|---|
| Visitante publico | Lee catalogo publicado y usa comparacion local | Sin escrituras privilegiadas ni PII automatizada |
| Operador de pipeline | Dispara o supervisa workflows por environment | Secrets solo en CI/backend |
| Administrador futuro | CA4 propone curacion manual | No existe identidad ni writer aprobado actualmente |
| Sitios institucionales | Fuentes publicas para discovery y harvesting | Allowlist, exclusiones, timeouts y circuit breaker |
| Proveedores AI | Enriquecimiento con fallback marcado | No demuestran verdad editorial ni busqueda semantica |
| Supabase | Persistencia y Data API por ambiente | Datos operativos no se copian Free a Pro |
| Hosting estatico | Publica `web/out` | No es backend administrativo |

## Alcance Temporal

- `ACTUAL`: frontend publico estatico, Golden Pipeline de cuatro estaciones,
  FG1/FG2/FG3 y Supabase por ambiente.
- `PROPOSED_PENDING_APPROVAL`: CA1-only, contrato CA2/CA3, `/admin`, Home y
  Resultados revisados.
- `EXCLUDED`: email/webhook real-time de leads, embeddings, reviews reales,
  scraping automatico de logos y tipo de cambio real.
