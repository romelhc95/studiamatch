---
name: backend-architect
description: Patrones de arquitectura backend, diseño de API, optimización de base de datos y mejores prácticas del lado del servidor.
tools:
  - '*'
---
# Patrones de Desarrollo Backend

Patrones de arquitectura backend y mejores prácticas para aplicaciones escalables del lado del servidor.

## Cuándo Activar

- Al diseñar endpoints de API REST o GraphQL.
- Al implementar capas de repositorio, servicio o controlador.
- Al optimizar consultas de base de datos (N+1, índices, pooling).
- Al añadir caché (Redis, memoria, cabeceras HTTP).
- Al configurar tareas en segundo plano o procesamiento asíncrono.
- Al estructurar el manejo de errores y validación para APIs.
- Al construir middleware (autenticación, logging, rate limiting).

## Patrones de Diseño de API

### Estructura de API RESTful
- Use URLs basadas en recursos: `GET /api/markets`, `POST /api/markets`.
- Use parámetros de consulta para filtrado, ordenación y paginación.

### Patrón de Repositorio (Repository Pattern)
Abstrae la lógica de acceso a datos detrás de una interfaz estándar (findAll, findById, create, update, delete). La lógica de negocio depende de la interfaz abstracta, no del mecanismo de almacenamiento.

### Capa de Servicio (Service Layer Pattern)
Separa la lógica de negocio del acceso a datos. El servicio orquesta múltiples repositorios o APIs externas.

## Patrones de Base de Datos

### Prevención de Consultas N+1
- **MAL**: Obtener datos relacionados en un bucle (N consultas).
- **BIEN**: Obtención por lotes (Batch fetch) o uso de JOINs (1 consulta).

### Patrón de Transacción
Use transacciones de base de datos (o funciones RPC en Supabase) para garantizar la atomicidad en operaciones que involucran múltiples tablas.

## Estrategias de Caché
- **Caché Redis**: Capa de almacenamiento rápido para reducir la carga en la DB principal.
- **Cache-Aside**: Intente leer de la caché; si falla, lea de la DB y actualice la caché.

## Autenticación y Autorización
- **Validación de Tokens JWT**: Almacenamiento seguro en cookies httpOnly.
- **RBAC (Control de Acceso Basado en Roles)**: Verifique permisos antes de ejecutar acciones sensibles.

---
*Basado en el catálogo oficial de ECC (everything-claude-code).*
