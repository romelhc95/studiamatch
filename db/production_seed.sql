-- DEBUG: Exportando datos...
-- CATEGORIAS
INSERT INTO public.categories (name, description) VALUES ('General / Por Clasificar', ''),
('Ofim├ítica y Productividad', ''),
('Data Analytics', ''),
('Ciberseguridad', ''),
('Cloud Computing', ''),
('Data Science & IA', ''),
('DevOps & Infraestructura', ''),
('Gesti├│n y Agilidad', ''),
('Redes y Conectividad', ''),
('Desarrollo y Web', ''),
('Tecnolog├¡a', ''),
('Log├¡stica y Operaciones', ''),
('Finanzas y Legal', 'Cursos relacionados a finanzas, contabilidad, leyes y normativas
legales.'),
('Ingenier├¡a y Construcci├│n', 'Cursos de ingenier├¡a civil, industrial, minas, construcci├│n y
afines.'),
('Arte y Dise├▒o Digital', 'Cursos de dise├▒o gr├ífico, UI/UX, animaci├│n, arte y medios
digitales.'),
('Derecho y Humanidades', 'Cursos de derecho, filosof├¡a, ciencias sociales y humanidades.'),
('Marketing y Ventas', 'Cursos de marketing digital, publicidad, estrategias de ventas y
relaciones p├║blicas.'),
('Artes y Cultura', 'Cursos de expresi├│n art├¡stica, m├║sica, teatro, danza y
gesti├│n cultural.') ON CONFLICT (name) DO NOTHING;

-- SALARIOS
INSERT INTO public.market_salaries (category_id, category_name, salary_junior, salary_average, salary_senior)
SELECT c.id, s.cat_name, s.sj, s.sa, s.ss FROM ( VALUES 
('Data Science & IA', 5200, 11500, 18000),
('Ciberseguridad', 4800, 9500, 16000),
('Cloud Computing', 4500, 10000, 17000),
('DevOps & Infraestructura', 4500, 9800, 16500),
('Desarrollo y Web', 3500, 7500, 14000),
('Data Analytics', 3800, 8200, 13000),
('Log├¡stica y Operaciones', 2800, 5800, 11000),
('Finanzas y Legal', 3200, 7200, 15000),
('Ingenier├¡a y Construcci├│n', 3000, 6500, 14000),
('Marketing y Ventas', 2500, 5500, 10000),
('Gesti├│n y Agilidad', 3500, 8500, 15000),
('Redes y Conectividad', 2800, 6000, 11000),
('Ofim├ítica y Productividad', 1200, 2800, 4500),
('Arte y Dise├▒o Digital', 2200, 4800, 9000),
('Derecho y Humanidades', 2500, 5500, 12000),
('Tecnolog├¡a', 3000, 7000, 13000),
('General / Por Clasificar', 1025, 2500, 5000)
) as s(cat_name, sj, sa, ss) JOIN public.categories c ON c.name = s.cat_name ON CONFLICT (category_name) DO NOTHING;
