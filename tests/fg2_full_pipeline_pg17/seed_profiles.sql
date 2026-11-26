\set ON_ERROR_STOP on

DELETE FROM public.institutions WHERE slug = 'h3-synthetic';

INSERT INTO public.institutions (id, name, slug, website_url)
VALUES
  ('20000000-0000-0000-0000-000000000001', 'Fixture SSR Institute', 'fg2-ssr-onboard', 'https://ssr.fg2.example'),
  ('20000000-0000-0000-0000-000000000002', 'Fixture SPA Institute', 'fg2-spa', 'https://spa.fg2.example'),
  ('20000000-0000-0000-0000-000000000003', 'Fixture Commerce Institute', 'fg2-ecommerce', 'https://ecommerce.fg2.example'),
  ('20000000-0000-0000-0000-000000000004', 'Fixture Blocked Institute', 'fg2-blocked', 'https://blocked.fg2.example'),
  ('20000000-0000-0000-0000-000000000005', 'Fixture Ambiguous Institute', 'fg2-ambiguous', 'https://ambiguous.fg2.example');

INSERT INTO public.institution_site_profiles (
  institution_id, pipeline_ready, pipeline_enabled, discovery_enabled,
  production_enabled, website_url, site_type, discovery_mode, seed_urls,
  allowed_url_patterns, exclusion_patterns, allowed_resource_origins,
  catalog_url_patterns, catalog_max_pages, catalog_scroll_iterations,
  catalog_link_selector, field_defaults, section_keywords, profile_status,
  diagnostic_status, auto_generated, requires_stealth, requires_cloudflare_bypass,
  detail_wait_ms
)
VALUES
  (
    '20000000-0000-0000-0000-000000000002', false, true, true,
    false, 'https://spa.fg2.example', 'spa_js_heavy', 'catalog_link_extraction',
    '["https://spa.fg2.example/catalogo/"]'::jsonb,
    '["re:^/programas/"]'::jsonb, '[]'::jsonb, '[]'::jsonb,
    '[]'::jsonb, 1, 1, 'a.program',
    '{"price_status":"publicado"}'::jsonb,
    '{"Requisitos":"requirements","Objetivos":"objectives"}'::jsonb,
    'active', 'verified', false, false, false, 0
  ),
  (
    '20000000-0000-0000-0000-000000000003', false, true, true,
    false, 'https://ecommerce.fg2.example', 'ecommerce', 'paginated_catalog',
    '[]'::jsonb,
    '["re:^/programas/"]'::jsonb, '[]'::jsonb, '[]'::jsonb,
    '["https://ecommerce.fg2.example/catalogo/?page={page}"]'::jsonb,
    2, 0, '.product-card a',
    '{"price_status":"publicado","mode":"Presencial"}'::jsonb,
    '{"Requisitos":"requirements","Objetivos":"objectives"}'::jsonb,
    'active', 'verified', false, false, false, 0
  ),
  (
    '20000000-0000-0000-0000-000000000004', false, true, true,
    false, 'https://blocked.fg2.example', 'traditional_ssr', 'sitemap_bfs',
    '[]'::jsonb,
    '[]'::jsonb, '[]'::jsonb, '[]'::jsonb,
    '[]'::jsonb, 1, 0, NULL,
    '{"price_status":"publicado"}'::jsonb,
    '{}'::jsonb,
    'active', 'verified', false, false, false, 0
  );

INSERT INTO auth.users (id, email)
VALUES ('30000000-0000-0000-0000-000000000001', 'fixture-admin@fg2.invalid');
