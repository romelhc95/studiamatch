"use client";

import { useEffect, useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, TrendingUp, ChevronDown, X, GraduationCap, CheckCircle2 } from "lucide-react";
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
  const [showFilters, setShowFilters] = useState(false);

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

  // Accordion state
  const [expandedFilter, setExpandedFilter] = useState<string | null>("area");

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
          fetch(`${SUPABASE_URL}/rest/v1/courses?is_active=eq.true&is_verified=eq.true&select=*,categories(name)&order=created_at.desc`, { headers }),
          fetch(`${SUPABASE_URL}/rest/v1/institutions?select=*`, { headers })
        ]);
        const [cData, iData] = await Promise.all([cRes.json(), iRes.json()]);

        if (Array.isArray(cData) && Array.isArray(iData)) {
          const enriched = cData.map((course: any) => ({
            ...course,
            institution_name: iData.find((i: Institution) => i.id === course.institution_id)?.name || "StudIAMatch",
            category: course.categories?.name || course.category
          }));
          setAllCourses(enriched);
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
    <div className="min-h-screen bg-white text-brand-slate font-sans selection:bg-brand-mint/30">
      {/* Hero Section - High-End Analytical Aesthetic */}
      <section className="relative mx-auto max-w-7xl px-8 pt-16 pb-12 overflow-hidden">
        {/* Background Decorative Mesh Filter */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full -z-10 opacity-40">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-brand-blue/20 rounded-full blur-[120px]" />
          <div className="absolute bottom-[10%] right-[-5%] w-[30%] h-[30%] bg-brand-mint/15 rounded-full blur-[100px]" />
        </div>

        <div className="relative overflow-hidden rounded-[2.5rem] bg-[#0A0F1C] p-16 text-white shadow-2xl border border-white/5">
          {/* Animated Matrix-like Grid */}
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none" 
               style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '40px 40px' }} />
          
          <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-16">
            <div className="max-w-3xl space-y-8 text-center lg:text-left">
              <div className="inline-flex items-center gap-2.5 rounded-full bg-white/5 px-5 py-2 border border-white/10 backdrop-blur-md">
                <div className="h-2 w-2 rounded-full bg-brand-mint shadow-[0_0_10px_#4ade80]" />
                <span className="text-[11px] font-black uppercase tracking-[0.3em] text-white/80">StudIAMatch · The Intelligence Layer</span>
              </div>
              
              <h1 className="text-5xl font-black leading-[1.05] md:text-7xl tracking-tighter">
                Auditoría <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-blue via-brand-mint to-brand-blue bg-[length:200%_auto] animate-gradient-x">imparcial</span> para tu carrera.
              </h1>
              
              <p className="text-lg md:text-xl text-slate-400 font-medium max-w-xl leading-relaxed">
                No elijas por promesas, elige por <span className="text-white">retorno financiero</span>. La primera base de datos auditada de educación tech en el Perú.
              </p>

              <div id="hero-search" className="flex flex-col sm:flex-row gap-4 pt-4 scroll-mt-32 max-w-2xl">
                <div className="relative flex-1 group">
                  <Search className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500 group-focus-within:text-brand-blue transition-colors" />
                  <Input
                    placeholder="¿En qué área quieres especializarte?"
                    className="pl-14 h-16 bg-white/5 border-white/10 text-white rounded-2xl text-sm font-bold placeholder:text-slate-600 focus:bg-white/10 focus:ring-2 focus:ring-brand-blue/50 transition-all shadow-2xl"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <Button
                  onClick={() => document.getElementById('programas')?.scrollIntoView({ behavior: 'smooth' })}
                  className="bg-brand-blue hover:bg-brand-blue/90 text-white font-black rounded-2xl px-12 h-16 text-[12px] tracking-widest uppercase shadow-2xl shadow-brand-blue/40 transition-all hover:scale-[1.02] active:scale-95"
                >
                  Analizar
                </Button>
              </div>
            </div>

            <div className="hidden lg:flex flex-col items-center justify-center p-8 rounded-[2rem] bg-white/5 border border-white/10 backdrop-blur-sm shadow-2xl">
              <div className="text-center space-y-1">
                <p className="text-5xl font-black text-brand-mint">+{allCourses.length || 0}</p>
                <p className="text-[9px] font-black uppercase tracking-[0.3em] text-white/50">Cursos Auditados</p>
              </div>
            </div>
          </div>
          {/* Subtle Decorative Gradient */}
          <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-brand-blue/20 rounded-full blur-[100px]" />
          <div className="absolute -top-24 -right-24 w-64 h-64 bg-brand-mint/10 rounded-full blur-[100px]" />
        </div>
      </section>

      {/* Unified Catalog Experience */}
      <div id="programas" className="mx-auto max-w-7xl px-6 py-10 relative scroll-mt-20">
        <div className="flex flex-col gap-12">

          {/* Controls Bar */}
          <div className="flex items-center justify-between gap-4 mb-4">
            <Button
              onClick={() => setShowFilters(!showFilters)}
              variant="outline"
              className={cn(
                "rounded-full px-8 h-14 font-black uppercase text-xs tracking-widest border-2 transition-all",
                showFilters ? "bg-brand-blue text-white border-brand-blue" : "border-brand-blue text-brand-blue hover:bg-brand-blue/5"
              )}
            >
              <ChevronDown className={cn("mr-2 h-4 w-4 transition-transform", showFilters && "rotate-180")} />
              {showFilters ? "Cerrar Filtros" : "Mostrar Filtros"}
              {Object.values(activeFilters).filter(v => v !== "" && v !== "Todas" && (Array.isArray(v) ? v.length > 0 : true) && v !== true).length > 0 && (
                <Badge className="ml-2 bg-brand-mint text-brand-slate border-0">
                  {Object.values(activeFilters).filter(v => v !== "" && v !== "Todas" && (Array.isArray(v) ? v.length > 0 : true) && v !== true).length}
                </Badge>
              )}
            </Button>


          </div>

          <div className="flex flex-col lg:flex-row gap-12 relative items-start">
            {/* Sidebar Filters - Compacted */}
            <aside className={cn(
              "space-y-4 shrink-0 transition-all duration-500 overflow-hidden lg:static",
              showFilters ? "w-full lg:w-72 opacity-100 max-h-[2000px]" : "w-0 opacity-0 max-h-0 pointer-events-none"
            )}>
              <div className="space-y-2">
                {[
                  { id: 'area', label: 'Área / Tema', icon: TrendingUp, options: activeCategories, current: selectedCategory, setter: setSelectedCategory, statsKey: 'categories' },
                  { id: 'tipo', label: 'Tipo de Programa', icon: GraduationCap, options: activeTypes, current: selectedType, setter: setSelectedType, statsKey: 'types' },
                  { id: 'inst', label: 'Institución', icon: Search, options: activeInstitutions, current: activeFilters.selectedInstitution, setter: (val: string) => setActiveFilters({ ...activeFilters, selectedInstitution: val }), statsKey: 'institutions' },
                ].map((group) => (
                  <div key={group.id} className="border border-brand-gray/50 rounded-2xl overflow-hidden bg-white shadow-sm">
                    <button
                      onClick={() => setExpandedFilter(expandedFilter === group.id ? null : group.id)}
                      className="w-full flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition-colors"
                    >
                      <span className="text-[10px] font-black uppercase tracking-[0.15em] text-slate-400 flex items-center gap-2">
                        <group.icon className="h-3 w-3 text-brand-blue" /> {group.label}
                      </span>
                      <ChevronDown className={cn("h-3 w-3 text-slate-300 transition-transform", expandedFilter === group.id && "rotate-180")} />
                    </button>
                    <div className={cn("px-3 pb-4 space-y-1 max-h-52 overflow-y-auto custom-scrollbar", expandedFilter !== group.id && "hidden")}>
                      {group.options.map(opt => (
                        <button
                          key={opt}
                          onClick={() => group.setter(opt)}
                          className={cn(
                            "w-full text-left px-4 py-2.5 rounded-xl text-[11px] font-bold transition-all flex items-center justify-between group",
                            group.current === opt ? "bg-brand-blue text-white shadow-sm" : "hover:bg-brand-blue/5 text-slate-600"
                          )}
                        >
                          <span className="truncate">{opt}</span>
                          {opt !== "Todos" && opt !== "Todas" && (
                            <span className={cn(
                              "text-[8px] px-1.5 py-0.5 rounded-md",
                              group.current === opt ? "bg-white/20 text-white" : "bg-slate-100 text-slate-400"
                            )}>
                              {(stats as any)[group.statsKey][opt]}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Investment Range - Compact */}
                <div className="border border-brand-gray/50 rounded-2xl overflow-hidden bg-white shadow-sm">
                  <button
                    onClick={() => setExpandedFilter(expandedFilter === 'price' ? null : 'price')}
                    className="w-full flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition-colors"
                  >
                    <span className="text-[10px] font-black uppercase tracking-[0.15em] text-slate-400">Rango de Inversión</span>
                    <ChevronDown className={cn("h-3 w-3 text-slate-300 transition-transform", expandedFilter === 'price' && "rotate-180")} />
                  </button>
                  <div className={cn("px-5 pb-5 pt-1 space-y-3", expandedFilter !== 'price' && "hidden")}>
                    <div className="flex items-center gap-2">
                      <Input placeholder="Mín" type="number" className="h-10 rounded-xl bg-slate-50 border-0 font-bold text-[11px] px-4" value={activeFilters.priceMin} onChange={(e) => setActiveFilters({ ...activeFilters, priceMin: e.target.value })} />
                      <div className="h-[1px] w-2 bg-slate-200" />
                      <Input placeholder="Máx" type="number" className="h-10 rounded-xl bg-slate-50 border-0 font-bold text-[11px] px-4" value={activeFilters.priceMax} onChange={(e) => setActiveFilters({ ...activeFilters, priceMax: e.target.value })} />
                    </div>
                  </div>
                </div>
              </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 space-y-10 min-w-0">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-brand-gray/40 pb-10">
                <div className="space-y-2">
                  <h2 className="text-4xl font-black tracking-tight uppercase">Programas <span className="text-brand-blue">Comparables</span></h2>
                  <p className="text-slate-500 font-bold text-sm">Mostrando {filteredCourses.length} resultados de alta relevancia.</p>
                </div>
              </div>

              {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
                  {[1, 2, 3, 4, 5, 6].map(i => <div key={i} className="h-[400px] bg-slate-50 rounded-[2.5rem]" />)}
                </div>
              ) : filteredCourses.length > 0 ? (
                <div className={cn(
                  "grid grid-cols-1 md:grid-cols-2 gap-6 transition-all duration-500",
                  showFilters ? "lg:grid-cols-2" : "lg:grid-cols-3"
                )}>
                  {paginatedCourses.map((course) => (
                    <article key={course.id} className="group relative flex flex-col justify-between rounded-[2.5rem] border border-brand-gray/50 bg-white p-8 shadow-premium transition-all duration-500 hover:-translate-y-2 hover:shadow-2xl hover:border-brand-blue/30 overflow-hidden">
                      <div className="space-y-6">
                        <div className="flex flex-col gap-4">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100">
                              {course.institution_name}
                            </span>
                            <div className="h-2 w-2 rounded-full bg-brand-mint/40" />
                          </div>
                          <Link href={`/courses/${cleanSlug(course.slug)}`} className="group/title">
                            <h3 className="text-xl font-black text-brand-slate leading-tight uppercase tracking-tight group-hover/title:text-brand-blue transition-colors">
                              {course.name}
                            </h3>
                          </Link>
                          <div className="flex gap-2 flex-wrap">
                            {course.category && (
                              <span className="text-[8px] font-bold uppercase tracking-wider text-slate-400">
                                {course.category}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 py-4 border-y border-brand-gray/30">
                          <div className="space-y-1">
                            <p className="text-[9px] font-bold text-slate-400 uppercase">Inversión</p>
                            <p className="text-sm font-black text-brand-slate">
                              {course.price_status === 'consultar' ? "Consultar" : (course.price_pen ? `S/ ${course.price_pen.toLocaleString()}` : "Consultar")}
                            </p>
                          </div>
                          <div className="space-y-1">
                            <p className="text-[9px] font-bold text-slate-400 uppercase">Modalidad</p>
                            <p className="text-sm font-black text-brand-slate capitalize">{course.mode}</p>
                          </div>
                        </div>
                      </div>

                      <div className="mt-6 space-y-2">
                        <div className="flex gap-2">
                          <Link href={`/courses/${cleanSlug(course.slug)}`} className="flex-1 rounded-xl bg-slate-50 hover:bg-slate-100 flex items-center justify-center text-[10px] font-black uppercase tracking-widest text-slate-600 transition-all h-10">
                            Detalle
                          </Link>
                          <Button
                            variant="outline"
                            onClick={() => {
                              setCompareList(prev => {
                                if (prev.find(c => c.id === course.id)) return prev.filter(c => c.id !== course.id);
                                if (prev.length >= 3) return prev;
                                return [...prev, course];
                              });
                            }}
                            className={cn(
                              "h-10 px-4 rounded-xl border-2 text-[10px] font-black uppercase tracking-widest transition-all",
                              compareList.find(c => c.id === course.id)
                                ? "bg-brand-blue border-brand-blue text-white"
                                : "border-slate-100 text-slate-400 hover:border-brand-blue hover:text-brand-blue"
                            )}
                          >
                            {compareList.find(c => c.id === course.id) ? "✓" : "+ Comparar"}
                          </Button>
                        </div>
                        <Button
                          onClick={() => openModal('info', course)}
                          className="w-full rounded-xl bg-brand-blue hover:bg-brand-blue/90 text-white font-black h-11 text-[10px] tracking-widest uppercase shadow-lg shadow-brand-blue/10 border-0"
                        >
                          Solicitar Información
                        </Button>
                      </div>
                    </article>
                  ))}

                  {totalPages > 1 && (
                    <div className="flex justify-center items-center gap-6 mt-10 col-span-full py-8 border-t border-brand-gray/30">
                      <Button
                        variant="outline"
                        disabled={currentPage === 1}
                        onClick={() => {
                          setCurrentPage(prev => Math.max(1, prev - 1));
                          document.getElementById('catalogo')?.scrollIntoView({ behavior: 'smooth' });
                        }}
                        className="rounded-2xl border-2 font-black py-5 uppercase tracking-widest h-auto"
                      >
                        Anterior
                      </Button>
                      <span className="font-bold text-slate-400 text-sm tracking-widest uppercase">Página {currentPage} de {totalPages}</span>
                      <Button
                        variant="outline"
                        disabled={currentPage === totalPages}
                        onClick={() => {
                          setCurrentPage(prev => Math.min(totalPages, prev + 1));
                          document.getElementById('catalogo')?.scrollIntoView({ behavior: 'smooth' });
                        }}
                        className="rounded-2xl border-2 border-brand-blue text-brand-blue font-black py-5 uppercase tracking-widest h-auto hover:bg-brand-blue hover:text-white"
                      >
                        Siguiente
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-32 text-center rounded-[3rem] border-4 border-dashed border-slate-50">
                  <Search className="h-16 w-16 text-slate-200 mx-auto mb-6" />
                  <h3 className="text-2xl font-black text-slate-400">Sin Coincidencias</h3>
                  <p className="text-slate-400 mt-2 font-bold mb-10">Intenta relajar los filtros laterales.</p>
                  <Button variant="outline" onClick={() => { setSearchTerm(""); setSelectedCategory("Todos"); setActiveFilters({ priceMin: "", priceMax: "", modes: [], durations: [], selectedInstitution: "Todas", includeConsultar: true }); }} className="rounded-2xl px-10 h-14 font-black border-2 border-brand-blue text-brand-blue uppercase text-xs tracking-widest">Reiniciar</Button>
                </div>
              )}
            </main>
          </div>
        </div>
      </div>

      {/* Floating Comparison Bar */}
      {compareList.length > 0 && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[60] w-[95%] max-w-2xl animate-in slide-in-from-bottom-10 duration-700">
          <div className="bg-brand-slate/95 backdrop-blur-2xl rounded-full p-3 shadow-premium border border-white/10 flex items-center justify-between gap-6">
            <div className="flex items-center gap-6 pl-6">
              <div className="flex -space-x-3">
                {compareList.map(c => <div key={c.id} className="h-14 w-14 rounded-full border-4 border-brand-slate bg-brand-blue flex items-center justify-center text-white font-black text-xs shadow-2xl">{c.name.charAt(0)}</div>)}
              </div>
              <div className="hidden sm:block">
                <p className="text-white font-black uppercase tracking-widest text-xs">{compareList.length} Programas</p>
                <p className="text-white/40 text-[9px] font-bold uppercase tracking-[0.2em]">Comparativa Lista</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button onClick={() => setCompareList([])} className="text-white/30 hover:text-white text-[10px] font-black uppercase tracking-widest px-4 transition-colors">Limpiar</button>
              <Link href={`/compare?ids=${compareList.map(c => c.id).join(",")}`}>
                <Button className="bg-brand-mint hover:bg-brand-mint/90 text-brand-slate font-black rounded-full px-10 h-16 border-0 shadow-2xl shadow-brand-mint/30 uppercase tracking-widest text-xs">Comparar Ahora</Button>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Como Funciona Section - Minimalist */}
      <section id="como-funciona" className="py-20 bg-slate-50/50 scroll-mt-20">
        <div className="mx-auto max-w-7xl px-8">
          <div className="flex flex-col md:flex-row items-end justify-between mb-12 gap-6">
            <div className="space-y-3">
              <div className="text-[10px] font-black uppercase tracking-[0.3em] text-brand-blue">Metodología</div>
              <h2 className="text-3xl font-black tracking-tight uppercase">¿Cómo funciona <span className="text-slate-400">StudIAMatch</span>?</h2>
            </div>
            <p className="max-w-md text-sm text-slate-500 font-medium leading-relaxed">
              Tres pilares diseñados para garantizar la transparencia y el retorno de tu inversión educativa.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { step: '01', title: 'Curación', desc: 'Auditamos programas bajo una matriz de 14 pilares de calidad.', icon: Search },
              { step: '02', title: 'Análisis', desc: 'Calculamos el ROI real basado en salarios de mercado actuales.', icon: TrendingUp },
              { step: '03', title: 'Decisión', desc: 'Te entregamos una ruta imparcial sin sesgo institucional.', icon: CheckCircle2 },
            ].map((item) => (
              <div key={item.step} className="bg-white p-8 rounded-2xl border border-brand-gray/50 shadow-sm hover:shadow-md transition-shadow group">
                <div className="flex items-center justify-between mb-6">
                  <div className="text-2xl font-black text-brand-blue/10 group-hover:text-brand-blue/20 transition-colors uppercase italic tracking-tighter">{item.step}</div>
                  <item.icon className="h-5 w-5 text-brand-blue" />
                </div>
                <h3 className="text-lg font-black text-brand-slate uppercase mb-3">{item.title}</h3>
                <p className="text-[11px] text-slate-500 leading-relaxed font-bold uppercase tracking-wider">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Nosotros Section - Compact */}
      <section id="nosotros" className="py-24 scroll-mt-20 overflow-hidden">
        <div className="mx-auto max-w-7xl px-8">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            <div className="flex-1 space-y-8">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-brand-slate text-white text-[9px] font-black uppercase tracking-[0.2em]">Nuestra Misión</div>
              <h2 className="text-4xl font-extrabold tracking-tighter leading-[1.1] uppercase">
                Democratizar la <span className="text-brand-blue">inteligencia</span> educativa.
              </h2>
              <p className="text-sm text-slate-500 leading-relaxed font-medium">
                En un mercado saturado de promesas, nosotros aportamos claridad. Consolidamos datos reales de instituciones para que tomes decisiones basadas en mérito y retorno financiero real.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-5 rounded-xl bg-slate-50 border border-brand-gray/50">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Principio 01</p>
                  <p className="text-xs font-black text-brand-slate uppercase">Transparencia Total</p>
                </div>
                <div className="p-5 rounded-xl bg-slate-50 border border-brand-gray/50">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Principio 02</p>
                  <p className="text-xs font-black text-brand-slate uppercase">Datos Verificados</p>
                </div>
              </div>
            </div>
            <div className="flex-1 w-full max-w-lg">
              <div className="relative aspect-video rounded-2xl overflow-hidden bg-brand-slate flex items-center justify-center p-12 group shadow-2xl">
                <div className="text-center space-y-2">
                  <p className="text-6xl font-black text-brand-mint italic">+{allCourses.length}</p>
                  <p className="text-[10px] font-black uppercase tracking-[0.4em] text-white/40">Benchmarks</p>
                </div>
                <div className="absolute inset-0 bg-gradient-to-tr from-brand-blue/20 to-transparent pointer-events-none" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section - Minimalist */}
      <section className="mx-auto max-w-7xl px-8 py-16">
        <div className="rounded-[2.5rem] bg-brand-blue p-12 md:p-16 text-center text-white relative overflow-hidden shadow-2xl">
          <div className="relative z-10 space-y-6">
            <h2 className="text-3xl md:text-4xl font-black uppercase tracking-tight">¿Listo para elegir con <span className="text-brand-mint">certeza</span>?</h2>
            <p className="text-blue-100/70 text-sm font-bold uppercase tracking-widest max-w-xl mx-auto leading-relaxed">
              Obtén una recomendación personalizada basada en datos reales de mercado.
            </p>
            <div className="flex justify-center pt-4">
              <Button
                onClick={() => { setModalType('recommendation'); setSelectedCourseForInfo(null); setIsModalOpen(true); }}
                className="bg-white hover:bg-slate-100 text-brand-blue font-black rounded-xl px-12 h-14 shadow-xl border-0 text-[11px] tracking-[0.2em] uppercase transition-transform active:scale-95"
              >
                Solicitar Asesoría
              </Button>
            </div>
          </div>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-white/10 via-transparent to-transparent opacity-50" />
        </div>
      </section>

      {/* Simplified Modal - Redesigned */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-brand-slate/80 backdrop-blur-md animate-in fade-in duration-500">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl relative overflow-hidden border border-brand-gray/50 animate-in zoom-in-95 duration-300">
            <button onClick={() => setIsModalOpen(false)} className="absolute top-4 right-4 p-2 hover:bg-slate-50 rounded-full transition-all z-20">
              <X className="h-4 w-4 text-slate-300" />
            </button>

            <div className="p-10">
              <div className="text-[9px] font-black uppercase tracking-[0.25em] text-brand-blue mb-4">
                {modalType === 'info' ? 'Consulta Directa' : 'Ruta Inteligente'}
              </div>
              <h3 className="text-2xl font-black mb-10 text-brand-slate tracking-tight uppercase leading-tight">
                {modalType === 'info' ? selectedCourseForInfo?.name : 'Define tu futuro con certeza.'}
              </h3>

              {isSuccess ? (
                <div className="py-12 text-center animate-in zoom-in duration-500">
                  <div className="h-20 w-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircle2 className="h-10 w-10 text-emerald-500" />
                  </div>
                  <h3 className="text-sm font-black text-brand-slate uppercase tracking-widest">Enviado con éxito</h3>
                  <p className="text-[11px] text-slate-400 mt-2 font-bold uppercase tracking-wider">Un auditor te contactará.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmitLead} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[9px] font-black uppercase tracking-widest text-slate-400 ml-1">Nombre</label>
                      <Input required className="h-11 rounded-xl bg-slate-50 border-0 px-4 font-bold text-xs shadow-inner" value={formData.first_name} onChange={(e) => setFormData({ ...formData, first_name: e.target.value })} />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[9px] font-black uppercase tracking-widest text-slate-400 ml-1">WhatsApp</label>
                      <Input required className="h-11 rounded-xl bg-slate-50 border-0 px-4 font-bold text-xs shadow-inner" value={formData.whatsapp} onChange={(e) => setFormData({ ...formData, whatsapp: e.target.value })} />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[9px] font-black uppercase tracking-widest text-slate-400 ml-1">Email Empresarial/Personal</label>
                    <Input required type="email" className="h-11 rounded-xl bg-slate-50 border-0 px-4 font-bold text-xs shadow-inner" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
                  </div>
                  {modalType === 'recommendation' && (
                    <div className="space-y-1.5">
                      <label className="text-[9px] font-black uppercase tracking-widest text-slate-400 ml-1">Cuéntanos tus objetivos</label>
                      <textarea className="w-full h-24 rounded-xl bg-slate-50 border-0 p-4 font-bold text-xs focus:ring-4 focus:ring-brand-blue/5 resize-none shadow-inner" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                    </div>
                  )}
                  <Button disabled={isSubmitting} type="submit" className="w-full h-12 bg-brand-slate hover:bg-black text-white font-black rounded-xl border-0 shadow-lg text-[10px] tracking-[0.2em] uppercase mt-4 transition-all active:scale-[0.98]">
                    {isSubmitting ? "Tramitando..." : "Confirmar solicitud"}
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
