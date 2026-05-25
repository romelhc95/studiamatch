# Plan de Remediación Definitiva — StudIAMatch

## Resumen de Problemas

| ID | Problema | Causa Raíz | Prioridad |
|---|---|---|---|
| P1 | Cursos no visibles (28/147 en Pro) | FG2 no ha procesado todos los registros; 378 pendientes | 🔴 |
| P2 | Error 404 en páginas de detalle de curso | Static export no se reconstruye automáticamente post-FG2 | 🔴 |
| P3 | JSON en vez de contenido formateado en detalle | `renderText()` no maneja objetos JSON anidados | 🟡 |
| P4 | RPC `lock_staging_records` falla con "cannot set path in scalar" | Circuit breaker implementado pero causa raíz no resuelta | 🟡 |

---

## Tarea A: Refresh schema de PostgREST

**Propósito**: Asegurar que la FK recién agregada (`courses.category_id → categories.id`) sea reconocida por PostgREST.

**Ejecución**: Una sola vez en Supabase Dashboard SQL Editor:

```sql
NOTIFY pgrst, 'reload schema';
```

**Verificación**: La homepage debe mostrar cursos (query con `categories(name)` debe devolver 200).

---

## Tarea B: Arreglar `renderText()` para objetos JSON anidados

**Propósito**: Evitar que campos como `syllabus` (almacenados como `{"pilares": ["item1", "item2"]}`) se rendericen como texto JSON crudo.

**Archivo**: `web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx`

**Cambio**: Reemplazar función `renderText()` (líneas 446-503) con:

```typescript
const renderText = (text: string | undefined) => {
  if (!text) return "Información en proceso de validación.";

  const trimmed = text.trim();

  // === NEW: Manejar objetos JSON {} ===
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    try {
      const parsed = JSON.parse(trimmed);
      if (typeof parsed === 'object' && !Array.isArray(parsed)) {
        const elements: React.ReactNode[] = [];
        let idx = 0;
        for (const [key, value] of Object.entries(parsed)) {
          const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          elements.push(
            <h4 key={`h-${idx}`} className="text-sm font-black uppercase tracking-wider text-brand-blue mt-4 mb-2">
              {label}
            </h4>
          );
          if (Array.isArray(value)) {
            elements.push(
              <ul key={`ul-${idx}`} className="my-2 space-y-1 pl-2">
                {value.map((item: unknown, i: number) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-brand-mint mt-1.5 shrink-0">•</span>
                    <span>{String(item)}</span>
                  </li>
                ))}
              </ul>
            );
          } else if (typeof value === 'object' && value !== null) {
            elements.push(<p key={`p-${idx}`} className="mb-2 italic">Información estructurada disponible.</p>);
          } else {
            elements.push(<p key={`p-${idx}`} className="mb-2">{String(value)}</p>);
          }
          idx++;
        }
        return <div className="text-lg text-slate-600 dark:text-slate-400">{elements}</div>;
      }
    } catch { /* fallthrough */ }
  }

  // === EXISTING: Manejar arrays JSON [] ===
  if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed)) {
        const lines = parsed.map(item => String(item));
        // continuar con lógica existente de renderizado de items...
      }
    } catch { /* fallthrough */ }
  }

  // === EXISTING: Texto plano ===
  const displayLines = trimmed.split('\n');
  const lines = displayLines.map(l => l.trim()).filter(l => l.length > 0);
  const elements: React.ReactNode[] = [];
  let currentList: string[] = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="my-4 space-y-2 pl-2">
          {currentList.map((item, i) => (
            <li key={`li-${i}`} className="flex items-start gap-2">
              <span className="text-brand-mint mt-1.5 shrink-0">•</span>
              <span>{item.replace(/^[-*•]\s*/, '')}</span>
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  lines.forEach((line, i) => {
    const isListItem = /^[-*•]\s+/.test(line) || (trimmed.startsWith('[') && Array.isArray(displayLines));
    if (isListItem) {
      currentList.push(line);
    } else {
      flushList();
      elements.push(<p key={`p-${i}`} className="mb-4 last:mb-0 leading-relaxed">{line}</p>);
    }
  });
  flushList();

  return <div className="text-lg text-slate-600 dark:text-slate-400">{elements}</div>;
};
```

### Tests de regresión (casos que debe soportar):

| Entrada | Resultado esperado |
|---|---|
| `"{"pilares":["A","B"]}"` | Título "Pilares" + bullets A, B |
| `"{"objetivos":"Texto"}` | Título "Objetivos" + párrafo |
| `["item1", "item2"]` | Bullets item1, item2 |
| `"Texto plano\nlínea 2"` | Párrafos separados |
| Texto con bullets `• item` | Lista con viñetas |

---

## Tarea C: Trigger automático de Cloudflare Pages rebuild al finalizar FG2

**Archivo**: `.github/workflows/production_pipeline.yml`

### Paso 1 — Agregar secretos de Cloudflare

Agregar a GitHub Actions secrets (si no existen):
- `CF_ACCOUNT_ID` — ya existe
- `CF_API_TOKEN` — ya existe

### Paso 2 — Agregar step al final del pipeline

En `phase_4_audit`, después del QA Audit, agregar:

```yaml
      - name: Trigger Cloudflare Pages rebuild
        if: always()
        env:
          CF_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
          CF_ACCOUNT_ID: ${{ secrets.CF_ACCOUNT_ID }}
          PROJECT_NAME: studiamatch
        run: |
          RESPONSE=$(curl -s -X POST \
            "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/pages/projects/${PROJECT_NAME}/deployments" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data '{"branch": "main"}')
          STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))")
          if [ "$STATUS" = "True" ]; then
            echo "✅ Cloudflare Pages rebuild triggered successfully"
          else
            echo "⚠️ Cloudflare Pages rebuild trigger returned: $(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('errors', 'unknown'))")"
          fi
```

