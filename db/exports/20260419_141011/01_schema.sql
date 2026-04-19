--
-- PostgreSQL database dump
--

\restrict xcGsmKhzzslJc0jXAmcbEZxGjoh6HbWw6YCcB2ZVIz7Z10ZRHMPXdvPI1Vr0Q4f

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
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id uuid,
    name text,
    description text,
    created_at timestamp with time zone
);


--
-- Name: category_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.category_rules (
    id uuid,
    category_id uuid,
    keyword text,
    priority integer,
    created_at timestamp with time zone
);


--
-- Name: cleansed_programs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cleansed_programs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    staging_id uuid,
    institution_id uuid,
    url text,
    clean_name text,
    clean_description text,
    modality text,
    location text,
    base_price numeric,
    currency text,
    status text,
    metadata jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: courses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.courses (
    id uuid,
    institution_id uuid,
    name text,
    slug text,
    price_pen numeric,
    mode text,
    address text,
    duration text,
    category text,
    url text,
    syllabus text,
    target_audience text,
    requirements text,
    certification text,
    benefits text,
    expected_monthly_salary numeric,
    last_scraped_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    description_long text,
    objectives text,
    price_status text,
    course_type text,
    brochure_url text,
    brochure_text text,
    is_active boolean,
    start_date_text text,
    category_id uuid,
    category_confirmed boolean,
    last_404_at timestamp with time zone,
    seniority_level text,
    roi_months numeric,
    is_verified boolean,
    embedding text
);


--
-- Name: crawler_exclusions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crawler_exclusions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    institution_id uuid,
    pattern text NOT NULL,
    reason text,
    created_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true
);


--
-- Name: enriched_programs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.enriched_programs (
    id uuid,
    cleansed_id uuid,
    institution_id uuid,
    url text,
    official_name text,
    duration_text text,
    duration_months integer,
    total_cost_est numeric,
    requirements text,
    graduate_profile text,
    curriculum_summary jsonb,
    modality text,
    primary_campus text,
    degree_type text,
    start_date text,
    partnerships text,
    certifications text,
    language text,
    categories text,
    ai_summary text,
    embedding text,
    status text,
    metadata jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    difficulty_level text
);


--
-- Name: institutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.institutions (
    id uuid NOT NULL,
    name text,
    slug text,
    website_url text,
    location_lat numeric,
    location_long numeric,
    address text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: leads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.leads (
    id uuid,
    first_name text,
    last_name text,
    email text,
    whatsapp text,
    type text,
    course_id uuid,
    area_interest text,
    budget numeric,
    modality text,
    description text,
    status text,
    created_at timestamp with time zone
);


--
-- Name: market_salaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.market_salaries (
    id uuid,
    category_id uuid,
    category_name text,
    salary_junior numeric,
    salary_average numeric,
    salary_senior numeric,
    last_updated timestamp with time zone
);


--
-- Name: ratings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ratings (
    id uuid,
    course_id uuid,
    rating_value integer,
    user_nickname text,
    created_at timestamp with time zone
);


--
-- Name: reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reviews (
    id uuid,
    course_id uuid,
    content text,
    user_nickname text,
    created_at timestamp with time zone
);


--
-- Name: staging_raw; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.staging_raw (
    id uuid DEFAULT gen_random_uuid(),
    institution_id uuid,
    url text,
    raw_name text,
    raw_description text,
    raw_html text,
    raw_json_ld jsonb,
    raw_og_tags jsonb,
    status text,
    discard_reason text,
    processing_error text,
    last_harvested_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    content_hash text,
    html_content text,
    metadata jsonb
);


--
-- Name: cleansed_programs cleansed_programs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleansed_programs
    ADD CONSTRAINT cleansed_programs_pkey PRIMARY KEY (id);


--
-- Name: cleansed_programs cleansed_programs_url_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleansed_programs
    ADD CONSTRAINT cleansed_programs_url_unique UNIQUE (url);


--
-- Name: crawler_exclusions crawler_exclusions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crawler_exclusions
    ADD CONSTRAINT crawler_exclusions_pkey PRIMARY KEY (id);


--
-- Name: institutions institutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institutions
    ADD CONSTRAINT institutions_pkey PRIMARY KEY (id);


--
-- Name: staging_raw staging_raw_url_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staging_raw
    ADD CONSTRAINT staging_raw_url_unique UNIQUE (url);


--
-- Name: crawler_exclusions crawler_exclusions_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crawler_exclusions
    ADD CONSTRAINT crawler_exclusions_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id);


--
-- PostgreSQL database dump complete
--

\unrestrict xcGsmKhzzslJc0jXAmcbEZxGjoh6HbWw6YCcB2ZVIz7Z10ZRHMPXdvPI1Vr0Q4f

