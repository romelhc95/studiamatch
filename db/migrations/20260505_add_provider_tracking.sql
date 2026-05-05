-- Fase 79A: Add provider tracking columns to enriched_programs and courses
-- Permite distinguir datos enriquecidos por LLM real vs smart mock

ALTER TABLE enriched_programs ADD COLUMN IF NOT EXISTS provider_used TEXT DEFAULT 'mock';
ALTER TABLE enriched_programs ADD COLUMN IF NOT EXISTS is_mock_data BOOLEAN DEFAULT true;

ALTER TABLE courses ADD COLUMN IF NOT EXISTS provider_used TEXT DEFAULT 'mock';
ALTER TABLE courses ADD COLUMN IF NOT EXISTS is_mock_data BOOLEAN DEFAULT true;
