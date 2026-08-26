"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  MapPin, TrendingUp,
  CheckCircle, ShieldCheck, GraduationCap, Download, Info,
  Award, Sprout
} from "lucide-react";
import Link from "next/link";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, COURSE_PUBLIC_FIELDS, cleanSlug } from "@/lib/supabase";
import { cn } from "@/lib/utils";

interface Course {
  id: string;
  name: string;
  slug: string;
  institution_slug?: string;
  institution_id?: string;
  institution_name: string;
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
  syllabus?: string;
  course_type?: string;
  brochure_url?: string;
  brochure_text?: string;
  is_active?: boolean;
  start_date_text?: string;
  certification?: string;
  benefits?: string;
  seniority_level?: string;
}

export default function CourseDetailClient({ institutionSlug, courseSlug }: { institutionSlug: string, courseSlug: string }) {
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [errorInfo, setErrorInfo] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'info' | 'requisitos'>('info');
  const [relatedCourses, setRelatedCourses] = useState<Course[]>([]);
  const [compareList, setCompareList] = useState<Array<{ id: string; name: string }>>([]);
  const [compareInit, setCompareInit] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('StudIAMatch_compare_list');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          // eslint-disable-next-line react-hooks/set-state-in-effect
          setCompareList(parsed);
        }
      }
    } catch {}
    setCompareInit(true);
  }, []);

  useEffect(() => {
    if (compareInit) {
      localStorage.setItem('StudIAMatch_compare_list', JSON.stringify(compareList));
    }
  }, [compareList, compareInit]);

  const toggleCompare = (course: Course) => {
    setCompareList(prev => {
      if (prev.find(c => c.id === course.id)) return prev.filter(c => c.id !== course.id);
      if (prev.length >= 3) return prev;
      return [...prev, { id: course.id, name: course.name }];
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
        
        if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) {
          throw new Error("Configuración de Supabase faltante.");
        }

        console.log("🔍 Buscando programa con slug de institución:", institutionSlug, "y slug de curso:", courseSlug);

        // ESTRATEGIA DE BÚSQUEDA ROBUSTA (Múltiples filtros)
        // Escapar parámetros para evitar errores de red y ataques de inyección de URL
        const safeCourseSlug = encodeURIComponent(courseSlug);
        const safeInstSlug = encodeURIComponent(institutionSlug);

        const headers = { 'apikey': SUPABASE_PUBLISHABLE_KEY };
        const [instResponse, categoriesResponse] = await Promise.all([
          fetch(`${SUPABASE_URL}/rest/v1/institutions?select=id,name,slug&slug=eq.${safeInstSlug}&limit=1`, { headers }),
          fetch(`${SUPABASE_URL}/rest/v1/categories?select=id,name`, { headers })
        ]);
        if (!instResponse.ok) throw new Error(`Error cargando institución: ${instResponse.status}`);
        const institutions = await instResponse.json();
        const institution = Array.isArray(institutions) ? institutions[0] : null;
        if (!institution?.id) {
          setErrorInfo(`La institución "${institutionSlug}" no está disponible actualmente.`);
          setLoading(false);
          return;
        }
        const categories = categoriesResponse.ok ? await categoriesResponse.json() : [];
        const categoryArray = Array.isArray(categories) ? categories : [];

        // Buscamos solo en la vista pública H2, que aplica el gate editorial.
        const url = `${SUPABASE_URL}/rest/v1/courses_public_effective?slug=eq.${safeCourseSlug}&institution_id=eq.${encodeURIComponent(institution.id)}&select=${COURSE_PUBLIC_FIELDS}`;

        const response = await fetch(url, { headers });
        
        if (!response.ok) throw new Error(`Error en la respuesta del servidor: ${response.status}`);
        
        let data = await response.json();

        // STRATEGY 2: Fallback to partial slug match OR URL contains slug
        if (!data || data.length === 0) {
          console.warn("⚠️ No encontrado por slug exacto, intentando búsqueda por URL y coincidencia parcial...");
          
          // Intentamos buscar por coincidencia en la URL (muy robusto si el slug se extrajo de ahí)
          const urlMatch = `${SUPABASE_URL}/rest/v1/courses_public_effective?url=ilike.*${safeCourseSlug}*&institution_id=eq.${encodeURIComponent(institution.id)}&select=${COURSE_PUBLIC_FIELDS}&limit=1`;
          const urlRes = await fetch(urlMatch, { headers });
          
          if (urlRes.ok) {
            data = await urlRes.json();
          }

          // STRATEGY 3: Búsqueda difusa en el slug si la URL falló
          if (!data || data.length === 0) {
            const keywords = courseSlug.replace(/-/g, '*');
            const safeKeywords = encodeURIComponent(keywords);
            
            try {
              const likeUrl = `${SUPABASE_URL}/rest/v1/courses_public_effective?slug=ilike.*${safeKeywords}*&institution_id=eq.${encodeURIComponent(institution.id)}&select=${COURSE_PUBLIC_FIELDS}&limit=1`;
              const likeRes = await fetch(likeUrl, { headers });
              
              if (likeRes.ok) {
                data = await likeRes.json();
              }
            } catch (likeErr) {
              console.error("❌ Error en búsqueda parcial:", likeErr);
            }
          }
        }

        if (Array.isArray(data) && data.length > 0) {
          const fetchedCourse = data[0];
          fetchedCourse.institution_name = institution.name || "StudIAMatch";
          fetchedCourse.institution_slug = institution.slug || institutionSlug;
          fetchedCourse.category = categoryArray.find((c: { id: string; name: string }) => c.id === fetchedCourse.category_id)?.name || fetchedCourse.category;
          // Extraer la duración si está implícita en la descripción larga
          if (!fetchedCourse.duration && fetchedCourse.description_long?.startsWith("Duración:")) {
            fetchedCourse.duration = fetchedCourse.description_long.split('\n')[0].replace("Duración:", "").trim();
          }
          setCourse(fetchedCourse);
          console.log("✅ Programa cargado:", fetchedCourse.name);
        } else {
          setErrorInfo(`El programa "${courseSlug}" de la institución "${institutionSlug}" no está disponible actualmente en nuestra base de datos.`);
        }
      } catch (err) {
        console.error("❌ Error crítico en fetch:", err);
        setErrorInfo("Ocurrió un error técnico al conectar con el servidor de datos.");
      } finally {
        setLoading(false);
      }
    };

    if (courseSlug && institutionSlug) fetchCourse();
  }, [courseSlug, institutionSlug]);

  useEffect(() => {
    if (course) {
      const fetchRelatedCourses = async () => {
        if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) return;

        const headers = { 'apikey': SUPABASE_PUBLISHABLE_KEY };
        const safeId = encodeURIComponent(course.id);
        const safeCatId = course.category_id ? encodeURIComponent(course.category_id) : null;
        const safeInstitutionId = course.institution_id ? encodeURIComponent(course.institution_id) : null;

        try {
          if (!safeCatId || !safeInstitutionId) {
            setRelatedCourses([]);
            return;
          }

          const response = await fetch(`${SUPABASE_URL}/rest/v1/courses_public_effective?category_id=eq.${safeCatId}&institution_id=eq.${safeInstitutionId}&id=neq.${safeId}&limit=3&select=${COURSE_PUBLIC_FIELDS}`, { headers });
          const relatedData = response.ok ? await response.json() : [];

          if (Array.isArray(relatedData)) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const enriched = relatedData.map((c: any) => ({
              ...c,
              institution_name: course.institution_name || "StudIAMatch",
              institution_slug: course.institution_slug || "general"
            }));
            setRelatedCourses(enriched as Course[]);
          }
        } catch (error) {
          console.error("Error fetching related courses:", error);
        }
      };
      fetchRelatedCourses();
    }
  }, [course]);

  if (loading || !mounted) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-brand-slate text-white">
      <div className="w-12 h-12 border-4 border-brand-mint border-t-transparent rounded-full animate-spin mb-4"></div>
      <p className="animate-pulse font-bold uppercase tracking-widest text-xs text-brand-mint">Cargando información del programa...</p>
    </div>
  );

  if (errorInfo) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white dark:bg-brand-slate p-6 text-center">
      <div className="bg-red-50 dark:bg-red-500/10 p-10 rounded-[3rem] border border-red-100 dark:border-red-500/20 max-w-lg">
        <h2 className="text-3xl font-bold mb-4 text-brand-slate dark:text-white">Lo sentimos</h2>
        <p className="text-slate-500 dark:text-slate-400 mb-8 leading-relaxed">{errorInfo}</p>
        <Link href="/">
          <Button className="bg-brand-blue text-white rounded-2xl h-12 px-8 font-bold shadow-lg shadow-brand-blue/20">Volver al buscador</Button>
        </Link>
      </div>
    </div>
  );

  if (!course) return null;

  const isValidUrl = (url: string) => {
    try { const p = new URL(url); return p.protocol === 'https:' || p.protocol === 'http:'; }
    catch { return false; }
  };

  // Render text blocks with smart formatting for bullet points and paragraphs
  const renderText = (text: string | undefined) => {
    if (!text) return "Información en proceso de validación.";

    const trimmedText = text.trim();

    // Handle JSON objects: { "section": [...] }
    if (trimmedText.startsWith('{') && trimmedText.endsWith('}')) {
      try {
        const parsed = JSON.parse(trimmedText);
        if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
          const elements: React.ReactNode[] = [];
          let idx = 0;

          Object.entries(parsed).forEach(([key, value]) => {
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
            elements.push(
              <h4 key={`h-${idx}`} className="text-sm font-black uppercase tracking-wider text-brand-blue mt-4 mb-2">
                {label}
              </h4>
            );

            if (Array.isArray(value)) {
              elements.push(
                <ul key={`ul-${idx}`} className="my-2 space-y-1 pl-2">
                  {value.map((item: unknown, i: number) => (
                    <li key={`li-${idx}-${i}`} className="flex items-start gap-2">
                      <span className="text-brand-mint mt-1.5 shrink-0">•</span>
                      <span>{String(item)}</span>
                    </li>
                  ))}
                </ul>
              );
            } else if (typeof value === 'object' && value !== null) {
              elements.push(<p key={`p-${idx}`} className="mb-2 italic">Información estructurada disponible.</p>);
            } else {
              elements.push(<p key={`p-${idx}`} className="mb-2">{String(value)}</p>);
            }

            idx += 1;
          });

          return <div className="text-lg text-slate-600 dark:text-slate-400">{elements}</div>;
        }
      } catch {
        // fallthrough to plain text parser
      }
    }

    let displayLines: string[] = [];
    let isJsonArrayInput = false;

    // Detect JSON arrays (common in AI outputs)
    if (trimmedText.startsWith('[') && trimmedText.endsWith(']')) {
      try {
        const parsed = JSON.parse(trimmedText);
        if (Array.isArray(parsed)) {
          displayLines = parsed.map((item: unknown) => String(item));
          isJsonArrayInput = true;
        } else {
          displayLines = text.split('\n');
        }
      } catch {
        displayLines = text.split('\n');
      }
    } else {
      displayLines = text.split('\n');
    }

    const lines = displayLines.map((line) => line.trim()).filter((line) => line.length > 0);
    const elements: React.ReactNode[] = [];
    let currentList: string[] = [];

    const flushList = () => {
      if (currentList.length > 0) {
        elements.push(
          <ul key={`ul-${elements.length}`} className="my-4 space-y-2 pl-2">
            {currentList.map((item, i) => (
              <li key={`li-${i}`} className="flex items-start gap-2">
                <span className="text-brand-mint mt-1.5 shrink-0">•</span>
                <span>{item.replace(/^[-*•]\s*/, '')}</span>
              </li>
            ))}
          </ul>
        );
        currentList = [];
      }
    };

    lines.forEach((line, i) => {
      const isListItem = /^[-*•]\s+/.test(line) || isJsonArrayInput;
      if (isListItem) {
        currentList.push(line);
      } else {
        flushList();
        elements.push(<p key={`p-${i}`} className="mb-4 last:mb-0 leading-relaxed">{line}</p>);
      }
    });

    flushList();

    return <div className="text-lg text-slate-600 dark:text-slate-400">{elements}</div>;
  };

  return (
    <div className="min-h-screen bg-white dark:bg-brand-slate text-brand-slate dark:text-white font-sans selection:bg-brand-mint/30 pb-20">
      <main className="mx-auto max-w-6xl px-6 py-10">
        <nav className="flex items-center gap-2 text-[11px] text-slate-400 mb-10 font-medium">
          <Link href="/" className="hover:text-brand-blue transition-colors">Home</Link>
          {course?.category && (
            <>
              <span className="text-slate-300">/</span>
              <span className="text-slate-600">{course.category}</span>
            </>
          )}
          {course?.institution_name && (
            <>
              <span className="text-slate-300">/</span>
              <span className="text-slate-600">{course.institution_name}</span>
            </>
          )}
          <span className="text-slate-300">/</span>
          <span className="text-brand-slate dark:text-white font-semibold truncate max-w-[200px]">{course?.name || ""}</span>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-16">
          <div className="lg:col-span-2 space-y-10">
            {!course.is_active && (
              <div className="bg-red-50 border border-red-100 text-red-600 p-4 rounded-xl flex items-center gap-3 text-[11px] font-black uppercase tracking-wider">
                <Info className="h-4 w-4" />
                Programa finalizado o inscripciones cerradas.
              </div>
            )}
            <header className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-blue bg-brand-blue/5 px-2 py-1 rounded">
                    {course.institution_name}
                  </span>
                  <div className="h-1 w-1 rounded-full bg-slate-300" />
                  <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                    {course.course_type}
                  </span>
                </div>
                
                <h1 className="text-4xl md:text-5xl font-black leading-[1.1] tracking-tighter text-brand-slate uppercase">
                  {course.name}
                </h1>

                <div className="flex items-center gap-2 flex-wrap pt-2">
                  {course.category && (
                    <Badge variant="outline" className="border-brand-mint/30 text-brand-mint font-bold uppercase tracking-widest text-[9px] px-3 py-1 bg-brand-mint/5">
                      {course.category}
                    </Badge>
                  )}
                  {course.mode && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full bg-slate-100 text-slate-600">
                      {course.mode.toLowerCase() === 'presencial' ? '🏫' : course.mode.toLowerCase() === 'remoto' ? '🌐' : course.mode.toLowerCase() === 'híbrido' || course.mode.toLowerCase() === 'hibrido' ? '🔀' : ''}
                      {' '}{course.mode}
                    </span>
                  )}
                  {course.certification && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full bg-amber-50 text-amber-700">
                      <Award className="h-3 w-3" /> Certificación
                    </span>
                  )}
                  {course.seniority_level && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full bg-emerald-50 text-emerald-700">
                      <Sprout className="h-3 w-3" /> {course.seniority_level}
                    </span>
                  )}
                </div>
              </div>

              {course.brochure_url && isValidUrl(course.brochure_url) && (
                <div className="pt-4">
                  <a href={course.brochure_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-3 bg-brand-blue text-white px-8 py-3.5 rounded-xl font-black transition-all uppercase tracking-widest text-[10px] shadow-xl shadow-brand-blue/20 hover:scale-105 active:scale-95">
                    <Download className="h-4 w-4" /> Descargar Brochure (PDF)
                  </a>
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 py-8 border-y border-brand-gray/50">
                <div className="space-y-1"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Inicio</p><p className="font-black text-xs text-brand-blue uppercase">{course.start_date_text || "Consultar"}</p></div>
                <div className="space-y-1"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Inversión</p><p className="font-black text-xs text-brand-slate uppercase truncate">{course.price_status === 'consultar' ? "Consultar" : (course.price_pen ? `S/ ${course.price_pen.toLocaleString()}` : "Consultar")}</p></div>
                <div className="space-y-1"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Duración</p><p className="font-black text-xs text-brand-slate uppercase">{course.duration || "N/A"}</p></div>
                <div className="space-y-1"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Modalidad</p><p className="font-black text-xs text-brand-slate uppercase">{course.mode}</p></div>
              </div>
            </header>

            <section className="relative overflow-hidden rounded-[2rem] bg-brand-slate p-10 text-white shadow-2xl border border-white/5">
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-8">
                  <TrendingUp className="h-4 w-4 text-brand-mint" />
                  <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-brand-mint">Análisis de Retorno Educativo</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
                  <div className="space-y-1">
                    <p className="text-[9px] font-bold text-white/40 uppercase tracking-widest">Inversión Total</p>
                    <p className="text-3xl font-black">
                      {course.price_status === 'consultar' ? "S/ --" : (course.price_pen ? `S/ ${course.price_pen.toLocaleString()}` : "S/ --")}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[9px] font-bold text-white/40 uppercase tracking-widest">Salario Sugerido</p>
                    <p className="text-3xl font-black text-brand-mint">
                      {course.expected_monthly_salary ? `S/ ${course.expected_monthly_salary.toLocaleString()}` : "S/ --"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[9px] font-bold text-white/40 uppercase tracking-widest">ROI (Estimado)</p>
                    <p className="text-3xl font-black">{course.roi_months ? `x${Number(course.roi_months).toFixed(1)}` : "—"}</p>
                  </div>
                </div>
                <p className="mt-8 text-[9px] text-white/30 font-bold uppercase tracking-wider leading-relaxed border-t border-white/5 pt-4">
                  * Cálculos basados en Big Data laboral 2026 para {course.category || "tu área"}.
                </p>
              </div>
            </section>

            <section className="space-y-8">
              <div className="flex items-center gap-4 bg-slate-100 dark:bg-white/5 p-2 rounded-2xl w-full md:w-fit overflow-x-auto custom-scrollbar scroll-smooth whitespace-nowrap hide-scrollbar">
                <button 
                  onClick={() => setActiveTab('info')}
                  className={cn("flex-shrink-0 px-6 py-2.5 rounded-xl text-[10px] md:text-xs font-black transition-all uppercase tracking-widest", activeTab === 'info' ? "bg-white dark:bg-brand-blue text-brand-blue dark:text-white shadow-sm" : "text-slate-500 hover:text-slate-700")}
                >GENERAL</button>
                <button 
                  onClick={() => setActiveTab('requisitos')}
                  className={cn("flex-shrink-0 px-6 py-2.5 rounded-xl text-[10px] md:text-xs font-black transition-all uppercase tracking-widest", activeTab === 'requisitos' ? "bg-white dark:bg-brand-blue text-brand-blue dark:text-white shadow-sm" : "text-slate-500 hover:text-slate-700")}
                >REQUISITOS</button>
              </div>

              <div className="min-h-[200px] animate-in fade-in slide-in-from-bottom-2 duration-500">
                {activeTab === 'info' && (
                  <div className="space-y-12">
                    <div className="space-y-4">
                      <h2 className="text-2xl font-bold flex items-center gap-2"><ShieldCheck className="h-6 w-6 text-brand-blue" /> Visión del Programa</h2>
                      <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed text-lg">
                        {course.description_long ? renderText(course.description_long.split('\n\n')[0]) : "Este programa representa una oportunidad estratégica de especialización."}
                      </div>
                    </div>
                    
                    {course.benefits && (
                      <div className="space-y-4 pt-6 border-t border-brand-gray/30">
                        <h2 className="text-2xl font-bold flex items-center gap-2"><ShieldCheck className="h-6 w-6 text-brand-blue" /> Qué Incluye</h2>
                        <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed text-lg">
                          {renderText(course.benefits)}
                        </div>
                      </div>
                    )}

                    {course.objectives && (
                      <div className="space-y-4 pt-6 border-t border-brand-gray/30">
                        <h2 className="text-2xl font-bold flex items-center gap-2"><GraduationCap className="h-6 w-6 text-brand-blue" /> Qué Aprenderás (Objetivos)</h2>
                        <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed text-lg">
                          {renderText(course.objectives)}
                        </div>
                      </div>
                    )}

                    {course.syllabus && (
                      <div className="space-y-4 pt-6 border-t border-brand-gray/30">
                        <h2 className="text-2xl font-bold flex items-center gap-2"><MapPin className="h-6 w-6 text-brand-blue" /> Temario Detallado</h2>
                        <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed text-lg bg-slate-50 dark:bg-white/5 p-8 rounded-3xl border border-dashed border-slate-200 dark:border-white/10">
                          {renderText(course.syllabus)}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'requisitos' && (
                  <div className="space-y-12">
                    {course.target_audience && (
                      <div className="space-y-4">
                        <h2 className="text-2xl font-bold flex items-center gap-2"><CheckCircle className="h-6 w-6 text-brand-blue" /> Perfil del Estudiante</h2>
                        <h4 className="text-xs font-black uppercase tracking-widest text-brand-blue">Dirigido a:</h4>
                        <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed text-lg italic">
                          {renderText(course.target_audience)}
                        </div>
                      </div>
                    )}
                    {course.requirements && (!course.target_audience || course.requirements !== course.target_audience) && (
                      <div className="space-y-4 pt-6 border-t border-brand-gray/30">
                        <h2 className="text-2xl font-bold flex items-center gap-2"><CheckCircle className="h-6 w-6 text-brand-blue" /> Requisitos Previos (Obligatorios)</h2>
                        <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed text-lg">
                          {renderText(course.requirements)}
                        </div>
                      </div>
                    )}
                    {!course.target_audience && !course.requirements && (
                      <div className="text-slate-400 italic py-10">No existen prerrequisitos técnicos estrictos reportados para este programa.</div>
                    )}
                  </div>
                )}
              </div>
            </section>
          </div>

          <div className="lg:col-span-1">
            <Card className="sticky top-24 overflow-hidden border-brand-gray/50 shadow-2xl rounded-[2rem] p-10 bg-white border-0">
              <div className="mb-10 text-center lg:text-left">
                <h3 className="text-2xl font-black uppercase tracking-tight mb-2">Solicitar Asesoría</h3>
                <p className="text-slate-400 text-[11px] font-bold uppercase tracking-wider leading-relaxed">
                  Recibe el plan detallado y asesoría imparcial sobre este programa.
                </p>
              </div>

              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
                <p className="text-[11px] font-black uppercase tracking-widest text-amber-900">Canal cerrado temporalmente</p>
                <p className="mt-3 text-[12px] leading-6 font-semibold text-amber-800/80">
                  StudIAMatch no está capturando datos personales ni enviando solicitudes comerciales mientras se completa la validación editorial H2.
                </p>
              </div>
            <div className="mt-6">
              <button
                onClick={() => toggleCompare(course)}
                className={cn(
                  "w-full flex items-center justify-center gap-2 h-12 rounded-xl font-bold text-[12px] uppercase tracking-wider transition-all active:scale-[0.98] border",
                  compareList.find(c => c.id === course.id)
                    ? "bg-brand-blue border-brand-blue text-white shadow-lg shadow-brand-blue/20"
                    : "bg-white border-slate-200 text-slate-600 hover:border-brand-blue hover:text-brand-blue shadow-md"
                )}
              >
                {compareList.find(c => c.id === course.id) ? "✓ En comparativa" : "+ Agregar a comparativa"}
              </button>
              {compareList.length > 0 && (
                <div className="mt-3 p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
                  <p className="text-[10px] text-slate-400 font-medium">{compareList.length}/3 programas seleccionados</p>
                  <Link href={`/compare?ids=${compareList.map(c => c.id).join(",")}`}>
                    <button className="mt-2 text-[11px] font-bold text-brand-blue hover:text-brand-blue/80 underline underline-offset-2">
                      Ver comparativa
                    </button>
                  </Link>
                </div>
              )}
            </div>
            </Card>
          </div>
        </div>

        {/* Related Courses Section - Minimalist */}
        {relatedCourses.length > 0 && (
          <section className="mt-16 pt-8 border-t border-brand-gray/50">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
              <div className="space-y-3">
                <div className="text-[10px] font-black uppercase tracking-[0.3em] text-brand-blue">Recomendaciones</div>
                <h2 className="text-3xl font-black uppercase tracking-tight">Programas <span className="text-slate-400">Similares</span></h2>
              </div>
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
                Basado en {course.category}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {relatedCourses.map((rc) => (
                <article key={rc.id} className="group relative flex flex-col justify-between rounded-2xl border border-brand-gray/50 bg-white p-6 shadow-premium transition-all hover:-translate-y-1 hover:shadow-2xl hover:border-brand-blue/30 overflow-hidden">
                  <div className="space-y-5">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-black uppercase tracking-widest text-brand-blue bg-brand-blue/5 px-2 py-1 rounded">
                        {rc.institution_name}
                      </span>
                      <GraduationCap className="h-4 w-4 text-slate-200" />
                    </div>
                    <Link href={`/courses/${cleanSlug((rc as Course).institution_slug || 'general')}/${rc.slug}`}>
                      <h3 className="text-base font-black text-brand-slate leading-tight line-clamp-2 h-10 group-hover:text-brand-blue transition-colors uppercase">
                        {rc.name}
                      </h3>
                    </Link>
                    <div className="flex items-center justify-between pt-4 border-t border-brand-gray/30">
                       <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Inversión</span>
                       <span className="text-sm font-black text-brand-slate uppercase">
                         {rc.price_status === 'consultar' ? "S/ --" : (rc.price_pen ? `S/ ${rc.price_pen.toLocaleString()}` : "S/ --")}
                       </span>
                    </div>
                  </div>
                   <Link href={`/courses/${cleanSlug((rc as Course).institution_slug || 'general')}/${rc.slug}`} className="mt-8 flex items-center justify-center rounded-xl bg-slate-50 hover:bg-brand-blue hover:text-white py-3.5 text-[10px] font-black uppercase tracking-widest text-slate-600 transition-all border border-brand-gray/20">
                    Ver Programa
                  </Link>
                </article>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
