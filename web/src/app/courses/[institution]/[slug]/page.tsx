import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, COURSE_PUBLIC_FIELDS, cleanSlug, type Course } from "@/lib/supabase";
import type { Metadata } from "next";
import CourseDetailClientWrapper from "./CourseDetailClientWrapper";

async function fetchCourseMeta(institution: string, slug: string) {
  try {
    if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) return null;
    const headers = { 'apikey': SUPABASE_PUBLISHABLE_KEY };
    const instRes = await fetch(`${SUPABASE_URL}/rest/v1/institutions?select=id,name,slug&slug=eq.${encodeURIComponent(institution)}&limit=1`, { headers });
    if (!instRes.ok) return null;
    const institutions = await instRes.json();
    const inst = Array.isArray(institutions) ? institutions[0] : null;
    if (!inst?.id) return null;
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/courses_public_effective?select=${COURSE_PUBLIC_FIELDS}&institution_id=eq.${encodeURIComponent(inst.id)}&slug=eq.${encodeURIComponent(slug)}&limit=1`,
      { headers }
    );
    if (!res.ok) return null;
    const data = await res.json();
    const course = data?.[0] || null;
    return course ? { ...course, institution_name: inst.name, institutions: { name: inst.name } } : null;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: { params: Promise<{ institution: string, slug: string }> }): Promise<Metadata> {
  const { institution, slug } = await params;
  const course = await fetchCourseMeta(institution, slug);

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

  if (process.env.NEXT_PUBLIC_H3_ALLOW_MOCK_BUILD === 'true') {
    return [{ institution: 'mock', slug: 'mock-course' }];
  }

  try {
    if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) {
      console.warn("No environment variables found for static generation. Using defaults.");
      return defaultPath;
    }

    const headers = { 'apikey': SUPABASE_PUBLISHABLE_KEY };
    const [response, institutionsResponse] = await Promise.all([
      fetch(`${SUPABASE_URL}/rest/v1/courses_public_effective?select=id,institution_id,slug,url`, { headers }),
      fetch(`${SUPABASE_URL}/rest/v1/institutions?select=id,slug`, { headers })
    ]);

    if (!response.ok || !institutionsResponse.ok) return defaultPath;

    const courses = await response.json();
    const institutions = await institutionsResponse.json();
    if (!Array.isArray(courses) || courses.length === 0) return defaultPath;
    const institutionArray = Array.isArray(institutions) ? institutions : [];

    const paths = courses
      .filter((c: { slug: string; institution_id: string }) => c.slug && institutionArray.find((i: { id: string; slug: string }) => i.id === c.institution_id)?.slug)
      .map((c: { slug: string; institution_id: string }) => ({
        institution: cleanSlug(institutionArray.find((i: { id: string; slug: string }) => i.id === c.institution_id)?.slug || 'general'),
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
  const courseMeta = await fetchCourseMeta(institution, slug);

  return (
    <>
      {courseMeta && <CourseJsonLd course={courseMeta} />}
      <CourseDetailClientWrapper institutionSlug={institution} courseSlug={slug} />
    </>
  );
}
