// Centralized Supabase Configuration
// All frontend components should import from here.

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  // In development, we allow it but log a warning. In production, this should be set in the platform.
  if (process.env.NODE_ENV === 'production') {
    throw new Error("Missing Supabase environment variables. Check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.");
  } else {
    console.warn("⚠️ Supabase environment variables are missing. Some features might not work correctly.");
  }
}

export const SUPABASE_URL = supabaseUrl || '';
export const SUPABASE_ANON_KEY = supabaseAnonKey || '';

export interface Course {
  id: string;
  name: string;
  slug: string;
  institution_name: string;
  price_pen: number | null;
  price_status?: string;
  mode: string;
  address: string;
  duration: string;
  url: string;
  roi_months?: number | null;
  expected_monthly_salary?: number;
  category?: string;
  description_long?: string;
  objectives?: string;
  learning_outcomes?: string;
  target_audience?: string;
  requirements?: string;
  subcategory?: string;
  course_type?: string;
  brochure_url?: string;
  brochure_text?: string;
}

export interface Institution {
  id: string;
  name: string;
  slug: string;
  address: string;
}

/**
 * Normalizes a text to be used as a URL-friendly slug.
 */
export function cleanSlug(text: string): string {
  if (!text) return "";
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/-+/g, "-")
    .trim();
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
