---
name: db-migrator
description: Guía de mejores prácticas para migraciones de esquemas de bases de datos, cambios sin tiempo de inactividad (Zero-Downtime) y herramientas populares.
tools:
  - '*'
---
# Migraciones de Bases de Datos

Estrategias y mejores prácticas para gestionar la evolución de esquemas de datos de forma segura.

## Principios Fundamentales

1. **Migraciones Versionadas**: Cada cambio debe estar en un archivo de migración versionado y rastreable por el sistema de control de versiones.
2. **Atomicidad**: Cada archivo de migración debe ser una transacción única. Si algo falla, el sistema debe ser capaz de revertir el cambio automáticamente.
3. **Inmutabilidad**: Nunca edite un archivo de migración que ya haya sido desplegado en producción. Cree uno nuevo para corregir errores.
4. **Validación**: Siempre pruebe las migraciones en un entorno de staging antes de aplicarlas en producción.

## Estrategia de Migración sin Tiempo de Inactividad (Zero-Downtime)

Para cambios críticos en producción, siga el patrón **Expand-Contract (Expandir-Contraer)**:

- **Fase 1: EXPANDIR**: Añada la nueva columna o tabla (opcional o con valor por defecto). Despliegue la app para escribir tanto en lo viejo como en lo nuevo.
- **Fase 2: MIGRAR**: Despliegue la app para leer solo de lo nuevo pero seguir escribiendo en ambos. Verifique la consistencia.
- **Fase 3: CONTRAER**: Despliegue la app para usar solo lo nuevo. Elimine la columna o tabla vieja en una migración separada.

## Herramientas Populares
- **Prisma**: `npx prisma migrate dev` para desarrollo y `npx prisma migrate deploy` para producción.
- **Django**: `python manage.py makemigrations` y `python manage.py migrate`.
- **Drizzle**: `npx drizzle-kit generate` y `npx drizzle-kit migrate`.

---
*Basado en el catálogo oficial de ECC (everything-claude-code).*
