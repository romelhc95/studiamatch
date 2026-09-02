-- H3 local-only demonstration seed. Never apply to Supabase Free.

INSERT INTO auth.users (
    id,
    email,
    encrypted_password,
    role,
    aud,
    email_confirmed_at,
    created_at,
    updated_at
) VALUES (
    '30000000-0000-0000-0000-000000000001',
    'admin@studiamatch.com',
    crypt(current_setting('h3.test_password', true), gen_salt('bf')),
    'authenticated',
    'authenticated',
    now(),
    now(),
    now()
) ON CONFLICT DO NOTHING;

INSERT INTO public.admin_members (user_id, role, is_active)
VALUES ('30000000-0000-0000-0000-000000000001', 'admin', true) ON CONFLICT DO NOTHING;

-- Additional local identities for RBAC tests (admin + user + inactive user).
INSERT INTO auth.users (
    id,
    email,
    encrypted_password,
    role,
    aud,
    email_confirmed_at,
    created_at,
    updated_at
)
SELECT
    ('30000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
    'seed-' || n || '@studiamatch.local',
    crypt(current_setting('h3.test_password', true), gen_salt('bf')),
    'authenticated',
    'authenticated',
    now(),
    now(),
    now()
FROM generate_series(2, 5) AS n
ON CONFLICT DO NOTHING;

INSERT INTO public.admin_members (user_id, role, is_active)
SELECT
    ('30000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
    CASE WHEN n = 2 THEN 'admin' WHEN n = 3 THEN 'user' WHEN n = 4 THEN 'user' ELSE 'user' END,
    n <> 5
FROM generate_series(2, 5) AS n
ON CONFLICT DO NOTHING;

INSERT INTO public.institutions (id, name, slug, website_url)
SELECT
    ('00000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
    names[n],
    slugs[n],
    'https://' || slugs[n] || '.example.test'
FROM (
    SELECT
        generate_series(1, 5) AS n,
        ARRAY[
            'Universidad de Lima',
            'Pontificia Universidad Católica del Perú',
            'Universidad Peruana de Ciencias Aplicadas',
            'Universidad San Ignacio de Loyola',
            'Universidad Tecnológica del Perú'
        ]         AS names,
        ARRAY['ulima', 'pucp', 'upc', 'usil', 'utp'] AS slugs
) seed
ON CONFLICT DO NOTHING;

-- Categories: every seeded course must carry a category so quality recompute stays consistent.
INSERT INTO public.categories (id, name)
SELECT
    ('01000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
    cat_names[n]
FROM (
    SELECT
        generate_series(1, 5) AS n,
        ARRAY[
            'Programas de grado',
            'Posgrados y maestrías',
            'Cursos y certificaciones',
            'Educación ejecutiva',
            'Idiomas'
        ]         AS cat_names
) seed
ON CONFLICT DO NOTHING;

INSERT INTO public.courses (
    id,
    institution_id,
    name,
    slug,
    url,
    price_pen,
    mode,
    duration,
    start_date,
    is_active,
    is_verified,
    provider_used,
    is_mock_data,
    created_at,
    updated_at
)
SELECT
    ('20000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
    ('00000000-0000-0000-0000-' || lpad((((n - 1) % 5) + 1)::text, 12, '0'))::uuid,
    'Programa local H3 ' || lpad(n::text, 2, '0'),
    'programa-local-h3-' || lpad(n::text, 2, '0'),
    'https://local.example.test/programas/' || n,
    5000 + (n * 250),
    CASE (n % 3) WHEN 0 THEN 'Remoto' WHEN 1 THEN 'Presencial' ELSE 'Hibrido' END,
    (6 + (n % 18)) || ' meses',
    DATE '2026-09-01' + n,
    n <= 25,
    n > 10,
    'local_seed',
    true,
    now() - make_interval(days => 31 - n),
    now() - make_interval(hours => 31 - n)
FROM generate_series(1, 30) AS n
ON CONFLICT DO NOTHING;

-- Assign the matching category to every locally seeded course (idempotent).
UPDATE public.courses c
SET category_id = (
    '01000000-0000-0000-0000-'
    || lpad((((substring(c.slug FROM '[0-9]+$'))::integer - 1) % 5 + 1)::text, 12, '0')
)::uuid
WHERE c.id::text LIKE '20000000-0000-0000-0000-%'
  AND (c.category_id IS NULL OR c.category_id::text NOT LIKE '01000000-%');

INSERT INTO public.course_editorial_state (
    course_id,
    editorial_status,
    quality_status,
    missing_fields,
    field_sources,
    field_timestamps,
    availability_status,
    manual_updated_by,
    published_at,
    archived_at,
    version,
    created_at,
    updated_at
)
SELECT
    c.id,
    CASE
        WHEN n <= 10 THEN 'draft'
        WHEN n <= 20 THEN 'pending_review'
        WHEN n <= 25 THEN 'published'
        ELSE 'archived'
    END,
    CASE
        WHEN n <= 10 THEN 'pending'
        WHEN n <= 25 THEN 'complete'
        ELSE 'blocked'
    END,
    CASE WHEN n <= 10 THEN ARRAY['description_long', 'requirements']::text[] ELSE ARRAY[]::text[] END,
    '{"name":"pipeline","url":"pipeline"}'::jsonb,
    jsonb_build_object('name', now()),
    CASE WHEN n <= 25 THEN 'available' ELSE 'unavailable' END,
    CASE WHEN n > 20 THEN '30000000-0000-0000-0000-000000000001'::uuid ELSE NULL END,
    CASE WHEN n BETWEEN 21 AND 25 THEN now() ELSE NULL END,
    CASE WHEN n > 25 THEN now() ELSE NULL END,
    1,
    c.created_at,
    c.updated_at
FROM public.courses c
CROSS JOIN LATERAL (
    SELECT substring(c.slug FROM '[0-9]+$')::integer AS n
) parsed
ON CONFLICT DO NOTHING;
