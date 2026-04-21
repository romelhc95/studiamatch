"use client";

import { useEffect, useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, TrendingUp, ChevronDown, X, GraduationCap, CheckCircle2, ArrowRight, SlidersHorizontal, Building2, Globe, Coins, LayoutGrid } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { SUPABASE_URL, SUPABASE_ANON_KEY, cleanSlug, type Course, type Institution } from "@/lib/supabase";

export default function Home() {
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCourseForInfo, setSelectedCourseForInfo] = useState<Course | null>(null);
  const [modalType, setModalType] = useState<'recommendation' | 'info'>('recommendation');
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  const [activeFilters, setActiveFilters] = useState({
    priceMin: "",
    priceMax: "",
    modes: [] as string[],
    durations: [] as string[],
    selectedInstitution: "Todas",
    includeConsultar: true
  });

  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("Todos");
  const [courseTypes, setCourseTypes] = useState<string[]>([]);
  const [selectedType, setSelectedType] = useState<string>("Todos");

  // INTELLIGENT FILTERS: Only show options that have courses
  const stats = useMemo(() => {
    const counts = {
      categories: {} as Record<string, number>,
      types: {} as Record<string, number>,
      institutions: {} as Record<string, number>
    };

    allCourses.forEach(c => {
      if (c.category) counts.categories[c.category] = (counts.categories[c.category] || 0) + 1;
      if (c.course_type) counts.types[c.course_type] = (counts.types[c.course_type] || 0) + 1;
      if (c.institution_name) counts.institutions[c.institution_name] = (counts.institutions[c.institution_name] || 0) + 1;
    });

    return counts;
  }, [allCourses]);

  const activeCategories = useMemo(() => ["Todos", ...Object.keys(stats.categories).sort()], [stats]);
  const activeTypes = useMemo(() => ["Todos", ...Object.keys(stats.types).sort()], [stats]);
  const activeInstitutions = useMemo(() => ["Todas", ...Object.keys(stats.institutions).sort()], [stats]);

  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 12;
  const [compareList, setCompareList] = useState<Course[]>([]);
  const [isCompareInitialized, setIsCompareInitialized] = useState(false);

  // PERSISTENCE: Load compareList ONCE on mount
  useEffect(() => {
    const savedCompare = localStorage.getItem('StudIAMatch_compare_list');
    if (savedCompare) {
      try {
        const parsed = JSON.parse(savedCompare);
        if (Array.isArray(parsed)) setCompareList(parsed);
      } catch (e) {
        console.error("Error parsing saved comparison list", e);
      }
    }
    setIsCompareInitialized(true);
  }, []);

  // PERSISTENCE: Only SAVE after initialization to prevent overwriting with empty array
  useEffect(() => {
    if (isCompareInitialized) {
      localStorage.setItem('StudIAMatch_compare_list', JSON.stringify(compareList));
    }
  }, [compareList, isCompareInitialized]);

  const [formData, setFormData] = useState({ first_name: "", last_name: "", email: "", whatsapp: "", area_interest: "", budget: "", modality: "Remoto", description: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const headers = { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` };
        const [cRes, iRes] = await Promise.all([
          fetch(`${SUPABASE_URL}/rest/v1/courses?is_active=eq.true&is_verified=eq.true&select=id,name,slug,url,institution_id,price_pen,price_status,mode,course_type,category_id,duration,start_date_text,categories(name),institutions(name,slug)&order=created_at.desc`, { headers }),
          fetch(`${SUPABASE_URL}/rest/v1/institutions?select=id,name,slug`, { headers })
        ]);
        const [cData, iData] = await Promise.all([cRes.json(), iRes.json()]);

        if (Array.isArray(cData) && Array.isArray(iData)) {
          const enriched = cData.map((course: any) => ({
            ...course,
            institution_name: course.institutions?.name || iData.find((i: Institution) => i.id === course.institution_id)?.name || "StudIAMatch",
            institution_slug: course.institutions?.slug || iData.find((i: Institution) => i.id === course.institution_id)?.slug || "general",
            category: course.categories?.name || course.category
          }));

          // De-duplicación por URL e Institución
          // Si dos registros tienen la misma URL en la misma institución, son el mismo curso real.
          const uniqueMap = new Map<string, any>();
          
          enriched.forEach((course: any) => {
            const key = `${course.institution_id}-${course.url || course.slug}`;
            const existing = uniqueMap.get(key);
            
            if (!existing) {
              uniqueMap.set(key, course);
            } else {
              // Si ya existe, preferir "Programa" sobre "Curso"
              if (course.course_type === 'Programa' && existing.course_type !== 'Programa') {
                uniqueMap.set(key, course);
              }
              // Si ambos son lo mismo, el que ya está se queda (ordenado por created_at desc)
            }
          });

          setAllCourses(Array.from(uniqueMap.values()));
        }
      } catch (error) {
        console.error("Error cargando datos:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSubmitLead = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const leadData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        whatsapp: formData.whatsapp,
        type: modalType,
        course_id: selectedCourseForInfo?.id || null,
        area_interest: formData.area_interest || (modalType === 'info' ? selectedCourseForInfo?.category : ""),
        budget: formData.budget ? parseFloat(formData.budget.replace(/[^0-9.]/g, '')) : null,
        modality: formData.modality,
        description: formData.description
      };

      const response = await fetch(`${SUPABASE_URL}/rest/v1/leads`, {
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
        setIsSuccess(true);
        setTimeout(() => {
          setIsModalOpen(false);
          setIsSuccess(false);
          setFormData({ first_name: "", last_name: "", email: "", whatsapp: "", area_interest: "", budget: "", modality: "Remoto", description: "" });
        }, 2500);
      }
    } catch (error) {
      console.error("Error submitting lead:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openModal = (type: 'recommendation' | 'info', course: Course | null = null) => {
    setModalType(type);
    setSelectedCourseForInfo(course);
    setIsModalOpen(true);
    setIsSuccess(false);
  };

  const filteredCourses = useMemo(() => {
    let result = [...allCourses];

    if (searchTerm) {
      const norm = (t: string) => t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
      const s = norm(searchTerm);
      result = result.filter(c => norm(c.name || "").includes(s) || norm(c.institution_name || "").includes(s));
    }
    if (selectedCategory !== "Todos") result = result.filter(c => c.category === selectedCategory);
    if (selectedType !== "Todos") result = result.filter(c => c.course_type === selectedType);

    if (activeFilters.selectedInstitution !== "Todas") {
      result = result.filter(c =>
        c.institution_name?.toLowerCase().trim() === activeFilters.selectedInstitution.toLowerCase().trim()
      );
    }

    // Deduplicación visual: Un solo curso por combinación de slug e institución
    const uniqueMap = new Map<string, Course>();
    result.forEach(c => {
      const key = `${(c as any).institution_slug}-${c.slug}`;
      const existing = uniqueMap.get(key);
      // Priorizar el que tenga precio o nombre más descriptivo
      if (!existing || (!existing.price_pen && c.price_pen) || (c.name.length > existing.name.length)) {
        uniqueMap.set(key, c);
      }
    });
    result = Array.from(uniqueMap.values());

    return result.filter(c => {
      if (activeFilters.modes.length > 0 && !activeFilters.modes.includes(c.mode)) return false;
      const price = c.price_pen;
      if (price === null) {
        if ((activeFilters.priceMin || activeFilters.priceMax) && !activeFilters.includeConsultar) return false;
      } else {
        if (activeFilters.priceMin && price < parseFloat(activeFilters.priceMin)) return false;
        if (activeFilters.priceMax && price > parseFloat(activeFilters.priceMax)) return false;
      }
      return true;
    });
  }, [allCourses, activeFilters, searchTerm, selectedCategory, selectedType]);

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedCategory, activeFilters]);

  // Pagination logic
  const totalPages = Math.ceil(filteredCourses.length / ITEMS_PER_PAGE);
  const paginatedCourses = filteredCourses.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  return (
    <div className="min-h-screen bg-white text-brand-slate font-sans selection:bg-brand-blue/10">

      {/* ── Hero ────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-brand-slate" />
        <div className="absolute inset-0 opacity-[0.02]" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '24px 24px' }} />
        <div className="absolute bottom-0 left-1/4 w-64 h-64 md:w-96 md:h-96 bg-brand-blue/20 rounded-full blur-[100px]" />
        <div className="absolute top-0 right-1/4 w-48 h-48 bg-brand-mint/10 rounded-full blur-[80px]" />

        <div className="relative mx-auto max-w-6xl px-6 pt-8 pb-8 md:pt-14 md:pb-12">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 lg:gap-10">
            <div className="max-w-2xl space-y-3 md:space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full bg-white/[0.06] px-3 py-1 border border-white/[0.08]">
                <div className="h-1.5 w-1.5 rounded-full bg-brand-mint" />
                <span className="text-[11px] font-medium text-white/50">
                  Stud<span className="text-brand-blue font-bold">IA</span>Match · Data-driven decisions
                </span>
              </div>

              <h1 className="text-2xl md:text-4xl font-bold leading-[1.15] tracking-tight text-white text-balance">
                Elige tu próximo programa con{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-blue to-brand-mint">datos reales</span>
              </h1>

              <p className="text-sm md:text-base text-slate-300 leading-relaxed max-w-lg font-medium">
                Compara inversión, contenido y retorno financiero de programas tech en Perú.
              </p>

              <div id="hero-search" className="pt-2 max-w-4xl scroll-mt-32 w-full">
                {/* ── Filter Chips (Google Flights Style) ──────────────── */}
                <div className="flex flex-wrap items-center gap-2 mb-3 px-1 overflow-x-auto no-scrollbar pb-1">
                  {[
                    { id: 'area', label: 'Área', icon: LayoutGrid, current: selectedCategory, setter: setSelectedCategory, options: activeCategories },
                    { id: 'tipo', label: 'Tipo', icon: GraduationCap, current: selectedType, setter: setSelectedType, options: activeTypes },
                    { id: 'inst', label: 'Institución', icon: Building2, current: activeFilters.selectedInstitution, setter: (val: string) => setActiveFilters({ ...activeFilters, selectedInstitution: val }), options: activeInstitutions },
                    { id: 'modalidad', label: 'Modalidad', icon: Globe, current: activeFilters.modes.length ? activeFilters.modes.join(", ") : "Todas", setter: (val: string) => setActiveFilters({ ...activeFilters, modes: val === "Todas" ? [] : [val] }), options: ["Todas", "Presencial", "Semipresencial", "Remoto", "Híbrido"] },
                  ].map((filter) => (
                    <div key={filter.id} className="relative">
                      <button
                        onClick={() => setActiveDropdown(activeDropdown === filter.id ? null : filter.id)}
                        className={cn(
                          "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all border",
                          activeDropdown === filter.id || (filter.current !== "Todos" && filter.current !== "Todas" && filter.current !== "Cualquier precio")
                            ? "bg-brand-blue/10 border-brand-blue text-brand-blue shadow-sm"
                            : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:border-white/20"
                        )}
                      >
                        <filter.icon className="h-3.5 w-3.5" />
                        <span className="max-w-[120px] truncate">{filter.current === "Todos" || filter.current === "Todas" || filter.current === "Cualquier precio" ? filter.label : filter.current}</span>
                        <ChevronDown className={cn("h-3 w-3 opacity-50 transition-transform", activeDropdown === filter.id && "rotate-180")} />
                      </button>

                      {activeDropdown === filter.id && (
                        <>
                          <div className="fixed inset-0 z-40" onClick={() => setActiveDropdown(null)} />
                          <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-xl shadow-elevated border border-slate-100 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100 origin-top-left">
                            <div className="p-1.5 max-h-72 overflow-y-auto custom-scrollbar">
                              {filter.options.map((opt) => (
                                <button
                                  key={opt}
                                  onClick={() => {
                                    filter.setter(opt === "Cualquier precio" ? "" : opt);
                                    setActiveDropdown(null);
                                  }}
                                  className={cn(
                                    "w-full text-left px-3 py-2 rounded-lg text-[13px] transition-all flex items-center justify-between",
                                    filter.current === opt || (opt === "Cualquier precio" && filter.current === "")
                                      ? "bg-brand-blue text-white font-semibold"
                                      : "hover:bg-slate-50 text-slate-600"
                                  )}
                                >
                                  <span className="truncate">{opt}</span>
                                  {filter.id !== 'modalidad' && filter.id !== 'precio' && opt !== "Todos" && opt !== "Todas" && (
                                    <span className={cn(
                                      "text-[10px] tabular-nums px-1.5 py-0.5 rounded",
                                      filter.current === opt ? "bg-white/20" : "bg-slate-100 text-slate-400"
                                    )}>
                                      {(stats as any)[filter.id === 'area' ? 'categories' : (filter.id === 'inst' ? 'institutions' : 'types')][opt] || 0}
                                    </span>
                                  )}
                                </button>
                              ))}
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>

                {/* ── Main Search Bar ──────────────────────────── */}
                <div className="flex flex-col md:flex-row shadow-2xl rounded-2xl bg-white p-2 gap-2 focus-within:ring-4 focus-within:ring-brand-blue/20 transition-all border border-white/10 group">
                  <div className="relative flex-1">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                      <Search className="h-5 w-5 text-slate-300 group-focus-within:text-brand-blue transition-colors" />
                    </div>
                    <Input
                      placeholder="¿Qué quieres estudiar hoy? (Nombre, tecnología o palabra clave)"
                      className="pl-12 h-14 bg-transparent border-0 text-brand-slate font-medium text-base placeholder:text-slate-400 focus-visible:ring-0 rounded-xl"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>

                  <div className="h-10 w-px bg-slate-100 self-center hidden md:block" />

                  <div className="relative w-full md:w-36 flex items-center px-4">
                    <Coins className="h-5 w-5 text-slate-300 mr-2 shrink-0" />
                    <Input
                      type="number"
                      placeholder="Máx S/"
                      className="h-14 bg-transparent border-0 text-brand-slate font-semibold text-base placeholder:text-slate-400 focus-visible:ring-0 px-0 w-full"
                      value={activeFilters.priceMax}
                      onChange={(e) => setActiveFilters({ ...activeFilters, priceMax: e.target.value })}
                    />
                  </div>

                  <Button
                    onClick={() => document.getElementById('programas')?.scrollIntoView({ behavior: 'smooth' })}
                    className="w-full md:w-auto bg-brand-blue hover:bg-brand-blue/90 text-white font-bold rounded-xl px-10 h-14 text-sm transition-all hover:shadow-lg active:scale-[0.98]"
                  >
                    Explorar
                  </Button>
                </div>
              </div>
            </div>

            {/* Stats — hidden on mobile */}
            <div className="hidden md:flex items-center gap-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-white tabular-nums">+{allCourses.length || 0}</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Programas</p>
              </div>
              <div className="h-8 w-px bg-white/10" />
              <div className="text-center">
                <p className="text-3xl font-bold text-brand-mint tabular-nums">{Object.keys(stats.institutions).length}</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Instituciones</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Catalog ─────────────────────────────────────── */}
      <div id="programas" className="mx-auto max-w-6xl px-6 py-8 scroll-mt-16">

        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold tracking-tight">Programas</h2>
            <p className="text-[13px] text-slate-400 mt-0.5">{filteredCourses.length} resultados</p>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6 relative items-start">
          <main className="flex-1 min-w-0">
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-40 rounded-xl bg-slate-50 animate-pulse" />
                ))}
              </div>
            ) : filteredCourses.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 transition-all duration-300">
                {paginatedCourses.map((course) => (
                  <article key={course.id} className="group flex flex-col bg-white rounded-xl border border-slate-100 hover:border-slate-200 transition-all duration-200 hover:shadow-card overflow-hidden">
                    {/* Card Body */}
                    <div className="p-5 flex-1 flex flex-col">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-[11px] font-medium text-slate-400">{course.institution_name}</span>
                        <span className="text-[11px] font-medium text-brand-blue bg-brand-blue/5 px-2 py-0.5 rounded-md">{course.course_type || "Programa"}</span>
                      </div>

                      <Link href={`/courses/${cleanSlug((course as any).institution_slug)}/${cleanSlug(course.slug, course.url)}`} className="group/title flex-1">
                        <h3 className="text-[15px] font-semibold text-brand-slate leading-snug group-hover/title:text-brand-blue transition-colors line-clamp-2">
                          {course.name}
                        </h3>
                      </Link>

                      {course.category && (
                        <p className="text-[12px] text-slate-400 mt-1.5">{course.category}</p>
                      )}

                      <div className="mt-4 pt-3 border-t border-slate-50">
                        <div className="grid grid-cols-2 gap-y-3">
                          <div>
                            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Inversión</p>
                            <p className="text-[13px] font-semibold text-brand-slate tabular-nums truncate">
                              {course.price_status === 'consultar' ? "Consultar" : (course.price_pen ? `S/ ${course.price_pen.toLocaleString()}` : "Consultar")}
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Modalidad</p>
                            <p className="text-[13px] font-semibold text-brand-slate capitalize truncate">{course.mode || "No especificada"}</p>
                          </div>
                          <div>
                            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Duración</p>
                            <p className="text-[13px] font-semibold text-brand-slate truncate">{(course as any).duration || "No especificada"}</p>
                          </div>
                          <div>
                            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Inicio</p>
                            <p className="text-[13px] font-semibold text-brand-slate truncate">{(course as any).start_date_text || "Consultar"}</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="px-5 pb-4 pt-0 flex items-center gap-2">
                      <Link href={`/courses/${cleanSlug((course as any).institution_slug)}/${cleanSlug(course.slug, course.url)}`} className="flex-1 flex items-center justify-center gap-1.5 h-9 rounded-lg bg-slate-50 hover:bg-slate-100 text-[13px] font-medium text-slate-600 transition-colors">
                        Ver detalle <ArrowRight className="h-3 w-3" />
                      </Link>
                      <button
                        onClick={() => {
                          setCompareList(prev => {
                            if (prev.find(c => c.id === course.id)) return prev.filter(c => c.id !== course.id);
                            if (prev.length >= 3) return prev;
                            return [...prev, course];
                          });
                        }}
                        className={cn(
                          "h-9 px-3 rounded-lg border text-[13px] font-medium transition-all",
                          compareList.find(c => c.id === course.id)
                            ? "bg-brand-blue border-brand-blue text-white"
                            : "border-slate-200 text-slate-400 hover:border-brand-blue hover:text-brand-blue"
                        )}
                      >
                        {compareList.find(c => c.id === course.id) ? "✓" : "+"}
                      </button>
                      <Button
                        onClick={() => openModal('info', course)}
                        size="sm"
                        className="h-9 rounded-lg bg-brand-blue hover:bg-brand-blue/90 text-white text-[13px] font-medium border-0 shadow-none"
                      >
                        Info
                      </Button>
                    </div>
                  </article>
                ))}

                {totalPages > 1 && (
                  <div className="flex justify-center items-center gap-4 col-span-full pt-6">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage === 1}
                      onClick={() => {
                        setCurrentPage(prev => Math.max(1, prev - 1));
                        document.getElementById('programas')?.scrollIntoView({ behavior: 'smooth' });
                      }}
                      className="rounded-lg h-9 text-[13px]"
                    >
                      Anterior
                    </Button>
                    <span className="text-[13px] text-slate-400 tabular-nums">{currentPage} / {totalPages}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage === totalPages}
                      onClick={() => {
                        setCurrentPage(prev => Math.min(totalPages, prev + 1));
                        document.getElementById('programas')?.scrollIntoView({ behavior: 'smooth' });
                      }}
                      className="rounded-lg h-9 text-[13px] border-brand-blue text-brand-blue hover:bg-brand-blue hover:text-white"
                    >
                      Siguiente
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-20 text-center rounded-xl border-2 border-dashed border-slate-100">
                <Search className="h-10 w-10 text-slate-200 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-400">Sin resultados</h3>
                <p className="text-[13px] text-slate-400 mt-1 mb-6">Intenta con otros filtros.</p>
                <Button variant="outline" size="sm" onClick={() => { setSearchTerm(""); setSelectedCategory("Todos"); setActiveFilters({ ...activeFilters, priceMax: "", modes: [] }); }} className="rounded-lg text-[13px]">Reiniciar filtros</Button>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* ── Compare Bar ────────────────────────────────── */}
      {compareList.length > 0 && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[60] animate-in slide-in-from-bottom-4 duration-300">
          <div className="bg-brand-slate backdrop-blur-xl rounded-full px-4 py-2 shadow-elevated border border-white/10 flex items-center gap-4">
            <div className="flex -space-x-2">
              {compareList.map(c => <div key={c.id} className="h-8 w-8 rounded-full border-2 border-brand-slate bg-brand-blue flex items-center justify-center text-white font-semibold text-[10px]">{c.name.charAt(0)}</div>)}
            </div>
            <span className="text-white text-[13px] font-medium hidden sm:inline">{compareList.length} programas</span>
            <button onClick={() => setCompareList([])} className="text-white/40 hover:text-white text-[13px] transition-colors">Limpiar</button>
            <Link href={`/compare?ids=${compareList.map(c => c.id).join(",")}`}>
              <Button size="sm" className="bg-brand-mint hover:bg-brand-mint/90 text-brand-slate font-semibold rounded-full h-9 px-5 border-0 text-[13px]">Comparar</Button>
            </Link>
          </div>
        </div>
      )}

      {/* ── Cómo Funciona ──────────────────────────────── */}
      <section id="como-funciona" className="py-16 bg-slate-50/50 scroll-mt-16">
        <div className="mx-auto max-w-6xl px-6">
          <div className="max-w-lg mb-10">
            <p className="text-[13px] font-medium text-brand-blue mb-1.5">Metodología</p>
            <h2 className="text-2xl font-bold tracking-tight">¿Cómo funciona StudIAMatch?</h2>
            <p className="text-[14px] text-slate-400 mt-2 leading-relaxed">Tres pilares para garantizar la transparencia de tu inversión educativa.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {[
              { step: '01', title: 'Curación', desc: 'Auditamos programas bajo una matriz de 14 pilares de calidad.', icon: Search },
              { step: '02', title: 'Análisis', desc: 'Calculamos el ROI basado en salarios de mercado actuales.', icon: TrendingUp },
              { step: '03', title: 'Decisión', desc: 'Ruta imparcial sin sesgo institucional.', icon: CheckCircle2 },
            ].map((item) => (
              <div key={item.step} className="bg-white p-6 rounded-xl border border-slate-100 hover:border-slate-200 transition-all hover:shadow-card group">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[12px] font-semibold text-slate-300">{item.step}</span>
                  <item.icon className="h-4 w-4 text-brand-blue opacity-60 group-hover:opacity-100 transition-opacity" />
                </div>
                <h3 className="text-[15px] font-semibold text-brand-slate mb-1.5">{item.title}</h3>
                <p className="text-[13px] text-slate-400 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Nosotros ───────────────────────────────────── */}
      <section id="nosotros" className="py-16 scroll-mt-16">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <div className="flex-1 space-y-5">
              <p className="text-[13px] font-medium text-brand-blue">Nuestra misión</p>
              <h2 className="text-2xl font-bold tracking-tight text-balance">
                Democratizar la inteligencia educativa en Perú.
              </h2>
              <p className="text-[14px] text-slate-400 leading-relaxed">
                En un mercado saturado de promesas, aportamos claridad. Consolidamos datos reales de instituciones para que tomes decisiones basadas en mérito y retorno financiero.
              </p>
              <div className="flex gap-3 pt-1">
                <div className="px-4 py-3 rounded-lg bg-slate-50 border border-slate-100">
                  <p className="text-[11px] text-slate-400 mb-0.5">Principio</p>
                  <p className="text-[13px] font-semibold text-brand-slate">Transparencia total</p>
                </div>
                <div className="px-4 py-3 rounded-lg bg-slate-50 border border-slate-100">
                  <p className="text-[11px] text-slate-400 mb-0.5">Principio</p>
                  <p className="text-[13px] font-semibold text-brand-slate">Datos verificados</p>
                </div>
              </div>
            </div>
            <div className="flex-1 w-full max-w-md">
              <div className="aspect-[4/3] rounded-xl bg-brand-slate flex items-center justify-center relative overflow-hidden">
                <div className="text-center">
                  <p className="text-5xl font-bold text-brand-mint tabular-nums">+{allCourses.length}</p>
                  <p className="text-[12px] text-white/30 mt-1">Benchmarks auditados</p>
                </div>
                <div className="absolute inset-0 bg-gradient-to-tr from-brand-blue/15 to-transparent pointer-events-none" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 pb-16">
        <div className="rounded-xl bg-brand-blue p-10 md:p-12 text-center text-white relative overflow-hidden">
          <div className="relative z-10">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight">¿Listo para elegir con <span className="text-brand-mint">certeza</span>?</h2>
            <p className="text-blue-200/60 text-[14px] mt-3 max-w-md mx-auto">Obtén una recomendación personalizada basada en datos reales de mercado.</p>
            <div className="mt-6">
              <Button
                onClick={() => { setModalType('recommendation'); setSelectedCourseForInfo(null); setIsModalOpen(true); }}
                className="bg-white hover:bg-slate-50 text-brand-blue font-semibold rounded-lg px-8 h-11 text-[13px] border-0 shadow-lg shadow-black/10 transition-all active:scale-[0.98]"
              >
                Solicitar asesoría
              </Button>
            </div>
          </div>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-white/8 via-transparent to-transparent" />
        </div>
      </section>

      {/* ── Modal ──────────────────────────────────────── */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-md rounded-xl shadow-elevated relative overflow-hidden border border-slate-100 animate-in zoom-in-95 duration-200">
            <button onClick={() => setIsModalOpen(false)} className="absolute top-3 right-3 p-1.5 hover:bg-slate-50 rounded-md transition-all z-20">
              <X className="h-4 w-4 text-slate-400" />
            </button>

            <div className="p-8">
              <p className="text-[12px] font-medium text-brand-blue mb-2">
                {modalType === 'info' ? 'Consulta directa' : 'Asesoría personalizada'}
              </p>
              <h3 className="text-xl font-bold mb-6 text-brand-slate tracking-tight leading-tight">
                {modalType === 'info' ? selectedCourseForInfo?.name : 'Obtén tu ruta educativa.'}
              </h3>

              {isSuccess ? (
                <div className="py-10 text-center animate-in zoom-in duration-300">
                  <div className="h-14 w-14 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle2 className="h-7 w-7 text-emerald-500" />
                  </div>
                  <h3 className="text-[15px] font-semibold text-brand-slate">Enviado con éxito</h3>
                  <p className="text-[13px] text-slate-400 mt-1">Un asesor te contactará pronto.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmitLead} className="space-y-3.5">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[12px] font-medium text-slate-400 mb-1 block">Nombre</label>
                      <Input required className="h-10 rounded-lg bg-slate-50 border-0 px-3 text-[13px]" value={formData.first_name} onChange={(e) => setFormData({ ...formData, first_name: e.target.value })} />
                    </div>
                    <div>
                      <label className="text-[12px] font-medium text-slate-400 mb-1 block">WhatsApp</label>
                      <Input required className="h-10 rounded-lg bg-slate-50 border-0 px-3 text-[13px]" value={formData.whatsapp} onChange={(e) => setFormData({ ...formData, whatsapp: e.target.value })} />
                    </div>
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-slate-400 mb-1 block">Email</label>
                    <Input required type="email" className="h-10 rounded-lg bg-slate-50 border-0 px-3 text-[13px]" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
                  </div>
                  {modalType === 'recommendation' && (
                    <div>
                      <label className="text-[12px] font-medium text-slate-400 mb-1 block">Tus objetivos</label>
                      <textarea className="w-full h-20 rounded-lg bg-slate-50 border-0 p-3 text-[13px] focus:ring-1 focus:ring-brand-blue/30 resize-none" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                    </div>
                  )}
                  <Button disabled={isSubmitting} type="submit" className="w-full h-10 bg-brand-slate hover:bg-black text-white font-medium rounded-lg border-0 text-[13px] mt-2 transition-all active:scale-[0.98]">
                    {isSubmitting ? "Enviando…" : "Confirmar solicitud"}
                  </Button>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
