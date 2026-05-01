-- Migration: 20260413_social_proof.sql
-- Description: Creates ratings and reviews tables for the Social Proof System with RLS policies

-- 1. Create the 'ratings' table
CREATE TABLE IF NOT EXISTS public.ratings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID NOT NULL,
    rating_value INTEGER NOT NULL CHECK (rating_value >= 1 AND rating_value <= 5),
    user_nickname VARCHAR(255) NOT NULL CHECK (char_length(TRIM(user_nickname)) > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Create the 'reviews' table
CREATE TABLE IF NOT EXISTS public.reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID NOT NULL,
    content TEXT NOT NULL CHECK (char_length(TRIM(content)) > 0),
    user_nickname VARCHAR(255) NOT NULL CHECK (char_length(TRIM(user_nickname)) > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Configure RLS Policies
-- Enable Row Level Security (RLS) on both tables
ALTER TABLE public.ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

-- Allow public read access (SELECT) for everyone
CREATE POLICY "Allow public read access on ratings" ON public.ratings FOR SELECT USING (true);
CREATE POLICY "Allow public read access on reviews" ON public.reviews FOR SELECT USING (true);

-- Allow public insert with basic validation
-- Database level CHECK constraints already handle base validation.
-- Here we re-verify them at policy level for safety, ensuring an anonymous user can insert valid data.
CREATE POLICY "Allow public insert on ratings" ON public.ratings FOR INSERT WITH CHECK (
    rating_value >= 1 AND rating_value <= 5 AND char_length(TRIM(user_nickname)) > 0
);

CREATE POLICY "Allow public insert on reviews" ON public.reviews FOR INSERT WITH CHECK (
    char_length(TRIM(content)) > 0 AND char_length(TRIM(user_nickname)) > 0
);
