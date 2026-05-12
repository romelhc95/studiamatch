-- Migration: 20260512_normalize_syllabus_text
-- Normalize existing JSON-like syllabus payloads into readable text.
-- Handles object JSON ({...}) and array JSON ([...]) and then enforces CHECK.

BEGIN;

-- 1) Objects: {"pilares":[...],"objetivos":"..."} -> "- pilares: ..."
UPDATE courses
SET syllabus = normalized.lines
FROM (
    SELECT
        c.id,
        string_agg('- ' || e.key || ': ' || kv.value_text, E'\n' ORDER BY e.key) AS lines
    FROM courses AS c
    CROSS JOIN LATERAL jsonb_each(c.syllabus::jsonb) AS e(key, value)
    CROSS JOIN LATERAL (
        SELECT CASE
            WHEN jsonb_typeof(e.value) = 'array' THEN (
                SELECT string_agg(item, ', ')
                FROM jsonb_array_elements_text(e.value) AS a(item)
            )
            WHEN jsonb_typeof(e.value) = 'string' THEN trim(both '"' from e.value::text)
            ELSE e.value::text
        END AS value_text
    ) AS kv
    WHERE c.syllabus IS NOT NULL
      AND c.syllabus ~ '^\s*\{'
    GROUP BY c.id
) AS normalized
WHERE courses.id = normalized.id;

-- 2) Arrays: ["item1", "item2"] -> "- item1\n- item2"
UPDATE courses
SET syllabus = normalized.lines
FROM (
    SELECT
        c.id,
        string_agg('- ' || a.item, E'\n' ORDER BY a.ord) AS lines
    FROM courses AS c
    CROSS JOIN LATERAL jsonb_array_elements_text(c.syllabus::jsonb) WITH ORDINALITY AS a(item, ord)
    WHERE c.syllabus IS NOT NULL
      AND c.syllabus ~ '^\s*\['
    GROUP BY c.id
) AS normalized
WHERE courses.id = normalized.id;

-- 3) If malformed remnants still start with { or [, null them to avoid constraint failure.
--    (Defensive fallback; should be rare.)
UPDATE courses
SET syllabus = NULL
WHERE syllabus IS NOT NULL
  AND syllabus ~ '^\s*[{[]';

-- 4) Add CHECK only if missing.
DO $block$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_syllabus_is_text'
          AND conrelid = 'public.courses'::regclass
    ) THEN
        ALTER TABLE public.courses
        ADD CONSTRAINT chk_syllabus_is_text CHECK (
            syllabus IS NULL OR syllabus !~ '^\s*[{[]'
        );
    END IF;
END;
$block$;

COMMIT;
