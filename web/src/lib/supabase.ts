import { createClient } from '@supabase/supabase-js';
import { createApiKeyOnlyFetch } from './supabase-transport';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY?.trim();
const h3MockUrl = process.env.NEXT_PUBLIC_H3_MOCK_URL?.trim();
const isLocalMock = Boolean(h3MockUrl);

if (!supabaseUrl) {
  throw new Error("Missing required environment variable NEXT_PUBLIC_SUPABASE_URL.");
}

if (
  !isLocalMock && (
    !supabasePublishableKey?.startsWith("sb_publishable_") ||
    supabasePublishableKey.length <= "sb_publishable_".length
  )
) {
  throw new Error("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY must start with sb_publishable_.");
}

if (h3MockUrl && process.env.NODE_ENV === "production" && process.env.NEXT_PUBLIC_H3_ALLOW_MOCK_BUILD !== "true") {
  throw new Error("NEXT_PUBLIC_H3_MOCK_URL is forbidden in production builds.");
}

if (h3MockUrl) {
  const parsedMockUrl = new URL(h3MockUrl);
  if (parsedMockUrl.protocol !== "http:" || !["localhost", "127.0.0.1"].includes(parsedMockUrl.hostname)) {
    throw new Error("NEXT_PUBLIC_H3_MOCK_URL must use local HTTP.");
  }
}

export const SUPABASE_URL = h3MockUrl || supabaseUrl;
export const SUPABASE_PUBLISHABLE_KEY = supabasePublishableKey || "local-publishable-key";

export const supabaseBrowserClient = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
  global: { fetch: createApiKeyOnlyFetch(SUPABASE_PUBLISHABLE_KEY, fetch) },
  auth: {
    flowType: 'pkce',
    autoRefreshToken: false,
    persistSession: false,
    detectSessionInUrl: false,
  },
});

export const COURSE_PUBLIC_FIELDS = 'id,institution_id,category_id,name,slug,url,price_pen,price_status,mode,duration,description_long,syllabus,target_audience,requirements,certification,benefits,objectives,start_date,start_date_text,course_type,brochure_url,expected_monthly_salary,seniority_level,roi_months,view_count,comparison_count,created_at,updated_at';

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

