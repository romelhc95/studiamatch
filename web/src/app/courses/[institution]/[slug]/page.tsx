import { SUPABASE_URL, SUPABASE_ANON_KEY, cleanSlug, type Course } from "@/lib/supabase";
import type { Metadata } from "next";
import CourseDetailClientWrapper from "./CourseDetailClientWrapper";

async function fetchCourseMeta(slug: string) {
  try {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return null;
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/courses?select=name,description_long,url,price_pen,mode,course_type,institutions(name)&slug=eq.${encodeURIComponent(slug)}&limit=1`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
        },
        next: { revalidate: 3600 }
      }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return data?.[0] || null;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: { params: Promise<{ institution: string, slug: string }> }): Promise<Metadata> {
  const { institution, slug } = await params;
  const course = await fetchCourseMeta(slug);

  const courseName = course?.name || slug;
  const instName = course?.institutions?.name || institution;
  const title = `${courseName} - ${instName} | StudIAMatch`;
  const description = course?.description_long?.substring(0, 160) || `Programa ${courseName} en ${instName}.`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "website",
      locale: "es_PE",
    },
    alternates: {
      canonical: `https://studiamatch.com/courses/${institution}/${slug}/`,
    },
  };
}

export const dynamicParams = false;

export async function generateStaticParams() {
  const defaultPath = [{ institution: 'pucp', slug: 'estudios-generales' }];

  try {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
      console.warn("No environment variables found for static generation. Using defaults.");
      return defaultPath;
    }

    const response = await fetch(`${SUPABASE_URL}/rest/v1/courses?select=slug,url,institutions(slug)`, {
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      },
      next: { revalidate: 3600 }
    });

    if (!response.ok) return defaultPath;

    const courses = await response.json();
    if (!Array.isArray(courses) || courses.length === 0) return defaultPath;

    const paths = courses
      .filter((c: { slug: string; institutions?: { slug: string } }) => c.slug && c.institutions?.slug)
      .map((c: { slug: string; institutions?: { slug: string } }) => ({
        institution: cleanSlug(c.institutions?.slug || 'general'),
        slug: c.slug
      }));

    return paths.length > 0 ? paths : defaultPath;
  } catch (error) {
    console.error("Error generating static params:", error);
    return defaultPath;
  }
}

function CourseJsonLd({ course }: { course: Course & { institutions?: { name: string } } }) {
  const ld = {
    "@context": "https://schema.org",
    "@type": "Course",
    "name": course.name,
    "description": course.description_long || `Programa en ${course.institutions?.name}`,
    "provider": {
      "@type": "EducationalOrganization",
      "name": course.institutions?.name || ""
    },
    ...(course.price_pen && course.price_pen > 0 ? {
      "offers": {
        "@type": "Offer",
        "price": course.price_pen,
        "priceCurrency": "PEN"
      }
    } : {}),
    "educationalCredentialAwarded": course.course_type || "Programa",
    "inLanguage": "es",
    ...(course.url ? { "url": course.url } : {})
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }}
    />
  );
}

export default async function CourseDetailPage({ 
  params 
}: { 
  params: Promise<{ institution: string; slug: string }> 
}) {
  const { institution, slug } = await params;
  const courseMeta = await fetchCourseMeta(slug);

  return (
    <>
      {courseMeta && <CourseJsonLd course={courseMeta} />}
      <CourseDetailClientWrapper institutionSlug={institution} courseSlug={slug} />
    </>
  );
}
