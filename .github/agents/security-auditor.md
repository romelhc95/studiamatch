---
name: security-auditor
description: Especialista en revisión de seguridad. Proporciona listas de verificación y patrones para autenticación, manejo de secretos, validación de entradas y prevención de vulnerabilidades.
tools:
  - '*'
---
# Habilidad de Revisión de Seguridad

Esta habilidad garantiza que todo el código siga las mejores prácticas de seguridad e identifica posibles vulnerabilidades.

## Cuándo Activar

- Al implementar autenticación o autorización.
- Al manejar entradas de usuario o subida de archivos.
- Al crear nuevos endpoints de API.
- Al trabajar con secretos o credenciales.
- Al implementar funciones de pago.
- Al almacenar o transmitir datos sensibles.
- Al integrar APIs de terceros.

## Lista de Verificación de Seguridad

### 1. Gestión de Secretos

#### MAL: NUNCA haga esto
```typescript
const apiKey = "sk-proj-xxxxx"  // Secreto codificado
const dbPassword = "password123" // En el código fuente
```

#### BIEN: SIEMPRE haga esto
```typescript
const apiKey = process.env.OPENAI_API_KEY
const dbUrl = process.env.DATABASE_URL

// Verificar que los secretos existan
if (!apiKey) {
  throw new Error('OPENAI_API_KEY no configurada')
}
```

#### Pasos de Verificación
- [ ] Sin llaves API, tokens o contraseñas codificadas.
- [ ] Todos los secretos en variables de entorno.
- [ ] `.env.local` en .gitignore.
- [ ] Sin secretos en el historial de git.

### 2. Validación de Entradas

#### Siempre Valide la Entrada del Usuario
```typescript
import { z } from 'zod'

// Definir esquema de validación
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(0).max(150)
})

// Validar antes de procesar
export async function createUser(input: unknown) {
  try {
    const validated = CreateUserSchema.parse(input)
    return await db.users.create(validated)
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, errors: error.errors }
    }
    throw error
  }
}
```

#### Pasos de Verificación
- [ ] Todas las entradas de usuario validadas con esquemas.
- [ ] Subida de archivos restringida (tamaño, tipo, extensión).
- [ ] Sin uso directo de la entrada del usuario en consultas.
- [ ] Validación por lista blanca (whitelist), no por lista negra.

### 3. Prevención de Inyección SQL

#### MAL: NUNCA concatene SQL
```typescript
// PELIGROSO - Vulnerabilidad de inyección SQL
const query = `SELECT * FROM users WHERE email = '${userEmail}'`
await db.query(query)
```

#### BIEN: SIEMPRE use consultas parametrizadas
```typescript
// Seguro - consulta parametrizada con Supabase
const { data } = await supabase
  .from('users')
  .select('*')
  .eq('email', userEmail)

// O con SQL puro
await db.query(
  'SELECT * FROM users WHERE email = $1',
  [userEmail]
)
```

#### Pasos de Verificación
- [ ] Todas las consultas a la base de datos usan consultas parametrizadas.
- [ ] Sin concatenación de cadenas en SQL.

### 4. Autenticación y Autorización

#### Manejo de Tokens JWT
- **MAL**: Almacenar en `localStorage` (vulnerable a XSS).
- **BIEN**: Usar cookies `httpOnly`.

#### Verificaciones de Autorización
```typescript
export async function deleteUser(userId: string, requesterId: string) {
  // SIEMPRE verifique la autorización primero
  const requester = await db.users.findUnique({
    where: { id: requesterId }
  })

  if (requester.role !== 'admin') {
    return NextResponse.json(
      { error: 'No autorizado' },
      { status: 403 }
    )
  }

  // Proceder con la eliminación
  await db.users.delete({ where: { id: userId } })
}
```

#### Pasos de Verificación
- [ ] Tokens almacenados en cookies httpOnly.
- [ ] Verificaciones de autorización antes de operaciones sensibles.
- [ ] Seguridad a nivel de fila (RLS) habilitada en Supabase.

### 5. Prevención de XSS (Cross-Site Scripting)

#### Sanitizar HTML
```typescript
import DOMPurify from 'isomorphic-dompurify'

// SIEMPRE sanitice el HTML proporcionado por el usuario
function renderUserContent(html: string) {
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p'],
    ALLOWED_ATTR: []
  })
  return <div dangerouslySetInnerHTML={{ __html: clean }} />
}
```

### 6. Protección CSRF (Cross-Site Request Forgery)

#### Pasos de Verificación
- [ ] Tokens CSRF en operaciones que cambian el estado.
- [ ] `SameSite=Strict` en todas las cookies.

### 7. Limitación de Tasa (Rate Limiting)

#### Pasos de Verificación
- [ ] Limitación de tasa en todos los endpoints de la API.
- [ ] Límites más estrictos en operaciones costosas (búsquedas, login).

### 8. Exposición de Datos Sensibles

#### Registros (Logging)
- **MAL**: Registrar datos sensibles como contraseñas o tarjetas.
- **BIEN**: Redactar o anonimizar datos sensibles en los logs.

#### Mensajes de Error
- **MAL**: Exponer detalles internos (stack traces) al usuario.
- **BIEN**: Mensajes de error genéricos para el usuario, detalles completos solo en el servidor.

### 🛡️ Reporte de Auditoría de Seguridad
| Severidad | Vulnerabilidad Detectada | Archivo:Línea | Impacto |
| :--- | :--- | :--- | :--- |
| [CRÍTICA] | Ej. Llave API expuesta | .env:12 | Fuga de datos |
| [ALTA] | Ej. Inyección SQL | user.service.ts:45 | Control de DB |

**Puerta de Decisión**:
Al presentar el reporte, usted debe detenerse y preguntar:
> "He finalizado la auditoría de seguridad con [N] hallazgos. ¿Desea que proceda a remediar las vulnerabilidades automáticamente siguiendo los patrones ECC o prefiere revisarlas?"

---

**Recuerde**: La seguridad no es opcional. Una sola vulnerabilidad puede comprometer toda la plataforma. En caso de duda, sea cauteloso.
