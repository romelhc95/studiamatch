---
name: devops-engineer
description: Flujos de trabajo de despliegue, patrones de tuberías CI/CD, contenedorización con Docker, verificaciones de salud, estrategias de rollback y listas de verificación para producción.
tools:
  - '*'
---
# Patrones de Despliegue y DevOps (ECC Core)

Esta habilidad define los estándares para llevar el código desde el repositorio hasta un entorno de producción estable y escalable.

## Estrategias de Despliegue

### 1. Rolling Deployment (Por defecto)
Reemplaza instancias gradualmente. Útil cuando los cambios son compatibles con versiones anteriores.
- **Pros**: Cero tiempo de inactividad.
- **Contras**: Dos versiones corren simultáneamente durante el despliegue.

### 2. Blue-Green Deployment
Mantiene dos entornos idénticos. Cambia el tráfico atómicamente de Azul (v1) a Verde (v2).
- **Pros**: Rollback instantáneo.
- **Contras**: Requiere el doble de infraestructura durante el proceso.

### 3. Canary Deployment
Dirige un pequeño porcentaje del tráfico (ej. 5%) a la nueva versión para validar métricas antes del despliegue total.

## Contenedorización con Docker

### Mejores Prácticas
- **Multi-Stage Builds**: Use varias etapas para minimizar el tamaño de la imagen final.
- **No-Root**: Ejecute la aplicación con un usuario sin privilegios de root.
- **Pines de Versión**: Nunca use la etiqueta `:latest`. Use versiones específicas (ej. `node:22-alpine`).
- **.dockerignore**: Excluya `node_modules`, `.git` y pruebas de la imagen.

## Pipeline de CI/CD (GitHub Actions)

### Etapas Estándar
1.  **Validación**: Linting, Typecheck y Pruebas Unitarias.
2.  **Construcción**: Creación de la imagen Docker y subida al registro (ej. GHCR).
3.  **Despliegue**: Actualización automática del servicio en el entorno correspondiente (Vercel, Railway, K8s).

## Monitoreo y Salud (Health Checks)
Implemente un endpoint `/health` que no solo responda "ok", sino que verifique la conectividad con la base de datos y servicios externos críticos.

## Lista de Verificación para Producción (Checklist)
- [ ] Sin secretos codificados (llaves API en variables de entorno).
- [ ] Manejo de errores que cubra todos los casos de borde.
- [ ] Logs estructurados en formato JSON.
- [ ] Límites de recursos (CPU/Memoria) configurados.
- [ ] SSL/TLS habilitado en todos los endpoints.
- [ ] Plan de rollback documentado y probado.

---
*Un despliegue automatizado y seguro es la base de la confiabilidad.*
