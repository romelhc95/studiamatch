"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, COURSE_PUBLIC_FIELDS } from "@/lib/supabase";
import CoursePublicRenderer, { type PublicCourse, type CoursePublicTab } from "@/components/courses/CoursePublicRenderer";

export default function CourseDetailClient({ institutionSlug, courseSlug }: { institutionSlug: string; courseSlug: string }) {
  const [course, setCourse] = useState<PublicCourse | null>(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [errorInfo, setErrorInfo] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<CoursePublicTab>("info");
  const [relatedCourses, setRelatedCourses] = useState<PublicCourse[]>([]);
  const [compareList, setCompareList] = useState<Array<{ id: string; name: string }>>([]);
  const [compareInit, setCompareInit] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("StudIAMatch_compare_list");
      if (saved) {
        const parsed: unknown = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          // eslint-disable-next-line react-hooks/set-state-in-effect
          setCompareList(parsed.filter((item): item is { id: string; name: string } => Boolean(item && typeof item.id === "string" && typeof item.name === "string")));
        }
      }
    } catch {
      // A corrupted comparison list should not prevent the course page from rendering.
    }
    setCompareInit(true);
  }, []);

  useEffect(() => {
    if (compareInit) localStorage.setItem("StudIAMatch_compare_list", JSON.stringify(compareList));
  }, [compareList, compareInit]);

  const toggleCompare = (selectedCourse: PublicCourse) => {
    setCompareList((current) => {
      if (current.find((item) => item.id === selectedCourse.id)) return current.filter((item) => item.id !== selectedCourse.id);
      if (current.length >= 3) return current;
      return [...current, { id: selectedCourse.id, name: selectedCourse.name }];
    });
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        setLoading(true);
        setErrorInfo(null);

        if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) throw new Error("Configuración de Supabase faltante.");

        const safeCourseSlug = encodeURIComponent(courseSlug);
        const safeInstitutionSlug = encodeURIComponent(institutionSlug);
        const headers = { apikey: SUPABASE_PUBLISHABLE_KEY };
        const [institutionResponse, categoriesResponse] = await Promise.all([
          fetch(`${SUPABASE_URL}/rest/v1/institutions?select=id,name,slug&slug=eq.${safeInstitutionSlug}&limit=1`, { headers }),
          fetch(`${SUPABASE_URL}/rest/v1/categories?select=id,name`, { headers }),
        ]);

        if (!institutionResponse.ok) throw new Error(`Error cargando institución: ${institutionResponse.status}`);
        const institutions: unknown = await institutionResponse.json();
        const institution = Array.isArray(institutions) ? institutions[0] as { id?: string; name?: string; slug?: string } | undefined : undefined;
        if (!institution?.id) {
          setErrorInfo(`La institución "${institutionSlug}" no está disponible actualmente.`);
          return;
        }

        const safeInstitutionId = encodeURIComponent(institution.id);
        const categories: unknown = categoriesResponse.ok ? await categoriesResponse.json() : [];
        const categoryArray = Array.isArray(categories) ? categories as Array<{ id: string; name: string }> : [];
        const publicUrl = `${SUPABASE_URL}/rest/v1/courses_public_effective?slug=eq.${safeCourseSlug}&institution_id=eq.${safeInstitutionId}&select=${COURSE_PUBLIC_FIELDS}`;
        const response = await fetch(publicUrl, { headers });
        if (!response.ok) throw new Error(`Error en la respuesta del servidor: ${response.status}`);

        let data: unknown = await response.json();
        if (!Array.isArray(data) || data.length === 0) {
          const urlMatch = `${SUPABASE_URL}/rest/v1/courses_public_effective?url=ilike.*${safeCourseSlug}*&institution_id=eq.${safeInstitutionId}&select=${COURSE_PUBLIC_FIELDS}&limit=1`;
          const urlResponse = await fetch(urlMatch, { headers });
          if (urlResponse.ok) data = await urlResponse.json();

          if (!Array.isArray(data) || data.length === 0) {
            const safeKeywords = encodeURIComponent(courseSlug.replace(/-/g, "*"));
            const likeResponse = await fetch(`${SUPABASE_URL}/rest/v1/courses_public_effective?slug=ilike.*${safeKeywords}*&institution_id=eq.${safeInstitutionId}&select=${COURSE_PUBLIC_FIELDS}&limit=1`, { headers });
            if (likeResponse.ok) data = await likeResponse.json();
          }
        }

        if (Array.isArray(data) && data.length > 0) {
          const fetchedCourse = {
            ...(data[0] as PublicCourse),
            institution_name: institution.name || "StudIAMatch",
            institution_slug: institution.slug || institutionSlug,
          };
          fetchedCourse.category = categoryArray.find((category) => category.id === fetchedCourse.category_id)?.name || fetchedCourse.category;
          if (!fetchedCourse.duration && fetchedCourse.description_long?.startsWith("Duración:")) {
            fetchedCourse.duration = fetchedCourse.description_long.split("\n")[0].replace("Duración:", "").trim();
          }
          setCourse(fetchedCourse);
        } else {
          setErrorInfo(`El programa "${courseSlug}" de la institución "${institutionSlug}" no está disponible actualmente en nuestra base de datos.`);
        }
      } catch {
        setErrorInfo("Ocurrió un error técnico al conectar con el servidor de datos.");
      } finally {
        setLoading(false);
      }
    };

    if (courseSlug && institutionSlug) void fetchCourse();
  }, [courseSlug, institutionSlug]);

  useEffect(() => {
    if (!course) return;

    const fetchRelatedCourses = async () => {
      if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY || !course.category_id || !course.institution_id) {
        setRelatedCourses([]);
        return;
      }

      try {
        const headers = { apikey: SUPABASE_PUBLISHABLE_KEY };
        const safeCatId = encodeURIComponent(course.category_id);
        const safeInstitutionId = encodeURIComponent(course.institution_id);
        const query = `${SUPABASE_URL}/rest/v1/courses_public_effective?category_id=eq.${safeCatId}&institution_id=eq.${safeInstitutionId}&id=neq.${encodeURIComponent(course.id)}&limit=3&select=${COURSE_PUBLIC_FIELDS}`;
        const response = await fetch(query, { headers });
        const relatedData: unknown = response.ok ? await response.json() : [];
        if (!Array.isArray(relatedData)) return;
        setRelatedCourses(relatedData.map((item) => ({
          ...(item as PublicCourse),
          institution_name: course.institution_name || "StudIAMatch",
          institution_slug: course.institution_slug || "general",
        })));
      } catch {
        setRelatedCourses([]);
      }
    };

    void fetchRelatedCourses();
  }, [course]);

  if (loading || !mounted) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-brand-slate text-white">
        <div className="mb-4 size-12 animate-spin rounded-full border-4 border-brand-mint border-t-transparent" />
        <p className="animate-pulse text-xs font-bold uppercase tracking-widest text-brand-mint">Cargando información del programa...</p>
      </div>
    );
  }

  if (errorInfo) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-white p-6 text-center dark:bg-brand-slate">
        <div className="max-w-lg rounded-[3rem] border border-red-100 bg-red-50 p-10 dark:border-red-500/20 dark:bg-red-500/10">
          <h2 className="mb-4 text-3xl font-bold text-brand-slate dark:text-white">Lo sentimos</h2>
          <p className="mb-8 leading-relaxed text-slate-500 dark:text-slate-400">{errorInfo}</p>
          <Link href="/" className="inline-flex h-12 items-center rounded-2xl bg-brand-blue px-8 font-bold text-white shadow-lg shadow-brand-blue/20">Volver al buscador</Link>
        </div>
      </div>
    );
  }

  if (!course) return null;

  return (
    <CoursePublicRenderer
      course={course}
      activeTab={activeTab}
      onActiveTabChange={setActiveTab}
      compareList={compareList}
      onToggleCompare={() => toggleCompare(course)}
      relatedCourses={relatedCourses}
    />
  );
}
