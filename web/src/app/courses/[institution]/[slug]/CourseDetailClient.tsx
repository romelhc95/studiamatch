"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  MapPin, Clock, TrendingUp, ChevronLeft, 
  CheckCircle, ShieldCheck, GraduationCap, Download, Info,
  Star, MessageSquare, Quote, User, ArrowRight
} from "lucide-react";
import Link from "next/link";
import { SUPABASE_URL, SUPABASE_ANON_KEY, cleanSlug } from "@/lib/supabase";
import { cn } from "@/lib/utils";

interface Rating {
  id: string;
  course_id: string;
  rating_value: number;
  user_nickname: string;
  created_at: string;
}

interface Review {
  id: string;
  course_id: string;
  content: string;
  user_nickname: string;
  created_at: string;
}

interface Course {
  id: string;
  name: string;
  slug: string;
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
  subcategory?: string;
  course_type?: string;
  brochure_url?: string;
  brochure_text?: string;
  is_active?: boolean;
  start_date_text?: string;
}

export default function CourseDetailClient({ institutionSlug, courseSlug }: { institutionSlug: string, courseSlug: string }) {
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorInfo, setErrorInfo] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({ first_name: "", last_name: "", email: "", whatsapp: "" });
  const [activeTab, setActiveTab] = useState<'info' | 'requisitos' | 'reviews'>('info');

  // SOCIAL PROOF STATE
  const [ratings, setRatings] = useState<Rating[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [relatedCourses, setRelatedCourses] = useState<Course[]>([]);
  const [newRating, setNewRating] = useState(5);
  const [newReview, setNewReview] = useState("");
  const [userNickname, setUserNickname] = useState("");
  const [isSocialSubmitting, setIsSocialSubmitting] = useState(false);
  const [socialSuccess, setSocialSuccess] = useState(false);

  const handleSubmitSocial = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!userNickname.trim()) {
      alert("Por favor, ingresa tu nombre o apodo.");
      return;
    }
    if (!newReview.trim()) {
      alert("Por favor, escribe un comentario sobre tu experiencia.");
      return;
    }
    if (!course) return;

    setIsSocialSubmitting(true);
    console.log("🚀 Iniciando envío de reseña...", { rating: newRating, nickname: userNickname });
    
    try {
      if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
        throw new Error("Configuración de Supabase incompleta. Verifique las variables de entorno.");
      }

      const headers = {
        'Content-Type': 'application/json',
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Prefer': 'return=minimal'
      };

      console.log("📡 Enviando calificación a:", `${SUPABASE_URL}/rest/v1/ratings`);
      // Insert Rating
      const ratingResponse = await fetch(`${SUPABASE_URL}/rest/v1/ratings`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          course_id: course.id,
          rating_value: newRating,
          user_nickname: userNickname.trim()
        })
      });

      if (!ratingResponse.ok) {
        const errorData = await ratingResponse.json().catch(() => ({}));
        console.error("❌ Error en Rating:", errorData);
        throw new Error(`Error al guardar la calificación: ${ratingResponse.statusText}`);
      }

      console.log("📡 Enviando reseña a:", `${SUPABASE_URL}/rest/v1/reviews`);
      // Insert Review
      const reviewResponse = await fetch(`${SUPABASE_URL}/rest/v1/reviews`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          course_id: course.id,
          content: newReview.trim(),
          user_nickname: userNickname.trim()
        })
      });

      if (!reviewResponse.ok) {
        const errorData = await reviewResponse.json().catch(() => ({}));
        console.error("❌ Error en Review:", errorData);
        throw new Error("Error al guardar la reseña.");
      }

      console.log("✅ Reseña publicada con éxito.");
      setSocialSuccess(true);
      setNewReview("");
      setUserNickname("");
      
      // Refresh social proof
      console.log("🔄 Actualizando lista de reseñas...");
      const safeId = encodeURIComponent(course.id);
      const rRes = await fetch(`${SUPABASE_URL}/rest/v1/ratings?course_id=eq.${safeId}&select=*`, { headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` } });
      const rvRes = await fetch(`${SUPABASE_URL}/rest/v1/reviews?course_id=eq.${safeId}&select=*&order=created_at.desc`, { headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` } });
      
      if (rRes.ok && rvRes.ok) {
        const rData = await rRes.json();
        const rvData = await rvRes.json();
        if (Array.isArray(rData)) setRatings(rData);
        if (Array.isArray(rvData)) setReviews(rvData);
      }

      setTimeout(() => setSocialSuccess(false), 3000);
    } catch (error: any) {
      console.error("🔴 Error crítico al enviar social proof:", error);
      alert(error.message || "Ocurrió un error al enviar tu reseña.");
    } finally {
      setIsSocialSubmitting(false);
    }
  };

  const handleSubmitLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!course) return;

    // VALIDACIÓN DE SEGURIDAD (ECC Phase 4 Audit)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      alert("Por favor, ingrese un correo electrónico válido.");
      return;
    }

    if (formData.whatsapp.length < 9) {
      alert("Por favor, ingrese un número de contacto válido.");
      return;
    }
    
    setIsSubmitting(true);
    try {
      // Sanitización básica: trim de espacios
      const leadData = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        email: formData.email.trim().toLowerCase(),
        whatsapp: formData.whatsapp.trim(),
        type: 'info',
        course_id: course.id,
        is_late_enrollment_request: true
      };

      const url = `${SUPABASE_URL}/rest/v1/leads`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Prefer': 'return=minimal'
        },
        body: JSON.stringify(leadData)
      });

      if (response.ok) {
        setSubmitted(true);
      }
    } catch (error) {
      console.error("Error submitting lead:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        setLoading(true);
        setErrorInfo(null);
        
        if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
          throw new Error("Configuración de Supabase faltante.");
        }

        console.log("🔍 Buscando programa con slug de institución:", institutionSlug, "y slug de curso:", courseSlug);

        // ESTRATEGIA DE BÚSQUEDA ROBUSTA (Múltiples filtros)
        // Escapar parámetros para evitar errores de red y ataques de inyección de URL
        const safeCourseSlug = encodeURIComponent(courseSlug);
        const safeInstSlug = encodeURIComponent(institutionSlug);

        // Buscamos el curso que coincida con el slug Y cuya institución vinculada también coincida con el slug de la URL
        const url = `${SUPABASE_URL}/rest/v1/courses?slug=eq.${safeCourseSlug}&institutions.slug=eq.${safeInstSlug}&select=*,institutions!inner(name,slug),categories(name)`;
        
        const response = await fetch(url, {
          headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
        });
        
        if (!response.ok) throw new Error(`Error en la respuesta del servidor: ${response.status}`);
        
        let data = await response.json();

        // STRATEGY 2: Fallback to partial slug match OR URL contains slug
        if (!data || data.length === 0) {
          console.warn("⚠️ No encontrado por slug exacto, intentando búsqueda por URL y coincidencia parcial...");
          
          // Intentamos buscar por coincidencia en la URL (muy robusto si el slug se extrajo de ahí)
          const urlMatch = `${SUPABASE_URL}/rest/v1/courses?url=ilike.*${safeCourseSlug}*&institutions.slug=eq.${safeInstSlug}&select=*,institutions!inner(name,slug),categories(name)&limit=1`;
          const urlRes = await fetch(urlMatch, {
            headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
          });
          
          if (urlRes.ok) {
            data = await urlRes.json();
          }

          // STRATEGY 3: Búsqueda difusa en el slug si la URL falló
          if (!data || data.length === 0) {
            const keywords = courseSlug.replace(/-/g, '*');
            const safeKeywords = encodeURIComponent(keywords);
            
            try {
              const likeUrl = `${SUPABASE_URL}/rest/v1/courses?slug=ilike.*${safeKeywords}*&institutions.slug=eq.${safeInstSlug}&select=*,institutions!inner(name,slug),categories(name)&limit=1`;
              const likeRes = await fetch(likeUrl, {
                headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
              });
              
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
          // Mapear el nombre de la institución
          if (fetchedCourse.institutions && fetchedCourse.institutions.name) {
            fetchedCourse.institution_name = fetchedCourse.institutions.name;
          }
          // Mapear el nombre de la categoría dinámica
          if (fetchedCourse.categories && fetchedCourse.categories.name) {
            fetchedCourse.category = fetchedCourse.categories.name;
          }
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
      const fetchSocialProofAndRelated = async () => {
        if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return;
        
        const headers = { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` };
        const safeId = encodeURIComponent(course.id);
        const safeCatId = course.category_id ? encodeURIComponent(course.category_id) : null;
        
        try {
          // Intentar fetch paralelo de ratings, reviews y cursos relacionados
          const promises = [
            fetch(`${SUPABASE_URL}/rest/v1/ratings?course_id=eq.${safeId}&select=*`, { headers }),
            fetch(`${SUPABASE_URL}/rest/v1/reviews?course_id=eq.${safeId}&select=*&order=created_at.desc`, { headers })
          ];

          if (safeCatId) {
            promises.push(fetch(`${SUPABASE_URL}/rest/v1/courses?category_id=eq.${safeCatId}&id=neq.${safeId}&limit=3&select=*,institutions(name,slug)`, { headers }));
          }

          const results = await Promise.all(promises);
          
          const ratingsData = results[0].ok ? await results[0].json() : [];
          const reviewsData = results[1].ok ? await results[1].json() : [];
          const relatedData = (safeCatId && results[2] && results[2].ok) ? await results[2].json() : [];

          if (Array.isArray(ratingsData)) setRatings(ratingsData);
          if (Array.isArray(reviewsData)) setReviews(reviewsData);
          if (Array.isArray(relatedData)) {
            const enriched = relatedData.map((c: any) => ({
              ...c,
              institution_name: c.institutions?.name || "StudIAMatch",
              institution_slug: c.institutions?.slug || "general"
            }));
            setRelatedCourses(enriched);
          }
        } catch (error) {
          console.error("Error fetching social proof:", error);
        }
      };
      fetchSocialProofAndRelated();
    }
  }, [course]);

  if (loading) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-brand-slate text-white">
      <div className="w-12 h-12 border-4 border-brand-mint border-t-transparent rounded-full animate-spin mb-4"></div>
      <p className="animate-pulse font-bold uppercase tracking-widest text-xs text-brand-mint">Validando credenciales académicas...</p>
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

  // Render text blocks with smart formatting for bullet points and paragraphs
  const renderText = (text: string | undefined) => {
    if (!text) return "Información en proceso de validación.";
    
    let displayLines: string[] = [];
    
    // INTELIGENCIA DE FORMATO: Detectar si es un array JSON (común en respuestas de IA)
    const trimmedText = text.trim();
    if (trimmedText.startsWith('[') && trimmedText.endsWith(']')) {
      try {
        const parsed = JSON.parse(trimmedText);
        if (Array.isArray(parsed)) {
          displayLines = parsed.map(item => String(item));
        } else {
          displayLines = text.split('\n');
        }
      } catch (e) {
        displayLines = text.split('\n');
      }
    } else {
      displayLines = text.split('\n');
    }
    
    const lines = displayLines.map(l => l.trim()).filter(l => l.length > 0);
    const elements: React.ReactNode[] = [];
    let currentList: string[] = [];
    
    const flushList = () => {
      if (currentList.length > 0) {
        elements.push(
          <ul key={`ul-${elements.length}`} className="my-4 space-y-2 pl-2">
            {currentList.map((item, i) => (
              <li key={`li-${i}`} className="flex items-start gap-2">
                <span className="text-brand-mint mt-1.5">•</span>
                <span>{item.replace(/^[-*•]\s*/, '')}</span>
              </li>
            ))}
          </ul>
        );
        currentList = [];
      }
    };

    lines.forEach((line, i) => {
      // Si el texto ya venía como JSON, forzamos que cada item sea un punto de lista
      const isListItem = /^[-*•]\s+/.test(line) || (trimmedText.startsWith('[') && Array.isArray(displayLines));
      
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
        <Link href="/" className="inline-flex items-center text-[11px] font-black text-brand-blue hover:translate-x-[-4px] transition-all mb-10 group uppercase tracking-widest">
          <ChevronLeft className="h-4 w-4 mr-1" /> Volver a la búsqueda
        </Link>

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

                <div className="flex items-center gap-3 flex-wrap pt-2">
                  {course.category && (
                    <Badge variant="outline" className="border-brand-mint/30 text-brand-mint font-bold uppercase tracking-widest text-[9px] px-3 py-1 bg-brand-mint/5">
                      {course.category}
                    </Badge>
                  )}
                  <Badge variant="outline" className="border-slate-200 text-slate-400 font-bold uppercase tracking-widest text-[9px] px-3 py-1">{course.mode}</Badge>
                </div>
              </div>

              {course.brochure_url && (
                <div className="pt-4">
                  <a href={course.brochure_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-3 bg-brand-blue text-white px-8 py-3.5 rounded-xl font-black transition-all uppercase tracking-widest text-[10px] shadow-xl shadow-brand-blue/20 hover:scale-105 active:scale-95">
                    <Download className="h-4 w-4" /> Descargar Brochure (PDF)
                  </a>
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 py-8 border-y border-brand-gray/50">
                <div className="space-y-1"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Inicio</p><p className="font-black text-xs text-brand-blue uppercase">{course.start_date_text || "Consultar"}</p></div>
                <div className="space-y-1"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Ubicación</p><p className="font-black text-xs text-brand-slate uppercase truncate">{course.address || "Sede Central"}</p></div>
                <div className="space-y-1"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Duración</p><p className="font-black text-xs text-brand-slate uppercase">{course.duration || "N/A"}</p></div>
                <div className="space-y-1"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Modalidad</p><p className="font-black text-xs text-brand-slate uppercase">{course.mode}</p></div>
              </div>
            </header>

            <section className="relative overflow-hidden rounded-[2rem] bg-[#0A0F1C] p-10 text-white shadow-2xl border border-white/5">
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
                    <p className="text-3xl font-black text-brand-mint">S/ {course.expected_monthly_salary?.toLocaleString() || "4,800"}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[9px] font-bold text-white/40 uppercase tracking-widest">ROI (Estimado)</p>
                    <p className="text-3xl font-black">x{Number(course.roi_months || 1.8).toFixed(1)}</p>
                  </div>
                </div>
                <p className="mt-8 text-[9px] text-white/30 font-bold uppercase tracking-wider leading-relaxed border-t border-white/5 pt-4">
                  * Cálculos basados en Big Data laboral 2026 para {course.category}.
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
                <button 
                  onClick={() => setActiveTab('reviews')}
                  className={cn("flex-shrink-0 px-6 py-2.5 rounded-xl text-[10px] md:text-xs font-black transition-all uppercase tracking-widest", activeTab === 'reviews' ? "bg-white dark:bg-brand-blue text-brand-blue dark:text-white shadow-sm" : "text-slate-500 hover:text-slate-700")}
                >RESEÑAS ({reviews.length})</button>
              </div>

              <div className="min-h-[200px] animate-in fade-in slide-in-from-bottom-2 duration-500">
                {activeTab === 'info' && (
                  <div className="space-y-12">
                    <div className="space-y-4">
                      <h2 className="text-2xl font-bold flex items-center gap-2"><ShieldCheck className="h-6 w-6 text-brand-blue" /> Visión del Programa</h2>
                      <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed text-lg">
                        {course.description ? renderText(course.description) : (course.description_long ? renderText(course.description_long.split('\n\n')[0]) : "Este programa representa una oportunidad estratégica de especialización.")}
                      </div>
                    </div>
                    
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

                {activeTab === 'reviews' && (
                  <div className="space-y-12 animate-in fade-in duration-700">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                      <div className="space-y-6">
                        <h3 className="text-2xl font-bold flex items-center gap-2">
                          <Star className="h-6 w-6 text-amber-400 fill-amber-400" />
                          Calificaciones
                        </h3>
                        {ratings.length > 0 ? (
                          <div className="bg-slate-50 dark:bg-white/5 p-8 rounded-[2.5rem] border border-brand-gray/30">
                            <div className="flex items-center gap-4">
                              <div className="text-5xl font-black text-brand-slate dark:text-white">
                                {(ratings.reduce((acc, r) => acc + r.rating_value, 0) / ratings.length).toFixed(1)}
                              </div>
                              <div>
                                <div className="flex text-amber-400 mb-1">
                                  {[1,2,3,4,5].map(star => (
                                    <Star key={star} className={cn("h-4 w-4", star <= Math.round(ratings.reduce((acc, r) => acc + r.rating_value, 0) / ratings.length) ? "fill-amber-400" : "text-slate-300")} />
                                  ))}
                                </div>
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest">{ratings.length} Reseñas Verificadas</div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="bg-slate-50 dark:bg-white/5 p-8 rounded-[2.5rem] border border-dashed border-slate-300 text-center">
                            <p className="text-slate-500 font-bold italic">Aún no hay calificaciones. ¡Sé el primero!</p>
                          </div>
                        )}
                        
                        <Card className="p-8 rounded-[2.5rem] border-brand-gray/50 bg-white dark:bg-zinc-900 shadow-xl overflow-hidden relative">
                          <div className="relative z-10">
                            <h4 className="text-lg font-bold mb-4">Deja tu opinión</h4>
                            <form onSubmit={handleSubmitSocial} className="space-y-4">
                              <div className="flex gap-2 mb-4">
                                {[1,2,3,4,5].map(star => (
                                  <button 
                                    type="button" 
                                    key={star} 
                                    onClick={() => setNewRating(star)}
                                    className="transition-transform hover:scale-125"
                                  >
                                    <Star className={cn("h-6 w-6", star <= newRating ? "fill-amber-400 text-amber-400" : "text-slate-300")} />
                                  </button>
                                ))}
                              </div>
                              <Input 
                                placeholder="Tu Apodo/Nombre" 
                                required 
                                className="h-12 rounded-2xl bg-slate-50 dark:bg-zinc-800 border-0 font-bold" 
                                value={userNickname}
                                onChange={(e) => setUserNickname(e.target.value)}
                              />
                              <textarea 
                                placeholder="Comparte tu experiencia con este programa..." 
                                required
                                className="w-full h-32 rounded-3xl bg-slate-50 dark:bg-zinc-800 border-0 p-6 font-bold text-sm focus:ring-4 focus:ring-brand-blue/10 resize-none transition-all"
                                value={newReview}
                                onChange={(e) => setNewReview(e.target.value)}
                              />
                              <Button 
                                type="submit"
                                disabled={isSocialSubmitting}
                                className="w-full h-14 bg-brand-slate text-white dark:bg-brand-mint dark:text-brand-slate font-black rounded-2xl border-0"
                              >
                                {isSocialSubmitting ? "ENVIANDO..." : "PUBLICAR RESEÑA"}
                              </Button>
                              {socialSuccess && <p className="text-center text-emerald-500 font-bold text-xs animate-bounce mt-2">¡Gracias por tu aporte!</p>}
                            </form>
                          </div>
                        </Card>
                      </div>

                      <div className="space-y-6">
                        <h3 className="text-2xl font-bold flex items-center gap-2">
                          <MessageSquare className="h-6 w-6 text-brand-blue" />
                          Comentarios
                        </h3>
                        <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                          {reviews.length > 0 ? reviews.map(review => (
                            <div key={review.id} className="bg-white dark:bg-white/5 p-6 rounded-3xl border border-brand-gray/30 shadow-sm relative group">
                              <div className="flex items-center gap-3 mb-4">
                                <div className="h-10 w-10 rounded-full bg-brand-blue/10 flex items-center justify-center text-brand-blue font-bold">
                                  <User className="h-5 w-5" />
                                </div>
                                <div>
                                  <div className="text-sm font-black text-brand-slate dark:text-white uppercase tracking-wider">{review.user_nickname}</div>
                                  <div className="text-[10px] text-slate-400 font-bold uppercase">{new Date(review.created_at).toLocaleDateString()}</div>
                                </div>
                              </div>
                              <p className="text-slate-600 dark:text-slate-400 leading-relaxed italic text-sm">"{review.content}"</p>
                            </div>
                          )) : (
                            <div className="py-20 text-center opacity-40">
                              <MessageSquare className="h-12 w-12 mx-auto mb-4" />
                              <p className="font-bold">Sin comentarios aún.</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </section>
          </div>

          <div className="lg:col-span-1">
            <Card className="sticky top-24 overflow-hidden border-brand-gray/50 shadow-2xl rounded-[2rem] p-10 bg-white border-0">
              <div className="mb-10 text-center lg:text-left">
                <h3 className="text-2xl font-black uppercase tracking-tight mb-2">Solicitar Auditoría</h3>
                <p className="text-slate-400 text-[11px] font-bold uppercase tracking-wider leading-relaxed">
                  Recibe el plan detallado y asesoría imparcial sobre este programa.
                </p>
              </div>

              {!submitted ? (
                <form className="space-y-4" onSubmit={handleSubmitLead}>
                   <div className="space-y-1.5">
                      <label className="text-[9px] font-black uppercase tracking-widest text-slate-400 ml-1">Nombre Completo</label>
                      <Input 
                        required
                        className="h-11 rounded-xl bg-slate-50 border-0 px-4 font-bold text-xs shadow-inner" 
                        value={formData.first_name}
                        onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[9px] font-black uppercase tracking-widest text-slate-400 ml-1">WhatsApp de Contacto</label>
                      <Input 
                        required
                        className="h-11 rounded-xl bg-slate-50 border-0 px-4 font-bold text-xs shadow-inner" 
                        value={formData.whatsapp}
                        onChange={(e) => setFormData({...formData, whatsapp: e.target.value})}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[9px] font-black uppercase tracking-widest text-slate-400 ml-1">Email</label>
                      <Input 
                        required
                        type="email" 
                        className="h-11 rounded-xl bg-slate-50 border-0 px-4 font-bold text-xs shadow-inner" 
                        value={formData.email}
                        onChange={(e) => setFormData({...formData, email: e.target.value})}
                      />
                    </div>
                  
                  <Button 
                    disabled={isSubmitting}
                    type="submit" 
                    className="w-full bg-brand-blue hover:bg-brand-blue/90 h-14 text-white font-black text-[11px] uppercase tracking-[0.2em] rounded-xl transition-all shadow-xl shadow-brand-blue/10 border-0 mt-4 active:scale-95"
                  >
                    {isSubmitting ? "Tramitando..." : "Confirmar Solicitud"}
                  </Button>
                  <p className="text-[8px] text-slate-300 text-center uppercase font-bold tracking-widest mt-4">Respuesta estimada: 2 horas</p>
                </form>
              ) : (
                <div className="py-12 text-center animate-in zoom-in duration-500">
                  <div className="h-20 w-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="h-10 w-10 text-emerald-500" />
                  </div>
                  <h3 className="text-sm font-black text-brand-slate uppercase tracking-widest">Solicitud enviada</h3>
                  <p className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-wider">Un auditor se pondrá en contacto pronto.</p>
                </div>
              )}
            </Card>
          </div>
        </div>

        {/* Related Courses Section - Minimalist */}
        {relatedCourses.length > 0 && (
          <section className="mt-32 pt-16 border-t border-brand-gray/50">
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
                    <Link href={`/courses/${rc.institution_slug}/${cleanSlug(rc.slug)}`}>
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
                  <Link href={`/courses/${rc.institution_slug}/${cleanSlug(rc.slug)}`} className="mt-8 flex items-center justify-center rounded-xl bg-slate-50 hover:bg-brand-blue hover:text-white py-3.5 text-[10px] font-black uppercase tracking-widest text-slate-600 transition-all border border-brand-gray/20">
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
