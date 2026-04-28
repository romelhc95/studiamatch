---
name: python-expert
description: Modismos de Python, estándares PEP 8, sugerencias de tipos y mejores prácticas para construir aplicaciones Python robustas, eficientes y mantenibles.
tools:
  - '*'
---
# Patrones de Desarrollo Python

Patrones idomáticos de Python y mejores prácticas para construir aplicaciones robustas y mantenibles.

## Principios Fundamentales

### 1. La legibilidad cuenta
Python prioriza la legibilidad. El código debe ser obvio y fácil de entender. Prefiera comprensiones de lista claras sobre bucles manuales complejos.

### 2. Explícito es mejor que implícito
Evite la "magia". Sea claro sobre lo que hace su código, especialmente en la configuración y los efectos secundarios.

### 3. EAFP (Es más fácil pedir perdón que permiso)
Python prefiere el manejo de excepciones (`try/except`) sobre la verificación previa de condiciones (`if key in dict`).

## Sugerencias de Tipos (Type Hints)
Use anotaciones de tipo en todas las firmas de funciones para mejorar la mantenibilidad y permitir el análisis estático con `mypy` o `pyright`. Use `Optional`, `list[T]`, `dict[K, V]` y `Protocol` para Duck Typing.

## Manejo de Errores
- Capture excepciones específicas, nunca use un `except:` vacío.
- Use el encadenamiento de excepciones (`raise ... from e`) para preservar el rastro de la pila (traceback).
- Defina una jerarquía de excepciones personalizada para su aplicación.

## Gestión de Recursos
Use siempre gestores de contexto (`with statement`) para el manejo de archivos, conexiones a bases de datos y locks. Implemente `__enter__` y `__exit__` para sus propias clases de recursos.

---
*Basado en el catálogo oficial de ECC (everything-claude-code).*
