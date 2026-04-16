import { Suspense } from "react";
import CourseDetailClient from "./CourseDetailClient";
import { SUPABASE_URL, SUPABASE_ANON_KEY, cleanSlug } from "@/lib/supabase";
import type { Metadata } from "next";

export async function generateMetadata({ params }: { params: Promise<{ institution: string, slug: string }> }): Promise<Metadata> {
  const { institution, slug } = await params;
  return {
    title: `${slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')} - ${institution.toUpperCase()} | StudIAMatch`,
    description: `Detalles del programa ${slug} en ${institution}. Compara precios, duración y ROI.`
  };
}

export async function generateStaticParams() {
  try {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/courses?select=slug,url,institutions(slug)`, {
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      }
    });

    const courses = await response.json();
    if (!Array.isArray(courses)) return [];

    return courses
      .filter((c: any) => c.slug && c.institutions?.slug)
      .map((c: any) => ({
        institution: cleanSlug(c.institutions.slug),
        slug: cleanSlug(c.slug, c.url)
      }));
  } catch (error) {
    console.error("Error generating static params:", error);
    return [];
  }
}

export default async function CourseDetailPage(props: { params: Promise<{ institution: string, slug: string }> }) {
  const params = await props.params;
  const { institution, slug } = params;
  if (!slug || !institution) return null;

  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Cargando programa...</div>}>
      <CourseDetailClient courseSlug={slug} institutionSlug={institution} />
    </Suspense>
  );
}
