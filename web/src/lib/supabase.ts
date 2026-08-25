// Centralized Supabase Configuration
// All frontend components should import from here.

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY?.trim();

if (!supabaseUrl) {
  throw new Error("Missing required environment variable NEXT_PUBLIC_SUPABASE_URL.");
}

if (
  !supabasePublishableKey?.startsWith("sb_publishable_") ||
  supabasePublishableKey.length <= "sb_publishable_".length
) {
  throw new Error("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY must start with sb_publishable_.");
}

export const SUPABASE_URL = supabaseUrl;
export const SUPABASE_PUBLISHABLE_KEY = supabasePublishableKey;

// Fase 80A: Columnas públicas de courses — explícitas, sin internals (provider_used, is_mock_data, last_scraped_at, etc.)
export const COURSE_PUBLIC_FIELDS = 'id,institution_id,category_id,name,slug,url,price_pen,price_status,mode,duration,description_long,syllabus,target_audience,requirements,certification,benefits,objectives,start_date,start_date_text,course_type,brochure_url,expected_monthly_salary,seniority_level,roi_months,view_count,comparison_count,editorial_status,quality_status,missing_fields,field_sources,field_timestamps,is_sponsored,lead_cta_enabled,sponsored_priority,sponsorship_label,availability_status,created_at,updated_at,editorial_updated_at';

export interface Course {
  id: string;
  name: string;
  slug: string;
  institution_name: string;
  institution_slug?: string;
  price_pen: number | null;
  price_status?: string;
  mode: string;
  address: string;
  duration: string;
  url: string;
  roi_months?: number | null;
  expected_monthly_salary?: number;
  category?: string;
  category_id?: string;
  description_long?: string;
  objectives?: string;
  target_audience?: string;
  requirements?: string;
  course_type?: string;
  brochure_url?: string;
  brochure_text?: string;
  start_date_text?: string;
  start_date?: string;
  syllabus?: string;
  is_active?: boolean;
  is_verified?: boolean;
  certification?: string;
  benefits?: string;
  seniority_level?: string;
  region?: string;
  created_at?: string;
  view_count?: number;
  comparison_count?: number;
}

export interface Institution {
  id: string;
  name: string;
  slug: string;
  address: string;
}

/**
 * Derives a URL-friendly slug from the course's real URL.
 * Falls back to normalizing the text slug if no URL is available.
 */
export function cleanSlug(slugOrUrl: string, url?: string): string {
  // If a real URL is available, extract the last meaningful path segment
  if (url) {
    try {
      const parsed = new URL(url);
      const segments = parsed.pathname.split('/').filter(Boolean);
      const last = segments[segments.length - 1];
      if (last && last.length > 2) {
        return last
          .toLowerCase()
          .replace(/[^a-z0-9-]/g, '-')
          .replace(/-+/g, '-')
          .replace(/^-|-$/g, '');
      }
    } catch {
      // URL parsing failed, fall through to text normalization
    }
  }

  if (!slugOrUrl) return "";
  return slugOrUrl
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

/**
 * Parses duration strings like '12 meses' or '1 año' to a numeric month value.
 */
export function parseDurationToMonths(duration: string): number {
  if (!duration) return 0;
  const match = duration.match(/(\d+)/);
  if (!match) return 0;
  const value = parseInt(match[1]);
  const unit = duration.toLowerCase();
  if (unit.startsWith('mes') || unit.startsWith('month')) return value;
  if (unit.startsWith('semana') || unit.startsWith('week')) return value / 4.33;
  if (unit.startsWith('año') || unit.startsWith('year')) return value * 12;
  return 0;
}
