"use client";

import { useEffect, useState, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  ChevronLeft, MapPin, Clock, TrendingUp, GraduationCap, Plus, Star, DollarSign
} from "lucide-react";
import Link from "next/link";
import { SUPABASE_URL, SUPABASE_ANON_KEY, COURSE_PUBLIC_FIELDS, cleanSlug, type Course } from "@/lib/supabase";

// Componente Skeleton para Feedback Inmediato
const ComparisonSkeleton = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
    {[1, 2, 3].map((i) => (
      <Card key={i} className="relative overflow-hidden border-brand-gray/50 animate-pulse rounded-3xl bg-slate-50/50">
        <div className="h-2 bg-slate-200 w-full" />
        <div className="p-8 space-y-8">
          <div className="space-y-4">
            <div className="h-4 bg-slate-200 rounded w-1/4" />
            <div className="h-8 bg-slate-200 rounded w-3/4" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-16 bg-white rounded-2xl border border-slate-100" />
            <div className="h-16 bg-white rounded-2xl border border-slate-100" />
          </div>
          <div className="space-y-4 pt-6">
            {[1, 2, 3, 4].map(j => (
              <div key={j} className="flex gap-4">
                <div className="w-10 h-10 bg-white rounded-xl" />
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-2 bg-slate-100 rounded w-1/3" />
                  <div className="h-3 bg-slate-200 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="p-8 bg-white border-t border-slate-100 space-y-3">
          <div className="h-14 bg-slate-100 rounded-2xl" />
          <div className="h-12 bg-slate-50 rounded-2xl" />
        </div>
      </Card>
    ))}
  </div>
);

export default function CompareContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const idsString = searchParams.get("ids") || "";

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (!idsString) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoading(false);
      router.push("/");
      return;
    }

    const ids = idsString.split(",").filter(id => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id));

    const fetchCourses = async () => {
      try {
        setLoading(true);
        const queryIds = ids.join(',');
        const response = await fetch(`${SUPABASE_URL}/rest/v1/courses?id=in.(${queryIds})&select=${COURSE_PUBLIC_FIELDS},institutions(name,slug),categories(name)&is_active=eq.true&is_verified=eq.true`, {
          headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
          }
        });

        if (!response.ok) throw new Error("Failed to fetch courses");

        const rawData = await response.json();
        const dataArray = Array.isArray(rawData) ? rawData : [];

        const enriched = dataArray.map(c => {
          // Cálculo seguro de ROI en el frontend si falla el backend
          const investment = c.price_pen || 0;
          const salary = c.expected_monthly_salary || 4500;
          const calculatedRoi = investment > 0 ? (investment / salary) : 0;

          return {
            ...c,
            roi_months: c.roi_months || calculatedRoi || 12,
            institution_name: c.institutions?.name || "StudIAMatch",
            institution_slug: c.institutions?.slug || "general",
            category: c.categories?.name || c.category
          };
        });

        setCourses(enriched);
      } catch (error) {
        console.error("Error fetching courses for comparison:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, [mounted, idsString, router]);

  const handleRemove = (id: string) => {
    const updatedCourses = courses.filter(c => c.id !== id);
    setCourses(updatedCourses);

    const newIds = updatedCourses.map(c => c.id).join(",");
    if (newIds) {
      router.push(`/compare?ids=${newIds}`);
    } else {
      router.push("/");
    }
    localStorage.setItem('StudIAMatch_compare_list', JSON.stringify(updatedCourses));
  };

  // Best-value analysis
  const bestRoiCourse = useMemo(() => {
    if (courses.length < 2) return null;
    const withRoi = courses.filter(c => c.roi_months && c.roi_months > 0);
    if (withRoi.length === 0) return null;
    return withRoi.reduce((best, c) => (c.roi_months! < best.roi_months! ? c : best));
  }, [courses]);

  const cheapestCourse = useMemo(() => {
    if (courses.length < 2) return null;
    const withPrice = courses.filter(c => c.price_pen && c.price_pen > 0);
    if (withPrice.length === 0) return null;
    return withPrice.reduce((best, c) => (c.price_pen! < best.price_pen! ? c : best));
  }, [courses]);

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-white dark:bg-brand-slate text-brand-slate dark:text-white font-sans selection:bg-brand-mint/30">
      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-12 gap-6">
          <div className="animate-in fade-in slide-in-from-left duration-500">
            <Link href="/" className="inline-flex items-center text-sm font-bold text-brand-blue hover:translate-x-[-4px] transition-all mb-4 group">
              <ChevronLeft className="h-5 w-5 mr-1 group-hover:stroke-[3px]" /> Volver a la búsqueda
            </Link>
            <h1 className="text-4xl font-bold text-brand-slate dark:text-white leading-tight">Comparativa de Programas</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-2 text-lg">Analiza detalladamente tus mejores opciones con datos reales.</p>
          </div>
          {!loading && (
            <Badge className="px-5 py-2 text-sm font-bold bg-brand-blue/10 text-brand-blue dark:bg-brand-blue/20 border-0 rounded-xl animate-in zoom-in duration-300">
              {courses.length} Programas seleccionados
            </Badge>
          )}
        </div>

        {loading ? (
          <ComparisonSkeleton />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {courses.map((course) => {
              const isBestRoi = bestRoiCourse?.id === course.id;
              const isCheapest = cheapestCourse?.id === course.id && course.id !== bestRoiCourse?.id;
              return (
              <Card key={course.id} className={cn(
                "relative overflow-hidden border-brand-gray/50 dark:border-white/10 shadow-premium flex flex-col rounded-3xl bg-white dark:bg-zinc-900/40 hover:shadow-2xl transition-all hover:-translate-y-1",
                isBestRoi && "ring-2 ring-amber-400/40 border-amber-300/50"
              )}>
                {isBestRoi && (
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-400 to-yellow-500 z-10" />
                )}
                {isCheapest && (
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-400 to-teal-500 z-10" />
                )}
                <button
                  onClick={() => handleRemove(course.id)}
                  className="absolute top-4 right-4 h-8 w-8 rounded-full bg-red-50 text-red-500 flex items-center justify-center hover:bg-red-500 hover:text-white transition-all z-20 shadow-sm"
                  title="Retirar de la comparativa"
                >
                  <Plus className="h-4 w-4 rotate-45" />
                </button>

                <div className="p-8 flex-1 space-y-8">
                  <div className="space-y-4">
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="bg-brand-blue/10 text-brand-blue dark:bg-brand-blue/20 font-black border-0 px-3 text-[9px] uppercase tracking-widest">
                        {course.institution_name}
                      </Badge>
                      {course.course_type && (
                        <Badge variant="outline" className="border-brand-gray/30 text-slate-400 font-bold px-3 text-[9px] uppercase tracking-widest">
                          {course.course_type}
                        </Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {isBestRoi && (
                        <Badge className="bg-amber-50 text-amber-700 border-amber-200 font-bold text-[9px] px-2 py-0.5 rounded-md flex items-center gap-1">
                          <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> Mejor ROI
                        </Badge>
                      )}
                      {isCheapest && (
                        <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 font-bold text-[9px] px-2 py-0.5 rounded-md flex items-center gap-1">
                          <DollarSign className="h-3 w-3 text-emerald-500" /> Más accesible
                        </Badge>
                      )}
                    </div>
                    <h2 className="text-xl font-bold text-brand-slate dark:text-white leading-snug h-14 overflow-hidden line-clamp-2">
                      {course.name}
                    </h2>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-50 dark:bg-zinc-800/50 p-4 rounded-2xl border border-brand-gray/30 dark:border-white/5">
                      <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Inversión</div>
                      <div className="text-lg font-bold text-brand-slate dark:text-white">
                        {course.price_status === 'consultar' ? "Consultar" : (course.price_pen ? `S/ ${course.price_pen.toLocaleString()}` : "Gratis")}
                      </div>
                    </div>
                    <div className="bg-emerald-50 dark:bg-emerald-500/10 p-4 rounded-2xl border border-emerald-100 dark:border-emerald-500/20">
                      <div className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-widest mb-1">ROI Est.</div>
                      <div className="text-lg font-bold text-emerald-700 dark:text-emerald-400">
                        {course.roi_months ? course.roi_months.toFixed(1) : "12.0"} meses
                      </div>
                    </div>
                  </div>

                  <div className="space-y-5 pt-6 border-t border-brand-gray/30 dark:border-white/10">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center shrink-0 shadow-sm">
                        <Clock className="h-5 w-5 text-brand-blue" />
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Duración</div>
                        <div className="text-sm font-bold">{course.duration || "Consultar"}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center shrink-0 shadow-sm">
                        <GraduationCap className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Modalidad</div>
                        <div className="text-sm font-bold">{course.mode}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center shrink-0 shadow-sm">
                        <MapPin className="h-5 w-5 text-amber-600" />
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Ubicación</div>
                        <div className="text-sm font-bold line-clamp-1">{course.address}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-brand-mint/10 dark:bg-brand-mint/20 flex items-center justify-center shrink-0 shadow-sm">
                        <TrendingUp className="h-5 w-5 text-brand-slate dark:text-brand-mint" />
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Salario Inicial</div>
                        <div className="text-sm font-bold">S/ {course.expected_monthly_salary?.toLocaleString() || "4,500"}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-8 bg-slate-50/50 dark:bg-zinc-800/30 border-t border-brand-gray/30 dark:border-white/10 flex flex-col gap-3 mt-auto">
                   <Link href={`/courses/${cleanSlug(course.institution_slug || 'general')}/${course.slug}`} className="w-full">
                    <Button className="w-full bg-brand-mint hover:bg-brand-mint/90 text-brand-slate font-black h-14 rounded-2xl shadow-lg shadow-brand-mint/10 border-0 uppercase tracking-widest text-xs">
                      Solicitar Info
                    </Button>
                  </Link>
                </div>
              </Card>
            );
            })}

            {courses.length < 3 && (
              <div className="border-2 border-dashed border-brand-gray/50 dark:border-white/10 rounded-3xl flex flex-col items-center justify-center p-12 text-center space-y-6 bg-slate-50/20">
                <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-zinc-900 flex items-center justify-center shadow-inner">
                  <Plus className="h-10 w-10 text-slate-300" />
                </div>
                <div className="space-y-2">
                  <div className="text-xl font-bold text-slate-400">Espacio disponible</div>
                  <p className="text-sm text-slate-400 max-w-[200px] mx-auto">Agrega otro programa para una comparativa más completa.</p>
                </div>
                <Link href="/">
                  <Button variant="outline" className="rounded-xl border-brand-blue text-brand-blue font-bold hover:bg-brand-blue hover:text-white transition-all">
                    + Agregar más programas
                  </Button>
                </Link>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}