# StudIAMatch.ai - Esquema de Base de Datos y Arquitectura

De acuerdo a las responsabilidades del Arquitecto de Software Senior y los requisitos funcionales, se definen los siguientes 10 puntos clave de la arquitectura de la base de datos:

## 10 Puntos Definidos del Esquema de Datos

1. **Catálogo Maestro de Instituciones:** Se gestiona una tabla central `institutions` que actúa como fuente de la verdad para todas las entidades educativas en el sistema.
2. **Presencia Oficial (official_website):** La tabla `institutions` incluye el campo `official_website` para asegurar la correcta vinculación a los portales oficiales de cada entidad.
3. **Clasificación Educativa (type):** Se incluye un campo `type` con los valores Enum (`Univ`, `Inst`) para diferenciar entre Universidades e Institutos.
4. **Estado Operativo (status):** Se gestiona la disponibilidad de las instituciones mediante el campo `status` (`Activa`, `Inactiva`) para filtrar entidades fuera de servicio.
5. **Integridad Referencial de Cursos:** Todo curso en la tabla `courses` extraído por el core backend mantiene un `institution_id` (Foreign Key) válido que garantiza la consistencia de los datos.
6. **Escalabilidad Geográfica:** Se implementa el campo `region` en `institutions` para permitir que el motor de descubrimiento y las interfaces de búsqueda filtren cursos según las diferentes regiones del Perú.
7. **Gestión de Leads (Captación):** Se crea la tabla `leads` con su Primary Key `id` (UUID) para unificar la intención de los estudiantes potenciales, aplicando políticas de seguridad a nivel de fila (RLS) para permitir su inserción anónima segura.
8. **Soporte para Flujo Específico (type = 'info'):** Diseño optimizado para capturar el interés en un curso exacto usando una Foreign Key opcional `course_id`, además de la información de contacto base (first_name, last_name, email, whatsapp).
9. **Soporte para Recomendación General (type = 'recommendation'):** Soporte para orientación dinámica almacenando `area_interest`, `budget`, `modality` y `description` cuando el usuario aún no tiene un curso definido.
10. **Trazabilidad de Contacto:** Se incorpora un control de estado mediante el campo `status` (Enum: `pending`, `contacted`, `resolved`) y su marca de tiempo `created_at` para el seguimiento del funnel de conversión.

## Gestión Dinámica de Categorías (Enfoque Híbrido)

Como parte del ecosistema, se ha diseñado un módulo de auto-categorización dinámica mediante evaluación de contenido:
- **`categories`**: Almacena las categorías principales, incluyendo por defecto la categoría `General / Por Clasificar`.
- **`category_rules`**: Define reglas semánticas (`id` UUID, `category_id` FK a categories, `keyword` texto único, `priority` int).
- **`courses`**: Incorpora los campos `category_id` y `category_confirmed` (boolean, default false).
- **Asignación Automática (Enfoque Híbrido)**: La función `assign_course_category` evaluada por un Trigger a nivel de base de datos busca la máxima prioridad de coincidencia de un keyword en el nombre, descripción y syllabus.
  - Si encuentra coincidencia: Asigna el `category_id` correspondiente y establece `category_confirmed = true`.
  - Si NO encuentra coincidencia: Asigna el ID de la categoría `General / Por Clasificar` y mantiene `category_confirmed = false`.

## Sistema de Social Proof

Para incrementar la confianza de los estudiantes, se implementa un esquema SQL de validación social (Social Proof):
- **`ratings`**: Tabla para almacenar calificaciones cuantitativas con campos `id`, `course_id`, `rating_value`, `user_nickname`, y `created_at`.
- **`reviews`**: Tabla para almacenar opiniones cualitativas con campos `id`, `course_id`, `content`, `user_nickname`, y `created_at`.
- **Políticas RLS**: Ambas tablas tienen Row Level Security activado. Se permite lectura pública e inserción de nuevos registros con validación básica (ej. `rating_value` entre 1 y 5).
