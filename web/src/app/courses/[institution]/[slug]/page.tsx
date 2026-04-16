import { Suspense } from "react";
import CourseDetailClient from "./CourseDetailClient";
import { SUPABASE_URL, SUPABASE_ANON_KEY, cleanSlug } from "@/lib/supabase";

// Generación dinámica de rutas para Cloudflare Pages
export async function generateStaticParams() {
  try {
    // Consultamos el slug del curso Y el slug de la institución asociada
    const response = await fetch(`${SUPABASE_URL}/rest/v1/courses?select=slug,url,institutions(slug)`, {
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      }
    });

    const courses = await response.json();
    
    if (!Array.isArray(courses)) return [];

    // Usamos EXACTAMENTE la misma función cleanSlug que usa la web para sus links
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

// Forzamos que el componente reciba ambos parámetros de la ruta
export default async function CourseDetailPage(props: { params: Promise<{ institution: string, slug: string }> }) {
  const params = await props.params;
  const { institution, slug } = params;

  if (!slug || !institution) return null;

  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-brand-slate text-slate-500 font-bold">
        Cargando programa de {institution}...
      </div>
    }>
      <CourseDetailClient courseSlug={slug} institutionSlug={institution} />
    </Suspense>
  );
}
