"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  ChevronLeft, MapPin, Clock, TrendingUp, ExternalLink, GraduationCap, Plus
} from "lucide-react";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";
import Link from "next/link";
import { SUPABASE_URL, SUPABASE_ANON_KEY, type Course } from "@/lib/supabase";

function CompareContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ids = searchParams.get("ids")?.split(",") || [];
    if (ids.length === 0) {
      router.push("/");
      return;
    }

    const fetchCourses = async () => {
      try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/courses?select=*,institutions(name,slug),categories(name)`, {
          headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
          }
        });
        const rawData: any[] = await response.json();
        
        // Map relationship data
        const enriched = rawData
          .filter(c => ids.includes(c.id))
          .map(c => ({
            ...c,
            institution_name: c.institutions?.name || "StudIAMatch",
            institution_slug: c.institutions?.slug || "general",
            category: c.categories?.name || c.category
          }));
          
        setCourses(enriched);
      } catch (error) {
        console.error("Error fetching courses for comparison:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, [searchParams, router]);

  const handleRemove = (id: string) => {
    const updatedCourses = courses.filter(c => c.id !== id);
    setCourses(updatedCourses);
    
    // Update URL
    const newIds = updatedCourses.map(c => c.id).join(",");
    if (newIds) {
      router.push(`/compare?ids=${newIds}`);
    } else {
      router.push("/");
    }

    // Update LocalStorage for sync with Home
    localStorage.setItem('StudIAMatch_compare_list', JSON.stringify(updatedCourses));
  };

  if (loading) return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-white dark:bg-brand-slate">
      <div className="w-12 h-12 rounded-full border-4 border-brand-blue border-t-transparent animate-spin" />
      <span className="text-sm font-bold text-slate-500 animate-pulse">Preparando comparativa...</span>
    </div>
  );

  return (
    <div className="min-h-screen bg-white dark:bg-brand-slate text-brand-slate dark:text-white font-sans selection:bg-brand-mint/30">
      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-12 gap-6">
          <div>
            <Link href="/" className="inline-flex items-center text-sm font-bold text-brand-blue hover:translate-x-[-4px] transition-all mb-4 group">
              <ChevronLeft className="h-5 w-5 mr-1 group-hover:stroke-[3px]" /> Volver a la búsqueda
            </Link>
            <h1 className="text-4xl font-bold text-brand-slate dark:text-white leading-tight">Comparativa de Programas</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-2 text-lg">Analiza detalladamente tus mejores opciones con datos reales.</p>
          </div>
          <Badge className="px-5 py-2 text-sm font-bold bg-brand-blue/10 text-brand-blue dark:bg-brand-blue/20 border-0 rounded-xl">
            {courses.length} Programas seleccionados
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {courses.map((course) => (
            <Card key={course.id} className="relative overflow-hidden border-brand-gray/50 dark:border-white/10 shadow-premium flex flex-col rounded-3xl bg-white dark:bg-zinc-900/40">
              <div className="h-2 bg-brand-blue w-full" />
              <button 
                onClick={() => handleRemove(course.id)}
                className="absolute top-4 right-4 h-8 w-8 rounded-full bg-red-50 text-red-500 flex items-center justify-center hover:bg-red-500 hover:text-white transition-all z-20 shadow-sm"
                title="Retirar de la comparativa"
              >
                <Plus className="h-4 w-4 rotate-45" />
              </button>
              
              <div className="p-8 flex-1 space-y-8">
                {/* Header Section */}
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
                  <h2 className="text-xl font-bold text-brand-slate dark:text-white leading-snug h-14 overflow-hidden line-clamp-2 group-hover:text-brand-blue transition-colors">
                    {course.name}
                  </h2>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 dark:bg-zinc-800/50 p-4 rounded-2xl border border-brand-gray/30 dark:border-white/5">
                    <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Inversión</div>
                    <div className="text-lg font-bold text-brand-slate dark:text-white">
                      {course.price_status === 'consultar' ? "Consultar" : (course.price_pen ? `S/ ${course.price_pen.toLocaleString()}` : "Gratis")}
                    </div>
                  </div>
                  <div className="bg-emerald-50 dark:bg-emerald-500/10 p-4 rounded-2xl border border-emerald-100 dark:border-emerald-500/20">
                    <div className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-widest mb-1">ROI Est.</div>
                    <div className="text-lg font-bold text-emerald-700 dark:text-emerald-400">{course.roi_months?.toFixed(1) || "12.0"} meses</div>
                  </div>
                </div>

                {/* Comparison Details */}
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

              {/* Action Buttons */}
              <div className="p-8 bg-slate-50/50 dark:bg-zinc-800/30 border-t border-brand-gray/30 dark:border-white/10 flex flex-col gap-3">
                <Link href={`/courses/${cleanSlug((course as any).institution_slug)}/${cleanSlug(course.slug, course.url)}`} className="w-full">
                  <Button className="w-full bg-brand-mint hover:bg-brand-mint/90 text-brand-slate font-black h-14 rounded-2xl shadow-lg shadow-brand-mint/10 border-0 uppercase tracking-widest text-xs">
                    Solicitar Info
                  </Button>
                </Link>
                <Link href={`/courses/${cleanSlug((course as any).institution_slug)}/${cleanSlug(course.slug, course.url)}`} className="w-full">
                  <Button variant="outline" className="w-full text-[10px] font-black h-12 rounded-2xl border-brand-gray/50 hover:bg-brand-blue/5 hover:text-brand-blue hover:border-brand-blue transition-all uppercase tracking-widest">
                    Ver Detalle Programa
                  </Button>
                </Link>
              </div>
            </Card>
          ))}

          {/* Add more slot if < 3 */}
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
      </main>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Cargando comparativa...</div>}>
      <CompareContent />
    </Suspense>
  );
}
