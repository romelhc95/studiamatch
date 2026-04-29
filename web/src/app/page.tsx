import { Suspense } from "react";
import type { Metadata } from "next";
import { SUPABASE_URL, SUPABASE_ANON_KEY, cleanSlug, type Course, type Institution } from "@/lib/supabase";
import HomeContent from "./HomeContent";

export const metadata: Metadata = {
  title: "StudIAMatch - Encuentra tu educación ideal",
  description: "Compara inversión, contenido y retorno financiero de programas tech en Perú. Datos reales de mercado para elegir tu próximo programa educativo con certeza.",
  openGraph: {
    title: "StudIAMatch - Data-driven education decisions",
    description: "Compara inversión, contenido y retorno financiero de programas tech en Perú.",
    type: "website",
    locale: "es_PE",
  },
  alternates: {
    canonical: "https://studiamatch.com",
  },
};

async function fetchCourses(): Promise<Course[]> {
  try {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return [];

    const headers = {
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
    };

    const [cRes, iRes] = await Promise.all([
      fetch(`${SUPABASE_URL}/rest/v1/courses?is_active=eq.true&is_verified=eq.true&select=id,name,slug,url,institution_id,price_pen,price_status,mode,course_type,category_id,duration,start_date_text,categories(name),institutions(name,slug)&order=created_at.desc`, {
        headers,
        next: { revalidate: 3600 }
      }),
      fetch(`${SUPABASE_URL}/rest/v1/institutions?select=id,name,slug`, {
        headers,
        next: { revalidate: 3600 }
      })
    ]);

    const [cData, iData] = await Promise.all([cRes.json(), iRes.json()]);

    if (!Array.isArray(cData) || !Array.isArray(iData)) return [];

    return cData.map((course: any) => ({
      ...course,
      institution_name: course.institutions?.name || iData.find((i: Institution) => i.id === course.institution_id)?.name || "StudIAMatch",
      institution_slug: course.institutions?.slug || iData.find((i: Institution) => i.id === course.institution_id)?.slug || "general",
      category: course.categories?.name || course.category
    })) as Course[];
  } catch {
    return [];
  }
}

export default async function Home() {
  const initialCourses = await fetchCourses();

  return (
    <Suspense fallback={
      <div className="min-h-screen bg-brand-slate flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-blue"></div>
      </div>
    }>
      <HomeContent initialCourses={initialCourses} />
    </Suspense>
  );
}
