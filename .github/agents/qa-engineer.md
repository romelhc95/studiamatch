---
name: qa-engineer
description: Patrones de pruebas E2E con Playwright, Modelo de Objetos de Página (POM), configuración, integración con CI/CD, gestión de artefactos y estrategias para pruebas inestables.
tools:
  - '*'
---
# Patrones de Pruebas End-to-End (E2E)

Esta habilidad proporciona patrones exhaustivos para construir suites de pruebas E2E estables, rápidas y mantenibles utilizando **Playwright**.

## Modelo de Objetos de Página (Page Object Model - POM)
Encapsule la lógica de la interfaz de usuario en clases dedicadas. Esto permite que, si la UI cambia, solo deba actualizar el objeto de página y no cada prueba individualmente.

## Estructura de Pruebas
- **Aislamiento**: Cada prueba debe ser independiente.
- **Hooks**: Use `test.beforeEach` para preparar el estado (ej. navegar a la página o iniciar sesión).
- **Aserciones**: Use aserciones web de Playwright (`expect(locator).toBeVisible()`) que esperan automáticamente a que se cumpla la condición.

## Gestión de Pruebas Inestables (Flaky Tests)
- **Auto-wait**: Playwright espera automáticamente a que los elementos estén listos antes de interactuar. Evite `waitForTimeout`.
- **Reintentos**: Configure reintentos automáticos en CI para manejar fallos de red esporádicos.
- **Cuarentena**: Use `test.fixme()` para marcar pruebas que fallan sistemáticamente y aislarlas del flujo principal hasta que se corrijan.

## Artefactos y Reportes
Configure Playwright para capturar:
- **Capturas de pantalla**: Solo en caso de fallo.
- **Videos**: Para entender el flujo que llevó al error.
- **Trazas (Traces)**: Para una depuración profunda paso a paso con el DOM y la red.

---
*La calidad E2E garantiza que los flujos críticos del usuario siempre funcionen.*
