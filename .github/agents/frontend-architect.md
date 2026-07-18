---
name: frontend-architect
description: Patrones de desarrollo frontend para React, Next.js, gestión de estado, optimización de rendimiento y mejores prácticas de UI.
tools:
  - '*'
---
# Patrones de Desarrollo Frontend

Patrones modernos de frontend para React, Next.js e interfaces de usuario de alto rendimiento.

## Cuándo Activar

- Al construir componentes de React (composición, props, renderizado).
- Al gestionar el estado (useState, useReducer, Zustand, Context).
- Al implementar la obtención de datos (SWR, React Query, server components).
- Al optimizar el rendimiento (memorización, virtualización, división de código).
- Al trabajar con formularios (validación, entradas controladas, esquemas Zod).
- Al manejar el enrutamiento y la navegación del lado del cliente.
- Al construir patrones de UI accesibles y responsivos.

## Patrones de Componentes

### Composición sobre Herencia

```typescript
// BIEN: Composición de componentes
interface CardProps {
  children: React.ReactNode
  variant?: 'default' | 'outlined'
}

export function Card({ children, variant = 'default' }: CardProps) {
  return <div className={`card card-${variant}`}>{children}</div>
}

// Uso
<Card variant="outlined">
  <CardHeader>Título</CardHeader>
  <CardBody>Contenido del cuerpo</CardBody>
</Card>
```

### Componentes Compuestos (Compound Components)

```typescript
// Permite una API de componentes más flexible y legible
<Tabs defaultTab="overview">
  <TabList>
    <Tab id="overview">Resumen</Tab>
    <Tab id="details">Detalles</Tab>
  </TabList>
</Tabs>
```

## Optimización del Rendimiento

### Memorización
- **useMemo**: Para cálculos costosos.
- **useCallback**: Para funciones pasadas a componentes hijos para evitar re-renderizados.
- **React.memo**: Para componentes puros que no necesitan re-renderizarse si sus props no cambian.

### Virtualización de Listas Largas
Use `@tanstack/react-virtual` para renderizar solo los elementos visibles en el viewport, mejorando drásticamente el rendimiento en listas de miles de elementos.

## Manejo de Formularios
Prefiera formularios controlados con validación de esquemas usando **Zod**. Esto garantiza que los datos sean válidos antes de intentar enviarlos al backend.

---
*Basado en el catálogo oficial de ECC (everything-claude-code).*
