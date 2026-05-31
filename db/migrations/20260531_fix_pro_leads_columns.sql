-- Fix: Pro leads table missing columns sent by frontend forms
-- The CourseDetailClient.tsx and HomeContent.tsx send extra fields
-- that didn't exist in Pro's leads table (only in Free).

ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS source_page TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS area_interest TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS budget NUMERIC;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS modality TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS is_late_enrollment_request BOOLEAN DEFAULT false;
