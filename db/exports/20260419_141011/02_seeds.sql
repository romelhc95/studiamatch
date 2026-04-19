--
-- PostgreSQL database dump
--

\restrict HLzmnGodGWDQwefSv4dWXJwJAYataW8sFzbk8bgFcvsq6r4AkFbaWZOuJuhECYX

-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.categories VALUES ('a850b28a-f0e6-4ecc-97b5-f98af53f7b65', 'General / Por Clasificar', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'OfimÃ¡tica y Productividad', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('31e042f0-1571-4bc7-800e-f63e26820ac0', 'Data Analytics', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('168ae652-21e7-48d2-85f8-53909444043f', 'Ciberseguridad', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('1ad13c48-4a85-4758-8615-38f4fb806422', 'Cloud Computing', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('d10b87c4-7b95-47ed-9b06-74c36435d4e4', 'Data Science & IA', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('ede6aeb8-d2e5-40b4-8433-1fbb967b7dd5', 'DevOps & Infraestructura', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('4a0de3b6-30de-456e-8301-b1c993d99cfc', 'GestiÃ³n y Agilidad', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('b5736c74-180c-4c31-8b00-98644ab7387e', 'Redes y Conectividad', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('56396b45-7eab-40c1-a373-6187069e33a6', 'Desarrollo y Web', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('811644b2-b226-43cd-9a6f-bfca066a1cc2', 'TecnologÃ­a', NULL, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.categories VALUES ('90866a67-9cf3-45e5-ad74-49dc1cd6cef6', 'LogÃ­stica y Operaciones', NULL, '2026-04-14 01:00:30.691177+00');
INSERT INTO public.categories VALUES ('028906bf-aa60-47e2-b11f-382073be8f67', 'Finanzas y Legal', 'Cursos relacionados a finanzas, contabilidad, leyes y normativas
legales.', '2026-04-14 01:55:31.971755+00');
INSERT INTO public.categories VALUES ('778c0a6c-09f0-4702-99fe-f9091c4d3f51', 'IngenierÃ­a y ConstrucciÃ³n', 'Cursos de ingenierÃ­a civil, industrial, minas, construcciÃ³n y
afines.', '2026-04-14 01:55:31.971755+00');
INSERT INTO public.categories VALUES ('7a719c33-5616-4725-bce6-9f8d205a6621', 'Arte y DiseÃ±o Digital', 'Cursos de diseÃ±o grÃ¡fico, UI/UX, animaciÃ³n, arte y medios
digitales.', '2026-04-14 01:55:31.971755+00');
INSERT INTO public.categories VALUES ('1ad2cdc5-1e68-4268-b6c2-8b3c428507f7', 'Derecho y Humanidades', 'Cursos de derecho, filosofÃ­a, ciencias sociales y humanidades.', '2026-04-14 01:55:31.971755+00');
INSERT INTO public.categories VALUES ('69dae276-bd42-47d2-ad2f-5e0bcb9d2e75', 'Marketing y Ventas', 'Cursos de marketing digital, publicidad, estrategias de ventas y
relaciones pÃºblicas.', '2026-04-14 01:55:31.971755+00');
INSERT INTO public.categories VALUES ('b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'Artes y Cultura', 'Cursos de expresiÃ³n artÃ­stica, mÃºsica, teatro, danza y
gestiÃ³n cultural.', '2026-04-14 06:03:10.021325+00');


--
-- Data for Name: category_rules; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.category_rules VALUES ('901ba4cf-806c-4ae9-af5f-a24361aa3c66', '66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'project', 5, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('ad5b1624-0fc3-464f-b7cb-cea8227bc603', '66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'visio', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('30e8c047-d583-4705-9319-1a6d374ee5a8', '66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'outlook', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('9e501867-143f-4883-ba7c-d8f29ebb404a', '66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'powerpoint', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('5b1186ef-e6bd-4643-b9c1-ab9f42d66e13', '66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'word', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('9c170109-14f7-487e-9376-e8c0f5269c86', '66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'excel', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('4309f8b0-3c99-49f5-8639-c9f16fbc5c27', '66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'office', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('f5bdafa4-03de-4c9b-b524-0785224fc0e8', '31e042f0-1571-4bc7-800e-f63e26820ac0', 'analÃ­tica', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('27dd88cf-a5db-4321-8fd0-5fc0da5b06c9', '31e042f0-1571-4bc7-800e-f63e26820ac0', 'analytics', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('67abb732-af54-4d43-a86c-c5361067720b', '31e042f0-1571-4bc7-800e-f63e26820ac0', 'qlik', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('33213e25-548b-4b5c-8b9b-d8419896a082', '31e042f0-1571-4bc7-800e-f63e26820ac0', 'tableau', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('29d59500-1ef7-4895-af56-2b54ffdb46fd', '31e042f0-1571-4bc7-800e-f63e26820ac0', 'power bi', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('5741df5e-dc0a-4e65-8dbe-6c0dd17c5598', '168ae652-21e7-48d2-85f8-53909444043f', 'firewall', 15, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('e54babd7-d3f5-4137-8e9c-932392ef7e6a', '168ae652-21e7-48d2-85f8-53909444043f', 'palo alto', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('6f2b4de9-2d8d-4ccc-ba61-3f67b582a46a', '168ae652-21e7-48d2-85f8-53909444043f', 'fortinet', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('0255712d-aa3c-41f8-9d2c-026dfa8db0db', '168ae652-21e7-48d2-85f8-53909444043f', 'owasp', 30, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('0bca3b7b-64db-4ff0-bac6-a5057cf58d80', '168ae652-21e7-48d2-85f8-53909444043f', 'ciber', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('658e9b88-d0ec-4723-8687-199c858d620b', '168ae652-21e7-48d2-85f8-53909444043f', 'cyber', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('147eb3cd-4636-4447-993d-a2677ce812cf', '168ae652-21e7-48d2-85f8-53909444043f', 'hacking', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('3f2a0127-41b6-422f-9818-7ffd94513606', '168ae652-21e7-48d2-85f8-53909444043f', 'seguridad', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('d966c826-3d92-4305-b461-bc68a7ab637d', '1ad13c48-4a85-4758-8615-38f4fb806422', 'amazon web services', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('56e86aa0-36b3-4fa9-91e3-8d7d5e2ae6cf', '1ad13c48-4a85-4758-8615-38f4fb806422', 'gcp', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('da558937-0f53-42b7-bb8c-1ad58067ccaf', '1ad13c48-4a85-4758-8615-38f4fb806422', 'google cloud', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('1b65af60-1624-4190-b6e2-357c1e626943', '1ad13c48-4a85-4758-8615-38f4fb806422', 'aws', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('a98ae3a0-c423-433e-b01b-1343f0081d37', '1ad13c48-4a85-4758-8615-38f4fb806422', 'azure', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('51e57283-ae2f-409a-9b4a-4f272dc8bc9a', '1ad13c48-4a85-4758-8615-38f4fb806422', 'cloud', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('fe04d48e-c359-42e6-94e0-aa68ffb9a1ef', 'd10b87c4-7b95-47ed-9b06-74c36435d4e4', 'python for data', 25, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('b31d32fc-990c-4bc6-9267-97d9e75a8b66', 'd10b87c4-7b95-47ed-9b06-74c36435d4e4', 'deep learning', 30, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('dfa86399-c502-444e-9c3e-03a6e2487ef9', 'd10b87c4-7b95-47ed-9b06-74c36435d4e4', 'machine learning', 30, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('2e837c3c-b502-43d4-a8f4-0fedb9e69dad', 'd10b87c4-7b95-47ed-9b06-74c36435d4e4', 'artificial', 15, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('5b6371fc-7d55-482a-a275-2363c099ea8c', 'd10b87c4-7b95-47ed-9b06-74c36435d4e4', 'datos', 5, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('c4196ad2-ee61-4f85-bcea-541e09749138', 'd10b87c4-7b95-47ed-9b06-74c36435d4e4', 'data', 5, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('aacc7809-f152-46d8-84c2-cafdfb9537c2', 'ede6aeb8-d2e5-40b4-8433-1fbb967b7dd5', 'ansible', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('f2bdcbed-0f20-4347-b967-0bf2ab32cc09', 'ede6aeb8-d2e5-40b4-8433-1fbb967b7dd5', 'terraform', 25, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('6f1ae9aa-83c7-4d87-a4fe-c9160675c1e3', 'ede6aeb8-d2e5-40b4-8433-1fbb967b7dd5', 'jenkins', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('f18fd120-2dcb-4334-8e37-9656190bbe94', 'ede6aeb8-d2e5-40b4-8433-1fbb967b7dd5', 'kubernetes', 30, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('ad0513b8-3e84-4a04-a1d9-20b27486dee1', 'ede6aeb8-d2e5-40b4-8433-1fbb967b7dd5', 'docker', 25, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('6cd824c8-4a23-4d00-a4ff-416c723a2486', 'ede6aeb8-d2e5-40b4-8433-1fbb967b7dd5', 'devops', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('9833312c-470a-43ed-9411-c27e3528237e', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'liderazgo', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('61965cc5-5594-473d-975f-8dba13e4e981', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'management', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('9c71297d-c221-4399-8ed8-52d0ed2f0d3d', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'gestion', 5, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('a5b363eb-d58f-48b6-9952-4b1e9989864e', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'gestiÃ³n', 5, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('1c6f35b9-ccde-492f-b793-6d8c7649d9dc', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'pmp', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('39210c27-51cf-4f11-9685-1314423064ed', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'itil', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('bca287ea-b2aa-4a45-9fcd-31aeb380ed50', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'scrum', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('cac0f1e7-b540-40ce-a360-24a3fa3684e9', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'agil', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('61d19a3d-fc8a-4e45-b3dc-53b951b22718', 'b5736c74-180c-4c31-8b00-98644ab7387e', 'switching', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('b9e5b2e6-b883-440f-aa38-7f63249a1a37', 'b5736c74-180c-4c31-8b00-98644ab7387e', 'routing', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('37cc427f-11fc-4f25-bc18-857e60e08aa1', 'b5736c74-180c-4c31-8b00-98644ab7387e', 'ccnp', 30, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('7fb6a0a7-e82e-4a48-b92c-e3544ab8be7f', 'b5736c74-180c-4c31-8b00-98644ab7387e', 'ccna', 30, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('c95f868f-dc08-4461-8bb5-138b9dd4d41c', 'b5736c74-180c-4c31-8b00-98644ab7387e', 'network', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('7f3bf604-1d9f-4d10-9031-11ab98bb90b7', 'b5736c74-180c-4c31-8b00-98644ab7387e', 'redes', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('93087635-0114-46e2-a36c-4421824cd84f', 'b5736c74-180c-4c31-8b00-98644ab7387e', 'cisco', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('3b853600-5b80-4833-85d1-a15eca7fe1cb', '56396b45-7eab-40c1-a373-6187069e33a6', 'node', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('30affb2f-6c87-4a5b-9dfa-c0a2b9db499a', '56396b45-7eab-40c1-a373-6187069e33a6', 'vue', 25, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('2c37824c-914b-4c09-b6f4-2e3c59922a51', '56396b45-7eab-40c1-a373-6187069e33a6', 'angular', 25, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('64dd2a7c-d46d-4cca-84a5-083baf6af120', '56396b45-7eab-40c1-a373-6187069e33a6', 'fullstack', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('b04c0252-b088-4602-a58e-66f1d0533945', '56396b45-7eab-40c1-a373-6187069e33a6', 'backend', 15, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('d5bca124-126e-41be-9bcb-bab5ffab7435', '56396b45-7eab-40c1-a373-6187069e33a6', 'frontend', 15, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('881ff9d6-59c5-47d7-8224-e5baa34d12a1', '56396b45-7eab-40c1-a373-6187069e33a6', 'web', 5, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('d2f55fa5-3b3e-4138-9470-45cc331e0d41', '56396b45-7eab-40c1-a373-6187069e33a6', 'programaciÃ³n', 5, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('dbac88aa-68cc-4195-8016-5cfa3ee58189', '56396b45-7eab-40c1-a373-6187069e33a6', 'desarrollo', 5, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('78b1ca1a-5c67-41b4-8d78-98eecde28b90', '56396b45-7eab-40c1-a373-6187069e33a6', 'react', 25, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('2d3815af-62af-4e51-a23c-f53b35d3a9e8', '56396b45-7eab-40c1-a373-6187069e33a6', 'javascript', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('cf8b09d4-03b1-4b74-8a44-7c689d293212', '56396b45-7eab-40c1-a373-6187069e33a6', 'php', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('ae03788c-bc89-401f-b203-e9ebcd509ebe', '56396b45-7eab-40c1-a373-6187069e33a6', 'python', 10, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('e5820820-be17-4e97-b626-b18e54fe46af', '56396b45-7eab-40c1-a373-6187069e33a6', 'java', 20, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('28185533-ef5e-4ebf-a687-c9a0772eb21c', '90866a67-9cf3-45e5-ad74-49dc1cd6cef6', 'supply chain', 30, '2026-04-14 01:04:34.674829+00');
INSERT INTO public.category_rules VALUES ('af358978-38a6-4eb8-afaa-afe0a7a22019', '90866a67-9cf3-45e5-ad74-49dc1cd6cef6', 'logÃ­stica', 30, '2026-04-14 01:04:34.674829+00');
INSERT INTO public.category_rules VALUES ('9b41fb32-6614-42eb-a331-a759e9e9a7a0', '90866a67-9cf3-45e5-ad74-49dc1cd6cef6', 'operaciones', 25, '2026-04-14 01:04:34.674829+00');
INSERT INTO public.category_rules VALUES ('94e82d1c-7014-45c4-bc2f-2df077151077', '90866a67-9cf3-45e5-ad74-49dc1cd6cef6', 'almacÃ©n', 25, '2026-04-14 01:04:34.674829+00');
INSERT INTO public.category_rules VALUES ('3670e52b-f333-4663-9622-cead97775492', '90866a67-9cf3-45e5-ad74-49dc1cd6cef6', 'distribuciÃ³n', 25, '2026-04-14 01:04:34.674829+00');
INSERT INTO public.category_rules VALUES ('590f2311-5353-48dc-806d-6fb7a683a6ec', '028906bf-aa60-47e2-b11f-382073be8f67', 'finanzas', 20, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('72956f8b-fdce-4bb0-8b39-8455b71e0b23', '028906bf-aa60-47e2-b11f-382073be8f67', 'contabilidad', 20, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('5caa18ae-ef87-49fa-9844-a18c2334e21c', '028906bf-aa60-47e2-b11f-382073be8f67', 'tributario', 25, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('6ce429a2-57ab-4357-aefc-81da70047c5a', '028906bf-aa60-47e2-b11f-382073be8f67', 'niif', 30, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('9f30dede-db64-40ac-b878-85a300d9f720', '778c0a6c-09f0-4702-99fe-f9091c4d3f51', 'ingenierÃ­a', 15, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('94b7edd1-a373-4769-a332-b78eafa7bc5a', '778c0a6c-09f0-4702-99fe-f9091c4d3f51', 'construcciÃ³n', 20, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('a5156631-9b72-43e6-9e19-39ccee387565', '778c0a6c-09f0-4702-99fe-f9091c4d3f51', 'civil', 20, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('3d8fb499-a6c2-49db-9a28-9252d129dfe0', '7a719c33-5616-4725-bce6-9f8d205a6621', 'diseÃ±o', 25, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('15cd27ca-48ea-44cd-8591-e9fe80e0ac42', '7a719c33-5616-4725-bce6-9f8d205a6621', 'ui/ux', 30, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('2b69f063-efb8-436a-92de-a711e91539bc', '7a719c33-5616-4725-bce6-9f8d205a6621', 'stop motion', 30, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('2d6db309-be3a-49c8-bffe-f792e03403c8', '1ad2cdc5-1e68-4268-b6c2-8b3c428507f7', 'derecho', 20, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('0081b8b9-a231-4810-a92e-dec846e93f79', '1ad2cdc5-1e68-4268-b6c2-8b3c428507f7', 'bioÃ©tica', 25, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('f1ae27ca-8df9-41b6-9fcf-2b42abb05995', '1ad2cdc5-1e68-4268-b6c2-8b3c428507f7', 'humanidades', 15, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('c3d885e5-dde9-4466-84cf-dea125d555c9', '1ad2cdc5-1e68-4268-b6c2-8b3c428507f7', 'sociologÃ­a', 20, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('f5a8d1d3-2598-4ec0-aa83-eea87b7ce2ff', '69dae276-bd42-47d2-ad2f-5e0bcb9d2e75', 'marketing', 20, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('38848b03-a5bd-4c18-a680-f03dece145b6', '69dae276-bd42-47d2-ad2f-5e0bcb9d2e75', 'ventas', 20, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('a3100846-9697-4df9-be2a-879ea04b8249', '69dae276-bd42-47d2-ad2f-5e0bcb9d2e75', 'seo', 30, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('a24784ba-4669-40ec-ae47-5c41f85aa848', '69dae276-bd42-47d2-ad2f-5e0bcb9d2e75', 'redes sociales', 25, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('6d1dabe4-c6b3-4050-96d8-c88a09a08412', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'agilidad', 25, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('37a82ceb-f5cb-4dc7-ae63-7d05b12be07d', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'agile', 25, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('6fff3a47-d6f8-4c9a-89a3-b61d5ac02330', '31e042f0-1571-4bc7-800e-f63e26820ac0', 'sql server', 30, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('1ed61fba-6563-43f5-b8f0-5d656a1d3a0e', '56396b45-7eab-40c1-a373-6187069e33a6', 'rpa', 30, '2026-04-14 01:55:31.971755+00');
INSERT INTO public.category_rules VALUES ('9e988e1c-7241-4d9b-8ab4-daa5011e60e8', 'd10b87c4-7b95-47ed-9b06-74c36435d4e4', ' IA ', 15, '2026-04-13 19:44:36.923137+00');
INSERT INTO public.category_rules VALUES ('9b5b97ac-82af-46e4-89c9-74b2264c6ba7', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'canto', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('abdb014d-ebe9-4a39-9182-7b72ff7f88ad', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'vocal', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('277dcb50-1b10-4c58-b2fa-f85bd18c5adb', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'teatro', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('9b30debf-8de4-4c1b-9fee-6a8a1440eaad', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'musical', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('5b069a29-9697-4cd1-b727-a27fb24e2149', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'escena', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('d5cae246-251c-4189-a6d9-1bfb6539786a', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'actuaciÃ³n', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('04c4576c-80c8-4ede-8366-52b83023de1a', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'danza', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('9b2b065d-0af7-4773-8b8c-c831e5e2e3f8', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'canciones', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('20198794-d23e-46bc-a6fa-bcb054dbb617', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'composiciÃ³n', 50, '2026-04-14 06:03:10.021325+00');
INSERT INTO public.category_rules VALUES ('b3bd7de1-511d-4156-8473-da01a87ef9ae', 'b8f45f46-f09f-4ea0-9b43-f7323d142fce', 'mÃºsica', 50, '2026-04-14 06:03:10.021325+00');


--
-- Data for Name: institutions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.institutions VALUES ('ccd04100-1bde-427b-b94f-ab24ae233a2a', 'Universidad de Lima', 'universidad-de-lima', 'https://www.ulima.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:43.897391+00', '2026-04-14 07:23:43.897391+00');
INSERT INTO public.institutions VALUES ('cf64d254-733d-4a92-8a2d-5df5b9dc80ac', 'Universidad del PacÃ­fico', 'universidad-del-pacÃ­fico', 'https://www.up.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:45.441576+00', '2026-04-14 07:23:45.441576+00');
INSERT INTO public.institutions VALUES ('2aa0d175-bfbd-46d0-b84c-14083d2336b0', 'IDAT', 'idat', 'https://www.idat.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:46.876087+00', '2026-04-14 07:23:46.876087+00');
INSERT INTO public.institutions VALUES ('7091517e-db4f-4f91-a822-db50974acbba', 'SENATI', 'senati', 'https://www.senati.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:48.241621+00', '2026-04-14 07:23:48.241621+00');
INSERT INTO public.institutions VALUES ('442d7f1c-c6fe-4c85-8f0d-68cc55993193', 'UPC', 'upc', 'https://www.upc.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:49.172956+00', '2026-04-14 07:23:49.172956+00');
INSERT INTO public.institutions VALUES ('755ce274-f7cd-44d7-985c-817f80f5f38e', 'USIL', 'usil', 'https://www.usil.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:50.131421+00', '2026-04-14 07:23:50.131421+00');
INSERT INTO public.institutions VALUES ('ba945423-f295-434d-9082-48c726b0fe8e', 'Universidad Continental', 'universidad-continental', 'https://ucontinental.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:51.212955+00', '2026-04-14 07:23:51.212955+00');
INSERT INTO public.institutions VALUES ('556c359b-55ec-4c1a-b6a5-177c6983da25', 'UTP', 'utp', 'https://www.utp.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:52.15482+00', '2026-04-14 07:23:52.15482+00');
INSERT INTO public.institutions VALUES ('48177d13-e476-468f-99f3-87371b4a1bae', 'UNMSM', 'unmsm', 'https://unmsm.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:53.083445+00', '2026-04-14 07:23:53.083445+00');
INSERT INTO public.institutions VALUES ('fb5c5e61-1afc-4dc4-b771-d3595ed329c2', 'UNI', 'uni', 'https://www.uni.edu.pe/', NULL, NULL, NULL, '2026-04-14 07:23:54.027764+00', '2026-04-14 07:23:54.027764+00');
INSERT INTO public.institutions VALUES ('24cc140d-de25-4ef1-9316-b897b451be50', 'New Horizons PerÃº', 'new-horizons-peru', 'https://www.newhorizons.edu.pe/', NULL, NULL, NULL, '2026-04-14 08:24:13.344695+00', '2026-04-14 08:24:13.344695+00');
INSERT INTO public.institutions VALUES ('b3969350-3df5-44c1-85c5-787cbb877494', 'Pontificia Universidad CatÃ³lica del PerÃº', 'pucp', 'https://www.pucp.edu.pe/', NULL, NULL, NULL, '2026-04-14 08:29:40.660251+00', '2026-04-14 08:29:40.660251+00');
INSERT INTO public.institutions VALUES ('5e3257be-1c70-457d-98d8-191a5b964045', 'SmartData', 'smartdata', 'https://smartdata.com.pe/', NULL, NULL, 'Remoto / Lima', '2026-04-14 08:31:29.936319+00', '2026-04-14 08:31:29.936319+00');
INSERT INTO public.institutions VALUES ('c64123d6-f00e-4c89-86a8-7706845c0483', 'DMC', 'dmc', 'https://dmc.pe/', NULL, NULL, NULL, '2026-04-16 18:29:06.414283+00', '2026-04-16 18:29:06.414283+00');
INSERT INTO public.institutions VALUES ('4385b2a0-f456-482f-8754-f68b50b74a7f', 'TEST-ADAPTER-PATCHED', 'test-slug-4385b2a0-f456-482f-8754-f68b50b74a7f', 'http://test.com', NULL, NULL, NULL, NULL, NULL);


--
-- Data for Name: crawler_exclusions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.crawler_exclusions VALUES ('448bd772-7712-4dc3-9050-a79e4e40bec3', NULL, '/medios/', 'InformaciÃ³n mediÃ¡tica', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('2dc24307-01f5-41bc-95d2-7cccd3d97e73', NULL, '/noticias/', 'Noticias institucionales', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('27c2bf11-21b0-4576-9f57-c2f855749fdb', NULL, '/programas-patrocinio', 'InformaciÃ³n patrocinadora', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('dcaf645e-ee28-427f-bdcf-9b8fc0ab20e0', NULL, '/modalidades-de-admisiÃ³n-para-programas-de-formaciÃ³n', 'InformaciÃ³n de admisiÃ³n informativa', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('e1eb328d-6b50-4ca9-997f-452ed6809140', NULL, '/logros-uc/', 'Logros institucionales (UC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('532ea3a9-4a5b-4438-83d8-a492207bac7e', NULL, '/eventos/', 'Eventos institucionales', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('ea1660af-0062-4026-8308-65887962acde', NULL, '/uc-global/', 'Movilidad estudiantil (UC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('7e53d0fe-5361-4211-8f32-b6ccea4f37c9', NULL, '/sostenibilidad/', 'Impacto social', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('d2cc169a-e525-4671-ba6e-bbdfb67adbf1', NULL, '/oportunidades-laborales/', 'Bolsa de trabajo', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('04bdd552-e561-4745-92cb-ec179186d4df', NULL, '/programa-training/', 'Noticiero training (UC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('a76e7323-8b3d-491c-bebf-3fc038b895aa', NULL, '/beca-18/', 'InformaciÃ³n de becas estatales', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('0b23d1cc-e1f0-4c9d-988e-59eca18637cd', NULL, '/beca/', 'InformaciÃ³n de becas generales', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('c294ac59-dab1-4886-ba67-85794275b8b2', NULL, '/malla-curricular/', 'SecciÃ³n sin oferta acadÃ©mica (DMC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('a2b2c149-73b0-4d3f-9b4c-d0fbcdece394', NULL, '/producto/', 'InformaciÃ³n de producto genÃ©rico (DMC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('a02c4677-d287-44d2-a02c-ad0ed9001255', NULL, '/categoria-pregunta/', 'Dudas/FAQ (DMC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('f21e64e3-76c8-400b-8086-6589e1a514d3', NULL, '/convocatorias-investigacion/', 'InvestigaciÃ³n acadÃ©mica', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('c264fc88-bb1e-4f26-ad52-042c6b9c29d7', NULL, '/blog/', 'ArtÃ­culos de blog', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('33d2bab2-6ddb-4646-a3ab-d48d654c053d', NULL, '/novedades-utp/', 'Noticiero UTP', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('b5bbd3b0-0c84-450c-9f26-2333c290977c', NULL, '/perfil-curso/', 'GeneralizaciÃ³n de especialidad (DMC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('3bb3b025-d4d8-4374-be72-1c70ede0a2bb', NULL, '/la-universidad/', 'InformaciÃ³n corporativa', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('5a175fc2-c36f-491d-a7ee-d0c3db6ad1e5', NULL, '/servicio/', 'Beneficios alumnos/profesores', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('6e1b1c2b-5a9d-47d8-a072-9bc8395a92d9', NULL, '/documento/', 'Reglamento interno', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('dcf967c3-abc2-46c9-82af-07b5c1592a86', NULL, '/categoria-producto/', 'CatÃ¡logo genÃ©rico (DMC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('be238cfe-b97b-42f1-8f20-615d1c812584', NULL, '/ruta-de-aprendizaje/', 'InformaciÃ³n de rutas (DMC)', '2026-04-19 16:53:05.844934+00', true);
INSERT INTO public.crawler_exclusions VALUES ('bc5a3f40-ccbf-4466-a6c9-8c30b202fb73', NULL, '/nuevo-reglamento/', 'InformaciÃ³n administrativa de reglamentos', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('27ed6ba8-b53e-4ec1-8c71-77b6ce2abbab', NULL, '/centro-cultural/', 'Actividades culturales no acadÃ©micas', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('d1f8286b-1f77-45ae-b408-3fa28c450f4d', NULL, '/sin-categoria/', 'Contenido no clasificado/basura', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('3556543d-b682-49fc-a41d-524c691df522', NULL, 'categorias-cursos', 'PÃ¡gina de Ã­ndice de categorÃ­as (UP)', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('9072f2c2-448e-499c-8029-ddf3679e69be', NULL, '/oficina-de-consejeria-academica/', 'Servicios de apoyo estudiantil', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('7f75c212-0f91-4888-92ff-382f2427ba89', NULL, '/recursos-para-la-virtualizacion/', 'Herramientas docentes', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('d59dfa4f-6aea-4095-a899-70a14b9c3e69', NULL, '/responsabilidad-social/', 'Actividades de impacto social', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('ed215c24-80ac-4f48-96fd-6cc2824652da', NULL, '/revistas-informativas-prosuc/', 'Contenido editorial/informativo', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('9843436e-9c25-4899-92fa-4086b83339c1', NULL, '/pregunta-frecuente/', 'FAQ/Ayuda', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('f7f09a5b-9745-494a-b77b-7c13949a0231', NULL, '/educacion-a-distancia/', 'InformaciÃ³n sobre modalidad, no curso', '2026-04-19 17:52:58.051329+00', true);
INSERT INTO public.crawler_exclusions VALUES ('225782c3-4406-46c0-96ba-1351439e5e05', NULL, '/programa-global-classroom/', 'Landing page genÃ©rica de la UC', '2026-04-19 18:10:56.452973+00', true);


--
-- Data for Name: market_salaries; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.market_salaries VALUES ('9461d42c-6a68-4f47-b163-6df5f3c2f800', 'd10b87c4-7b95-47ed-9b06-74c36435d4e4', 'Data Science & IA', 5200, 11500, 18000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('d45455b7-3d48-4664-8857-bfe9a19319b1', '168ae652-21e7-48d2-85f8-53909444043f', 'Ciberseguridad', 4800, 9500, 16000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('2adcd46c-20a6-4fd4-bac8-91122927e94a', '1ad13c48-4a85-4758-8615-38f4fb806422', 'Cloud Computing', 4500, 10000, 17000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('8f6e35e3-3cd1-41c3-8631-4dbe3c45670b', 'ede6aeb8-d2e5-40b4-8433-1fbb967b7dd5', 'DevOps & Infraestructura', 4500, 9800, 16500, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('a7a7b5b3-2a2c-4c21-b767-46665f493387', '56396b45-7eab-40c1-a373-6187069e33a6', 'Desarrollo y Web', 3500, 7500, 14000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('22fe3c90-4d06-446b-ac07-396c1dbe1170', '31e042f0-1571-4bc7-800e-f63e26820ac0', 'Data Analytics', 3800, 8200, 13000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('ec5759d9-a08c-415a-b88b-219aa2bf6418', '90866a67-9cf3-45e5-ad74-49dc1cd6cef6', 'LogÃ­stica y Operaciones', 2800, 5800, 11000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('9eec68b1-fb70-48c7-97dd-c8db47e5f4b2', '028906bf-aa60-47e2-b11f-382073be8f67', 'Finanzas y Legal', 3200, 7200, 15000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('c8a9e205-cdd1-4946-9c45-096558742392', '778c0a6c-09f0-4702-99fe-f9091c4d3f51', 'IngenierÃ­a y ConstrucciÃ³n', 3000, 6500, 14000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('63d75c85-27d8-4476-8524-0f7fbe112bdf', '69dae276-bd42-47d2-ad2f-5e0bcb9d2e75', 'Marketing y Ventas', 2500, 5500, 10000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('24e875a7-85be-48a7-abe0-fdb30413c34f', '4a0de3b6-30de-456e-8301-b1c993d99cfc', 'GestiÃ³n y Agilidad', 3500, 8500, 15000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('39aa752d-25f2-4243-a7d3-dad2c5bcad3f', 'b5736c74-180c-4c31-8b00-98644ab7387e', 'Redes y Conectividad', 2800, 6000, 11000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('7009c0e7-312c-4034-9325-2fce50fe9ec2', '66de1f7c-6c06-4732-add8-4b7fa2e624bb', 'OfimÃ¡tica y Productividad', 1200, 2800, 4500, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('412df693-3eaf-4188-bb9a-8f3b8018db59', '7a719c33-5616-4725-bce6-9f8d205a6621', 'Arte y DiseÃ±o Digital', 2200, 4800, 9000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('d6dbe6ed-bbee-45c5-ada8-b3cc859461a0', '1ad2cdc5-1e68-4268-b6c2-8b3c428507f7', 'Derecho y Humanidades', 2500, 5500, 12000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('bb89b339-d741-4bab-bf31-829d6208114e', '811644b2-b226-43cd-9a6f-bfca066a1cc2', 'TecnologÃ­a', 3000, 7000, 13000, '2026-04-14 05:28:07.683141+00');
INSERT INTO public.market_salaries VALUES ('fedf5cfd-85f4-494c-b7a1-f42052a98ab6', 'a850b28a-f0e6-4ecc-97b5-f98af53f7b65', 'General / Por Clasificar', 1025, 2500, 5000, '2026-04-14 05:28:07.683141+00');


--
-- PostgreSQL database dump complete
--

\unrestrict HLzmnGodGWDQwefSv4dWXJwJAYataW8sFzbk8bgFcvsq6r4AkFbaWZOuJuhECYX

