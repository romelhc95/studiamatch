---
name: mobile-architect
description: Mejores prácticas para el desarrollo de aplicaciones móviles con Flutter y Dart, cubriendo widgets, gestión de estado (Riverpod, BLoC), rendimiento y arquitectura limpia.
tools:
  - '*'
---
# Desarrollo de Aplicaciones Móviles con Flutter y Dart

Guía integral para el desarrollo de aplicaciones móviles robustas y de alto rendimiento.

## Mejores Prácticas de Widgets

### 1. Descomposición de Widgets
- Ningún método `build()` debe exceder las 100 líneas.
- Divida los widgets por encapsulamiento y por fronteras de re-renderizado.
- Use widgets Stateless siempre que sea posible.

### 2. Uso de `const`
- Use constructores `const` siempre que sea posible para evitar re-renderizados innecesarios.
- Declare constantes para colecciones que no cambian.

## Gestión de Estado (State Management)
- **Separación de Concernimientos**: La lógica de negocio vive fuera de la capa de widgets (BLoC, Notifier, Store).
- **Inyección de Dependencias**: Use inyección de dependencias para proveer servicios a los gestores de estado.
- **Inmutabilidad**: El estado debe ser inmutable; cree nuevas instancias mediante `copyWith()`.

## Rendimiento Móvil
- **Re-renderizados**: Localice los cambios de estado en el subárbol más pequeño posible.
- **Imágenes**: Use caché para imágenes de red y optimice su resolución.
- **Listas Largas**: Use `ListView.builder` para listas dinámicas o grandes en lugar del constructor normal.

## Arquitectura Limpia (Clean Architecture)
- Separe las capas de UI, Negocio y Datos.
- Los widgets y gestores de estado no deben llamar directamente a APIs o bases de datos.
- Use repositorios para abstraer las fuentes de datos.

---
*Basado en el catálogo oficial de ECC (everything-claude-code).*
