import { Suspense } from "react";
import CourseDetailClient from "./CourseDetailClient";
import { SUPABASE_URL, SUPABASE_ANON_KEY } from "@/lib/supabase";

// Generación dinámica de rutas para Cloudflare Pages
export async function generateStaticParams() {
  try {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/courses?select=slug`, {
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      }
    });    const courses = await response.json();
    
    // Normalización estricta para evitar errores en el sistema de archivos de Cloudflare
    return courses
      .filter((c: { slug: string }) => c.slug)
      .map((c: { slug: string }) => ({
        slug: c.slug
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .toLowerCase()
          .replace(/[^a-z0-9-]/g, "-")
      }));
  } catch (error) {
    console.error("Error generating static params:", error);
    return [];
  }
}

// Forzamos que el componente reciba el slug ya resuelto del servidor
export default async function CourseDetailPage(props: { params: Promise<{ slug: string }> }) {
  const params = await props.params;
  const slug = params.slug;

  if (!slug) return null;

  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-brand-slate text-slate-500 font-bold">
        Cargando programa...
      </div>
    }>
      <CourseDetailClient slug={slug} />
    </Suspense>
  );
}