/** Normalize PostgreSQL numeric values that PostgREST serializes as strings. */
export function toFiniteNumberOrNull(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null;
  const parsed = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function normalizeCourseNumbers(course: Course): Course {
  return {
    ...course,
    price_pen: toFiniteNumberOrNull(course.price_pen),
    expected_monthly_salary: toFiniteNumberOrNull(course.expected_monthly_salary) ?? undefined,
    roi_months: toFiniteNumberOrNull(course.roi_months),
    view_count: toFiniteNumberOrNull(course.view_count) ?? undefined,
    comparison_count: toFiniteNumberOrNull(course.comparison_count) ?? undefined,
  };
}

export function cleanSlug(slugOrUrl: string, url?: string): string {
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
      return slugOrUrl
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");
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

export function parseDurationToMonths(duration: string): number {
  if (!duration) return 0;
  const normalized = duration
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
  const unitPattern = '(anos?|years?|mes(?:es)?|months?|semanas?|weeks?)';
  const matchesIn = (text: string) => {
    const range = text.match(new RegExp(`(\\d+(?:[.,]\\d+)?)\\s*(?:a|hasta|[-–])\\s*\\d+(?:[.,]\\d+)?\\s*${unitPattern}`));
    return range
      ? [range]
      : [...text.matchAll(new RegExp(`(\\d+(?:[.,]\\d+)?)\\s*${unitPattern}`, 'g'))];
  };
  const toMonths = (matches: RegExpMatchArray[]) => matches.reduce((total, match) => {
    const value = Number(match[1].replace(',', '.'));
    const unit = match[2];
    if (!Number.isFinite(value)) return total;
    if (unit.startsWith('ano') || unit.startsWith('year')) return total + value * 12;
    if (unit.startsWith('semana') || unit.startsWith('week')) return total + value / 4.33;
    if (unit.startsWith('mes') || unit.startsWith('month')) return total + value;
    return total;
  }, 0);
  const relativeTolerance = 0.1;
  const logBucketWidth = Math.log(1.01);
  const bucketNeighbors = 12;
  const periodBuckets = new Map<number, { minimum: number; maximum: number }>();
  let hasFinitePositiveReference = false;
  let hasInfiniteReference = false;

  // A 1% log bucket is narrower than the 10% equivalence window; +/-12 covers
  // its maximum log-distance. Within a bucket, its extrema preserve nearest
  // reference checks for values inside or outside that bucket.
  const isDuplicatePeriod = (months: number) => {
    if (hasInfiniteReference && Number.isFinite(months)) return true;
    if (months === Number.POSITIVE_INFINITY) return hasFinitePositiveReference;
    if (!Number.isFinite(months) || months <= 0) return false;

    const bucket = Math.floor(Math.log(months) / logBucketWidth);
    for (let offset = -bucketNeighbors; offset <= bucketNeighbors; offset += 1) {
      const references = periodBuckets.get(bucket + offset);
      if (!references) continue;
      const matchesReference = (referenceMonths: number) =>
        Math.abs(months - referenceMonths) <= Math.max(referenceMonths, months) * relativeTolerance;
      if (matchesReference(references.minimum) || matchesReference(references.maximum)) return true;
    }
    return false;
  };

  const addReferencePeriod = (months: number) => {
    if (months === Number.POSITIVE_INFINITY) {
      hasInfiniteReference = true;
      return;
    }
    if (!Number.isFinite(months) || months <= 0) return;

    hasFinitePositiveReference = true;
    const bucket = Math.floor(Math.log(months) / logBucketWidth);
    const references = periodBuckets.get(bucket);
    if (!references) {
      periodBuckets.set(bucket, { minimum: months, maximum: months });
      return;
    }
    references.minimum = Math.min(references.minimum, months);
    references.maximum = Math.max(references.maximum, months);
  };

  const addDistinctPeriods = (matches: RegExpMatchArray[], startingTotal: number) => {
    let total = startingTotal;
    for (const match of matches) {
      const months = toMonths([match]);
      if (isDuplicatePeriod(months)) continue;
      total += months;
      addReferencePeriod(months);
    }
    return total;
  };

  const outsideParentheses: string[] = [];
  const parentheticalGroups: string[] = [];
  let depth = 0;
  let currentGroup = '';
  for (const character of normalized) {
    if (character === '(') {
      if (depth === 0) currentGroup = '';
      else currentGroup += character;
      depth += 1;
      continue;
    }
    if (character === ')' && depth > 0) {
      depth -= 1;
      if (depth === 0) parentheticalGroups.push(currentGroup);
      else currentGroup += character;
      continue;
    }
    if (depth === 0) outsideParentheses.push(character);
    else currentGroup += character;
  }
  if (depth > 0) parentheticalGroups.push(currentGroup);

  const primaryMatches = matchesIn(outsideParentheses.join(''));
  if (primaryMatches.length === 0) return addDistinctPeriods(matchesIn(normalized), 0);

  const primaryPeriods = primaryMatches.map((match) => toMonths([match]));
  const primaryMonths = toMonths(primaryMatches);
  primaryPeriods.forEach(addReferencePeriod);
  addReferencePeriod(primaryMonths);
  return parentheticalGroups.reduce((total, group) => addDistinctPeriods(matchesIn(group), total), primaryMonths);
}

export function isUpdateCareerGoalCourse(duration: string | null | undefined, mode: string | null | undefined): boolean {
  const months = parseDurationToMonths(duration || '') || 12;
  const normalizedMode = (mode || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();

  return months <= 6 && (normalizedMode === 'remoto' || normalizedMode === 'hibrido');
}