### Paso 3 — Aumentar timeout de phase_4_audit

El rebuild puede tardar unos segundos. Aumentar `timeout-minutes` de 15 a 20.

---

## Tarea D: Arreglar `lock_staging_records` RPC (causa raíz del circuit breaker)

### Diagnóstico

La función actual es LANGUAGE sql con `RETURNS TABLE(...)`. PG17 puede tener problemas al inlinearla cuando los nombres de OUT parameters (`id`, `url`, etc.) entran en conflicto con columnas de tabla en el scope del UPDATE.

### Solución: Migrar a LANGUAGE plpgsql con columnas fully qualified

**Archivo**: Nueva migración SQL para aplicar en Pro Dashboard

```sql
-- Migration: 20260512_fix_lock_staging_records_plpgsql
-- Fase: Fix RPC lock_staging_records — migrar de SQL a plpgsql
-- para evitar error "cannot set path in scalar" por inline conflict en PG17.
-- Las columnas están fully qualified para eliminar toda ambigüedad.

CREATE OR REPLACE FUNCTION public.lock_staging_records(inst_id uuid, batch_size integer DEFAULT 100)
 RETURNS TABLE(id uuid, url text, institution_id uuid, raw_html text, raw_name text, raw_description text)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
BEGIN
    RETURN QUERY
    UPDATE staging_raw
    SET status = 'processing'
    WHERE staging_raw.id IN (
        SELECT sub.id
        FROM staging_raw AS sub
        WHERE sub.status = 'pending'
        AND (sub.institution_id = inst_id OR inst_id IS NULL)
        ORDER BY sub.last_harvested_at ASC NULLS FIRST
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    )
    RETURNING staging_raw.id, staging_raw.url, staging_raw.institution_id,
              staging_raw.raw_html, staging_raw.raw_name, staging_raw.raw_description;
END;
$function$;
```

**Verificación**: Ejecutar después de aplicar:

```sql
SELECT * FROM lock_staging_records(NULL, 3);
-- Debe retornar registros sin error "cannot set path in scalar"
```

---

## Tarea E: Normalizar syllabus existente en DB Pro

**Propósito**: Corregir los registros existentes que tienen `syllabus` como objeto JSON.

```sql
UPDATE courses
SET syllabus = (
  SELECT string_agg(value, E'\n')
  FROM jsonb_each_text(syllabus::jsonb) AS each_key(key, value_agg)
  CROSS JOIN LATERAL (
    SELECT CASE
      WHEN value_agg LIKE '["[%"]%' THEN (
        SELECT string_agg(item, E'\n')
        FROM jsonb_array_elements_text(value_agg::jsonb) AS items(item)
      )
      ELSE value_agg
    END AS final_value
  ) AS sub
  CROSS JOIN LATERAL (
    SELECT '- ' || key || ': ' || final_value AS line
  ) AS line_gen
)
WHERE syllabus IS NOT NULL AND syllabus LIKE '{%';

ALTER TABLE courses
ADD CONSTRAINT chk_syllabus_is_text CHECK (
  syllabus IS NULL OR syllabus !~ '^\s*[{[]'
);
```

**Nota**: Esta migración es delicada porque el formato puede variar. Se recomienda revisar primero los datos:

```sql
SELECT slug, syllabus FROM courses WHERE syllabus LIKE '{%' LIMIT 5;
```

---

## Tarea F: Ejecutar FG2 hasta procesar todos los registros

**Propósito**: Consumir los 378 registros pendientes (206 pending + 172 discovered en staging_raw + 46 pending en cleansed_programs).

**Procedimiento**:

```bash
# 1. Después de aplicar tareas A, B, C, D, E → PR a main

# 2. Ejecutar FG2 manualmente en main
gh workflow run "FG2 - StudIAMatch Golden Pipeline" --ref main

# 3. Monitorear
gh run list --workflow "FG2 - StudIAMatch Golden Pipeline" --branch main --limit 3

# 4. Repetir hasta que staging_raw pending/discovered ≈ 0
#    SELECT status, COUNT(*) FROM staging_raw GROUP BY status;
#    (ignorar skipped que son por pipeline_ready=false)

# 5. Si quedan registros skipped que deberían procesarse:
#    Activar pipeline_ready=true para esa institución
#    Luego: SELECT requeue_pipeline_records('institution-uuid');
```

**Criterio de éxito**: `staging_raw` solo tiene registros `discarded` o `skipped`. `cleansed_programs` solo `synced`. `enriched_programs` solo `synced`. Total cursos en Pro ≈ 147+.

---

## Orden de Ejecución

```
A → [SQL en Dashboard] Refresh schema PostgREST          (1 min)
↓
B → [Código] Arreglar renderText()                         (20 min)
C → [Código] Trigger Cloudflare rebuild en pipeline        (15 min)
D → [SQL en Dashboard + Código] Fix lock_staging_records  (10 min)
↓
E → [SQL en Dashboard] Normalizar syllabus existente       (5 min)
↓
F1 → commit, push, PR → desarrollo → certificacion → main
F2 → rebuild Cloudflare Pages
F3 → Ejecutar FG2 repetidamente hasta procesar todo
```

¿Revisas el plan para que proceda con la implementación?
