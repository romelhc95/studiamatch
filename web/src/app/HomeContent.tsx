"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, TrendingUp, ChevronDown, X, GraduationCap, CheckCircle2, ArrowRight, Building2, Globe, LayoutGrid, ArrowUpDown, ArrowDownWideNarrow, ArrowUpNarrowWide, RotateCcw, Sparkles, Zap, Clock, Verified, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { SUPABASE_URL, SUPABASE_ANON_KEY, COURSE_PUBLIC_FIELDS, cleanSlug, parseDurationToMonths, type Course, type Institution } from "@/lib/supabase";

export default function HomeContent({ initialCourses = [] }: { initialCourses: Course[] }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [allCourses, setAllCourses] = useState<Course[]>(initialCourses);
  const [searchTerm, setSearchTerm] = useState(searchParams.get('q') || "");
  const [loading, setLoading] = useState(initialCourses.length === 0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCourseForInfo, setSelectedCourseForInfo] = useState<Course | null>(null);
  const [modalType, setModalType] = useState<'recommendation' | 'info'>('recommendation');
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  const [activeFilters, setActiveFilters] = useState({
    priceMin: searchParams.get('min') || "",
    priceMax: searchParams.get('max') || "",
    modes: searchParams.get('modalidad') ? searchParams.get('modalidad')!.split(',') : [] as string[],
    durations: [] as string[],
    selectedInstitution: searchParams.get('inst') || "Todas",
    includeConsultar: true
  });

  const [selectedCategory, setSelectedCategory] = useState<string>(searchParams.get('area') || "Todos");
  const [selectedType, setSelectedType] = useState<string>(searchParams.get('tipo') || "Todos");
  const [sortOrder, setSortOrder] = useState<string | null>(searchParams.get('sort') || null);
  const [careerGoal, setCareerGoal] = useState<string | null>(null);
  const [durationFilter, setDurationFilter] = useState<string | null>(searchParams.get('duration') || null);
  const [priceRange, setPriceRange] = useState<string | null>(searchParams.get('priceRange') || null);
  const [selectedRegion, setSelectedRegion] = useState<string>(searchParams.get('region') || "Todas");
  const [showGoals, setShowGoals] = useState(false);
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const careerGoals = [
    { id: 'tech', label: 'Cambiar a Tech', icon: Zap, desc: 'Cursos Junior para empezar en tecnología' },
    { id: 'update', label: 'Actualizarme', icon: Sparkles, desc: 'Cursos cortos y flexibles' },
    { id: 'postgrad', label: 'Posgrado', icon: GraduationCap, desc: 'Maestrías y especializaciones' },
    { id: 'fast-job', label: 'Trabajo rápido', icon: TrendingUp, desc: 'Alto ROI con certificación' },
  ];

  // Sync state to URL
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchTerm) params.set('q', searchTerm);
    if (selectedCategory !== "Todos") params.set('area', selectedCategory);
    if (selectedType !== "Todos") params.set('tipo', selectedType);
    if (activeFilters.selectedInstitution !== "Todas") params.set('inst', activeFilters.selectedInstitution);
    if (activeFilters.modes.length > 0) params.set('modalidad', activeFilters.modes.join(','));
    if (activeFilters.priceMax) params.set('max', activeFilters.priceMax);
    if (sortOrder) params.set('sort', sortOrder);
    if (durationFilter) params.set('duration', durationFilter);
    if (priceRange) params.set('priceRange', priceRange);
    if (selectedRegion !== "Todas") params.set('region', selectedRegion);

    const queryString = params.toString();
    const url = queryString ? `${pathname}?${queryString}` : pathname;
    router.replace(url, { scroll: false });
  }, [searchTerm, selectedCategory, selectedType, activeFilters, sortOrder, pathname, router, durationFilter, priceRange, selectedRegion]);

  // Cascading Filters Logic
  const getFilteredExcluding = (excludeKey: string) => {
    let result = [...allCourses];
    
    if (searchTerm && excludeKey !== 'search') {
      const norm = (t: string) => t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
      const s = norm(searchTerm);
      result = result.filter(c => norm(c.name || "").includes(s) || norm(c.institution_name || "").includes(s));
    }

    if (careerGoal && excludeKey !== 'goal') {
    if (selectedRegion !== "Todas") result = result.filter(c => c.region === selectedRegion);
    if (durationFilter) {
      result = result.filter(c => {
        const months = parseDurationToMonths(c.duration || '');
        if (durationFilter === 'short') return months > 0 && months < 3;
        if (durationFilter === 'medium') return months >= 3 && months <= 6;
        if (durationFilter === 'long') return months > 6;
        return true;
      });
    }
    if (priceRange) {
      result = result.filter(c => {
        const price = c.price_pen;
        if (!price || price <= 0) return c.price_status === 'consultar';
        if (priceRange === 'accessible') return price <= 1500;
        if (priceRange === 'standard') return price > 1500 && price <= 5000;
        if (priceRange === 'premium') return price > 5000 && price <= 15000;
        if (priceRange === 'executive') return price > 15000;
        return true;
      });
    }
    if (careerGoal === 'tech') {
        result = result.filter(c => c.seniority_level === 'Junior' || !c.seniority_level);
      } else if (careerGoal === 'update') {
        result = result.filter(c => {
          const months = c.duration ? parseInt(c.duration.match(/\d+/)?.[0] || '12') : 12;
          return months <= 6 && (c.mode === 'Remoto' || c.mode === 'Híbrido');
        });
      } else if (careerGoal === 'postgrad') {
        result = result.filter(c => c.course_type === 'Maestría' || c.course_type === 'Doctorado' || c.course_type === 'Especialización');
      } else if (careerGoal === 'fast-job') {
        result = result.filter(c => (c.roi_months ?? 999) <= 6 && !!c.certification);
      }
    }
    
    if (selectedCategory !== "Todos" && excludeKey !== 'area') {
      result = result.filter(c => c.category === selectedCategory);
    }
    
    if (selectedType !== "Todos" && excludeKey !== 'tipo') {
      result = result.filter(c => c.course_type === selectedType);
    }
    
    if (activeFilters.selectedInstitution !== "Todas" && excludeKey !== 'inst') {
      result = result.filter(c => c.institution_name?.toLowerCase().trim() === activeFilters.selectedInstitution.toLowerCase().trim());
    }
    
    if (activeFilters.modes.length > 0 && excludeKey !== 'modalidad') {
      result = result.filter(c => activeFilters.modes.includes(c.mode));
    }
    
    if ((activeFilters.priceMin || activeFilters.priceMax) && excludeKey !== 'precio') {
      result = result.filter(c => {
        const price = c.price_pen;
        const isConsultar = c.price_status === 'consultar' || !price || price <= 0;
        if (isConsultar) return false;
        if (activeFilters.priceMin && price < parseFloat(activeFilters.priceMin)) return false;
        if (activeFilters.priceMax && price > parseFloat(activeFilters.priceMax)) return false;
        return true;
      });
    }

    if (durationFilter && excludeKey !== 'duration') {
      result = result.filter(c => {
        const months = parseDurationToMonths(c.duration || '');
        if (durationFilter === 'short') return months > 0 && months < 3;
        if (durationFilter === 'medium') return months >= 3 && months <= 6;
        if (durationFilter === 'long') return months > 6;
        return true;
      });
    }

    if (priceRange && excludeKey !== 'priceRange') {
      result = result.filter(c => {
        const price = c.price_pen;
        if (!price || price <= 0) return false;
        if (priceRange === 'accessible') return price <= 1500;
        if (priceRange === 'standard') return price > 1500 && price <= 5000;
        if (priceRange === 'premium') return price > 5000 && price <= 15000;
        if (priceRange === 'executive') return price > 15000;
        return true;
      });
    }

    if (selectedRegion !== "Todas" && excludeKey !== 'region') {
      result = result.filter(c => c.region === selectedRegion);
    }
    
    return result;
  };

  const activeCategories = useMemo(() => {
    const courses = getFilteredExcluding('area');
    const categories = Array.from(new Set(courses.map(c => c.category).filter(Boolean))).sort() as string[];
    return ["Todos", ...categories];
  }, [allCourses, searchTerm, selectedType, activeFilters, careerGoal, durationFilter, priceRange, selectedRegion]);

  const activeTypes = useMemo(() => {
    const courses = getFilteredExcluding('tipo');
    const types = Array.from(new Set(courses.map(c => c.course_type).filter(Boolean))).sort() as string[];
    return ["Todos", ...types];
  }, [allCourses, searchTerm, selectedCategory, activeFilters, careerGoal, durationFilter, priceRange, selectedRegion]);

  const activeInstitutions = useMemo(() => {
    const courses = getFilteredExcluding('inst');
    const institutions = Array.from(new Set(courses.map(c => c.institution_name).filter(Boolean))).sort() as string[];
    return ["Todas", ...institutions];
  }, [allCourses, searchTerm, selectedCategory, selectedType, activeFilters.modes, activeFilters.priceMax, careerGoal, durationFilter, priceRange, selectedRegion]);

  const activeModes = useMemo(() => {
    const courses = getFilteredExcluding('modalidad');
    const modes = Array.from(new Set(courses.map(c => c.mode).filter(Boolean))).sort() as string[];
    return ["Todas", ...modes];
  }, [allCourses, searchTerm, selectedCategory, selectedType, activeFilters.selectedInstitution, activeFilters.priceMax, careerGoal, durationFilter, priceRange, selectedRegion]);

  const activeRegions = useMemo(() => {
    const courses = getFilteredExcluding('region');
    const regions = Array.from(new Set(courses.map(c => c.region).filter(Boolean))).sort() as string[];
    return ["Todas", ...regions];
  }, [allCourses, searchTerm, selectedCategory, selectedType, activeFilters, careerGoal, durationFilter, priceRange, selectedRegion]);

  const contextualStats = useMemo(() => {
    const counts = { categories: {} as Record<string, number>, types: {} as Record<string, number>, institutions: {} as Record<string, number> };
    const areaCourses = getFilteredExcluding('area');
    areaCourses.forEach(c => { if (c.category) counts.categories[c.category] = (counts.categories[c.category] || 0) + 1; });
    const typeCourses = getFilteredExcluding('tipo');
    typeCourses.forEach(c => { if (c.course_type) counts.types[c.course_type] = (counts.types[c.course_type] || 0) + 1; });
    const instCourses = getFilteredExcluding('inst');
    instCourses.forEach(c => { if (c.institution_name) counts.institutions[c.institution_name] = (counts.institutions[c.institution_name] || 0) + 1; });
    return counts;
  }, [allCourses, searchTerm, selectedCategory, selectedType, activeFilters, careerGoal, durationFilter, priceRange, selectedRegion]);

  const stats = useMemo(() => {
    const counts = { categories: {} as Record<string, number>, types: {} as Record<string, number>, institutions: {} as Record<string, number> };
    allCourses.forEach(c => {
      if (c.category) counts.categories[c.category] = (counts.categories[c.category] || 0) + 1;
      if (c.course_type) counts.types[c.course_type] = (counts.types[c.course_type] || 0) + 1;
      if (c.institution_name) counts.institutions[c.institution_name] = (counts.institutions[c.institution_name] || 0) + 1;
    });
    return counts;
  }, [allCourses]);

  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 12;
  const [compareList, setCompareList] = useState<Course[]>([]);
  const [isCompareInitialized, setIsCompareInitialized] = useState(false);

  useEffect(() => {
    const savedCompare = localStorage.getItem('StudIAMatch_compare_list');
    if (savedCompare) {
      try {
        const parsed = JSON.parse(savedCompare);
        // eslint-disable-next-line react-hooks/set-state-in-effect
        if (Array.isArray(parsed)) setCompareList(parsed);
      } catch (e) {
        console.error("Error parsing saved comparison list", e);
      }
    }
    setIsCompareInitialized(true);
  }, []);

  useEffect(() => {
    if (isCompareInitialized) {
      localStorage.setItem('StudIAMatch_compare_list', JSON.stringify(compareList));
    }
  }, [compareList, isCompareInitialized]);

  const [formData, setFormData] = useState({ first_name: "", last_name: "", email: "", whatsapp: "", area_interest: "", budget: "", modality: "Remoto", description: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const headers = { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` };
      const [cRes, iRes] = await Promise.all([
        fetch(`${SUPABASE_URL}/rest/v1/courses?is_active=eq.true&is_verified=eq.true&is_mock_data=neq.true&select=${COURSE_PUBLIC_FIELDS},categories(name),institutions(name,slug)&order=created_at.desc`, { headers }),
        fetch(`${SUPABASE_URL}/rest/v1/institutions?select=id,name,slug`, { headers })
      ]);
      const [cData, iData] = await Promise.all([cRes.json(), iRes.json()]);

      if (Array.isArray(cData) && Array.isArray(iData)) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const enriched = cData.map((course: any) => ({
          ...course,
          institution_name: course.institutions?.name || iData.find((i: Institution) => i.id === course.institution_id)?.name || "StudIAMatch",
          institution_slug: course.institutions?.slug || iData.find((i: Institution) => i.id === course.institution_id)?.slug || "general",
          category: course.categories?.name || course.category
        }));

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const uniqueMap = new Map<string, any>();
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        enriched.forEach((course: any) => {
          const institutionSlug = course.institutions?.slug || "general";
          const key = `${institutionSlug}-${course.slug}`;
          const existing = uniqueMap.get(key);
          if (!existing || (!existing.price_pen && course.price_pen) || (course.name.length > existing.name.length)) {
            uniqueMap.set(key, course);
          }
        });

        const deduped = Array.from(uniqueMap.values());
        setAllCourses(deduped);
        setLastUpdated(new Date());

        try {
          localStorage.setItem('StudIAMatch_courses_cache', JSON.stringify({ data: deduped, timestamp: Date.now() }));
        } catch (_e) {}
      }
    } catch (error) {
      console.error("Error cargando datos:", error);
    }
  }, []);

  // Initial fetch + polling every 5 minutes
  useEffect(() => {
    const CACHE_TTL = 5 * 60 * 1000;

    // Try cache first
    try {
      const cached = localStorage.getItem('StudIAMatch_courses_cache');
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_TTL && Array.isArray(data) && data.length > 0) {
          // eslint-disable-next-line react-hooks/set-state-in-effect
          setAllCourses(data);
          setLoading(false);
          setLastUpdated(new Date(timestamp));
          return;
        }
      }
    } catch (_e) {}

    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  // Polling: re-fetch every 5 minutos
  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleSubmitLead = async (e: React.FormEvent) => {
    e.preventDefault();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) { alert("Por favor, ingresa un email válido."); return; }
    if (formData.whatsapp.replace(/\D/g, '').length < 9) { alert("Por favor, ingresa un WhatsApp válido (mín. 9 dígitos)."); return; }
    if (!formData.first_name.trim()) { alert("Por favor, ingresa tu nombre."); return; }
    setIsSubmitting(true);
    try {
      const leadData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        whatsapp: formData.whatsapp,
        source_page: 'home',
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

  const filteredCourses = useMemo(() => {
    let result = [...allCourses];

    if (searchTerm) {
      const norm = (t: string) => t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
      const s = norm(searchTerm);
      result = result.filter(c => norm(c.name || "").includes(s) || norm(c.institution_name || "").includes(s));
    }
    if (careerGoal === 'tech') {
      result = result.filter(c => c.seniority_level === 'Junior' || !c.seniority_level);
    } else if (careerGoal === 'update') {
      result = result.filter(c => {
        const months = c.duration ? parseInt(c.duration.match(/\d+/)?.[0] || '12') : 12;
        return months <= 6 && (c.mode === 'Remoto' || c.mode === 'Híbrido');
      });
    } else if (careerGoal === 'postgrad') {
      result = result.filter(c => c.course_type === 'Maestría' || c.course_type === 'Doctorado' || c.course_type === 'Especialización');
    } else if (careerGoal === 'fast-job') {
      result = result.filter(c => (c.roi_months ?? 999) <= 6 && !!c.certification);
    }
    if (selectedCategory !== "Todos") result = result.filter(c => c.category === selectedCategory);
    if (selectedType !== "Todos") result = result.filter(c => c.course_type === selectedType);

    if (activeFilters.selectedInstitution !== "Todas") {
      result = result.filter(c =>
        c.institution_name?.toLowerCase().trim() === activeFilters.selectedInstitution.toLowerCase().trim()
      );
    }

    const filtered = result.filter(c => {
      if (activeFilters.modes.length > 0 && !activeFilters.modes.includes(c.mode)) return false;
      const price = c.price_pen;
      const isConsultar = c.price_status === 'consultar' || !price || price <= 0;

      if (isConsultar) {
        if (activeFilters.priceMin || activeFilters.priceMax) return false;
      } else {
        if (activeFilters.priceMin && price < parseFloat(activeFilters.priceMin)) return false;
        if (activeFilters.priceMax && price > parseFloat(activeFilters.priceMax)) return false;
      }
      return true;
    });

    if (sortOrder) {
      if (sortOrder === 'popular') {
        filtered.sort((a, b) => (b.view_count || 0) - (a.view_count || 0));
      } else if (sortOrder === 'price') {
        filtered.sort((a, b) => {
          const hasPriceA = a.price_pen !== null && a.price_pen !== undefined && a.price_pen > 0;
          const hasPriceB = b.price_pen !== null && b.price_pen !== undefined && b.price_pen > 0;
          if (hasPriceA && !hasPriceB) return -1;
          if (!hasPriceA && hasPriceB) return 1;
          if (!hasPriceA && !hasPriceB) return 0;
          return a.price_pen! - b.price_pen!;
        });
      } else if (sortOrder === 'roi') {
        filtered.sort((a, b) => {
          const roiA = a.roi_months ?? 999;
          const roiB = b.roi_months ?? 999;
          return roiA - roiB;
        });
      } else if (sortOrder === 'recent') {
        filtered.sort((a, b) => {
          const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
          const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
          return dateB - dateA;
        });
      } else {
        filtered.sort((a, b) => {
          const hasPriceA = a.price_pen !== null && a.price_pen !== undefined && a.price_pen > 0;
          const hasPriceB = b.price_pen !== null && b.price_pen !== undefined && b.price_pen > 0;
          if (hasPriceA && !hasPriceB) return -1;
          if (!hasPriceA && hasPriceB) return 1;
          if (!hasPriceA && !hasPriceB) return 0;
          const priceA = a.price_pen!;
          const priceB = b.price_pen!;
          return sortOrder === 'asc' ? priceA - priceB : priceB - priceA;
        });
      }
    }

    return filtered;
  }, [allCourses, activeFilters, searchTerm, selectedCategory, selectedType, sortOrder, careerGoal, durationFilter, priceRange, selectedRegion]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [searchTerm, selectedCategory, activeFilters, careerGoal, durationFilter, priceRange, selectedRegion]);

  const totalPages = Math.ceil(filteredCourses.length / ITEMS_PER_PAGE);
  const paginatedCourses = filteredCourses.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  return (
    <div className="min-h-screen bg-white text-brand-slate font-sans selection:bg-brand-blue/10">

      {/* Hero */}
      <section className="relative">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute inset-0 bg-brand-slate" />
          <div className="absolute inset-0 opacity-[0.02]" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '24px 24px' }} />
          <div className="absolute bottom-0 left-1/4 w-64 h-64 md:w-96 md:h-96 bg-brand-blue/20 rounded-full blur-[100px]" />
          <div className="absolute top-0 right-1/4 w-48 h-48 bg-brand-mint/10 rounded-full blur-[80px]" />
        </div>

        <div className="relative mx-auto max-w-6xl px-6 pt-8 pb-10 md:pt-14 md:pb-14">
          <div className="max-w-2xl mb-5 space-y-3 md:space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/[0.06] px-3 py-1 border border-white/[0.08]">
              <div className="h-1.5 w-1.5 rounded-full bg-brand-mint" />
              <span className="text-[11px] font-medium text-white/50">
                Stud<span className="text-brand-blue font-bold">IA</span>Match — Data-driven decisions
              </span>
            </div>

            <h1 className="text-2xl md:text-4xl font-bold leading-[1.15] tracking-tight text-white text-balance">
              Elige tu próximo programa con{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-blue to-brand-mint">datos reales</span>
            </h1>

            <p className="text-sm md:text-base text-slate-300 leading-relaxed max-w-lg font-medium">
              Compara inversión, contenido y retorno financiero de programas tech en Perú.
            </p>
          </div>

          {/* Search bar — primera interacción */}
          <div id="hero-search" className="max-w-4xl scroll-mt-32">
            <div className="flex flex-col md:flex-row shadow-2xl rounded-2xl bg-white p-2 gap-2 focus-within:ring-4 focus-within:ring-brand-blue/20 transition-all border border-white/10 group">
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-slate-300 group-focus-within:text-brand-blue transition-colors" />
                </div>
                <Input
                  placeholder="¿Qué quieres estudiar hoy?"
                  className="pl-12 h-14 bg-transparent border-0 text-brand-slate font-medium text-base placeholder:text-slate-400 focus-visible:ring-0 rounded-xl"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div className="h-10 w-px bg-slate-100 self-center hidden md:block" />

              <div className="relative flex-shrink-0 flex items-center w-full md:w-[200px] md:min-w-[200px]">
                <Input
                  type="text"
                  inputMode="numeric"
                  placeholder="Precio Máx"
                  className="h-14 bg-transparent border-0 text-brand-slate font-medium text-base placeholder:text-slate-400 focus-visible:ring-0 pl-6 pr-4 w-full rounded-none shadow-none"
                  value={activeFilters.priceMax}
                  onKeyDown={(e) => {
                    if (['-', '+', 'e', 'E', '.', ','].includes(e.key)) e.preventDefault();
                  }}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === "" || /^\d+$/.test(val)) {
                      setActiveFilters({ ...activeFilters, priceMax: val });
                    }
                  }}
                />
                <button
                  onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : (prev === 'desc' ? null : 'asc'))}
                  className={cn(
                    "absolute right-4 p-1.5 rounded-md transition-all",
                    sortOrder ? "text-brand-blue bg-brand-blue/5" : "text-slate-300 hover:text-slate-500"
                  )}
                  title={sortOrder === 'asc' ? "Precio: Menor a Mayor" : (sortOrder === 'desc' ? "Precio: Mayor a Menor" : "Ordenar por precio")}
                >
                  {sortOrder === 'asc' ? <ArrowUpNarrowWide className="h-4 w-4" /> : 
                   sortOrder === 'desc' ? <ArrowDownWideNarrow className="h-4 w-4" /> : 
                   <ArrowUpDown className="h-4 w-4" />}
                </button>
              </div>

              <Button
                onClick={() => document.getElementById('programas')?.scrollIntoView({ behavior: 'smooth' })}
                className="w-full md:w-auto bg-brand-blue hover:bg-brand-blue/90 text-white font-bold rounded-xl px-10 h-14 text-sm transition-all hover:shadow-lg active:scale-[0.98]"
              >
                Explorar
              </Button>
            </div>
          </div>

          {/* Filtros y búsqueda personalizada */}
          <div className="mt-5 space-y-3">
            {/* Filtros primarios (3 visibles) */}
            <div className="flex flex-wrap items-center gap-2">
              {[
                { id: 'area', label: 'Área', icon: LayoutGrid, current: selectedCategory, setter: setSelectedCategory, options: activeCategories },
                { id: 'modalidad', label: 'Modalidad', icon: Globe, current: activeFilters.modes.length ? activeFilters.modes.join(", ") : "Todas", setter: (val: string) => setActiveFilters({ ...activeFilters, modes: val === "Todas" ? [] : [val] }), options: activeModes },
                { id: 'inst', label: 'Institución', icon: Building2, current: activeFilters.selectedInstitution, setter: (val: string) => setActiveFilters({ ...activeFilters, selectedInstitution: val }), options: activeInstitutions },
              ].map((filter) => (
                <div key={filter.id} className="relative">
                  <button
                    onClick={() => setActiveDropdown(activeDropdown === filter.id ? null : filter.id)}
                    className={cn(
                      "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all border",
                      activeDropdown === filter.id || (filter.current !== "Todos" && filter.current !== "Todas" && filter.current !== "")
                        ? "bg-brand-blue/10 border-brand-blue text-brand-blue shadow-sm"
                        : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:border-white/20"
                    )}
                  >
                    <filter.icon className="h-3.5 w-3.5" />
                    <span className="max-w-[100px] truncate">{filter.current === "Todos" || filter.current === "Todas" || filter.current === "" ? filter.label : filter.current}</span>
                    <ChevronDown className={cn("h-3 w-3 opacity-50 transition-transform", activeDropdown === filter.id && "rotate-180")} />
                  </button>

                  {activeDropdown === filter.id && (
                    <>
                      <div className="fixed inset-0 z-[60] bg-slate-900/40 backdrop-blur-sm md:hidden" onClick={() => setActiveDropdown(null)} />
                      <div className="fixed inset-0 z-40 hidden md:block" onClick={() => setActiveDropdown(null)} />
                      
                      <div className={cn(
                        "absolute top-full left-0 mt-2 w-64 bg-white rounded-xl shadow-elevated border border-slate-100 z-[70] overflow-hidden animate-in fade-in zoom-in-95 duration-100 origin-top-left",
                        "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 md:absolute md:top-full md:left-0 md:translate-x-0 md:translate-y-0"
                      )}>
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
                                filter.current === opt
                                  ? "bg-brand-blue text-white font-semibold"
                                  : "hover:bg-slate-50 text-slate-600"
                              )}
                            >
                              <span className="truncate">{opt}</span>
                              {opt !== "Todos" && opt !== "Todas" && (
                                <span className={cn(
                                  "text-[10px] tabular-nums px-1.5 py-0.5 rounded",
                                  filter.current === opt ? "bg-white/20" : "bg-slate-100 text-slate-400"
                                )}>
                                  {(contextualStats as Record<string, Record<string, number>>)[filter.id === 'area' ? 'categories' : (filter.id === 'inst' ? 'institutions' : 'types')][opt] || 0}
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

              {/* Más filtros collapsible */}
              <div className="relative">
                <button
                  onClick={() => setShowMoreFilters(!showMoreFilters)}
                  className={cn(
                    "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all border",
                    showMoreFilters
                      ? "bg-brand-blue/10 border-brand-blue text-brand-blue shadow-sm"
                      : "bg-white/5 border-white/10 text-white/50 hover:text-white/70 hover:bg-white/10"
                  )}
                >
                  <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", showMoreFilters && "rotate-180")} />
                  Más filtros
                </button>

                {showMoreFilters && (
                  <div className="absolute top-full left-0 mt-2 w-[320px] bg-white rounded-xl shadow-elevated border border-slate-100 z-[70] overflow-hidden animate-in fade-in zoom-in-95 duration-100 origin-top-left">
                    <div className="p-3 space-y-3">
                      <div className="flex flex-wrap gap-2">
                        {[
                          { id: 'tipo', label: 'Tipo', icon: GraduationCap, current: selectedType, setter: setSelectedType, options: activeTypes },
                          { id: 'region', label: 'Ubicación', icon: MapPin, current: selectedRegion, setter: setSelectedRegion, options: activeRegions },
                        ].map((filter) => (
                          <div key={filter.id} className="relative">
                            <button
                              onClick={() => setActiveDropdown(activeDropdown === filter.id ? null : filter.id)}
                              className={cn(
                                "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all border",
                                filter.current !== "Todos" && filter.current !== "Todas"
                                  ? "bg-brand-blue/10 border-brand-blue text-brand-blue"
                                  : "border-slate-200 text-slate-500 hover:text-slate-700"
                              )}
                            >
                              <filter.icon className="h-3 w-3" />
                              <span className="max-w-[80px] truncate">{filter.current === "Todos" || filter.current === "Todas" ? filter.label : filter.current}</span>
                              <ChevronDown className={cn("h-3 w-3 opacity-50 transition-transform", activeDropdown === filter.id && "rotate-180")} />
                            </button>

                            {activeDropdown === filter.id && (
                              <div className="absolute top-full left-0 mt-1 w-56 bg-white rounded-lg shadow-elevated border border-slate-100 z-[70] overflow-hidden">
                                <div className="p-1 max-h-56 overflow-y-auto custom-scrollbar">
                                  {filter.options.map((opt) => (
                                    <button
                                      key={opt}
                                      onClick={() => { filter.setter(opt === "Cualquier precio" ? "" : opt); setActiveDropdown(null); }}
                                      className={cn(
                                        "w-full text-left px-3 py-2 rounded-lg text-[12px] transition-all flex items-center justify-between",
                                        filter.current === opt ? "bg-brand-blue text-white font-semibold" : "hover:bg-slate-50 text-slate-600"
                                      )}
                                    >
                                      <span className="truncate">{opt}</span>
                                    </button>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>

                      <div className="border-t border-slate-100 pt-3">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Duración</p>
                        <div className="flex flex-wrap gap-1.5">
                          {[
                            { id: 'short', label: 'Cortos (<3m)' },
                            { id: 'medium', label: 'Estándar (3-6m)' },
                            { id: 'long', label: 'Largos (6+m)' },
                          ].map((d) => (
                            <button
                              key={d.id}
                              onClick={() => setDurationFilter(durationFilter === d.id ? null : d.id)}
                              className={cn(
                                "inline-flex px-2.5 py-1 rounded-md text-[11px] font-medium transition-all border",
                                durationFilter === d.id
                                  ? "bg-brand-blue/20 border-brand-blue/40 text-brand-blue"
                                  : "border-slate-200 text-slate-500 hover:text-slate-700"
                              )}
                            >
                              {d.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="border-t border-slate-100 pt-3">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Precio</p>
                        <div className="flex flex-wrap gap-1.5">
                          {[
                            { id: 'accessible', label: 'Accesible (S/0-1,500)' },
                            { id: 'standard', label: 'Estándar (S/1,500-5,000)' },
                            { id: 'premium', label: 'Premium (S/5,000-15,000)' },
                            { id: 'executive', label: 'Ejecutivo (S/15,000+)' },
                          ].map((p) => (
                            <button
                              key={p.id}
                              onClick={() => setPriceRange(priceRange === p.id ? null : p.id)}
                              className={cn(
                                "inline-flex px-2.5 py-1 rounded-md text-[11px] font-medium transition-all border",
                                priceRange === p.id
                                  ? "bg-brand-blue/20 border-brand-blue/40 text-brand-blue"
                                  : "border-slate-200 text-slate-500 hover:text-slate-700"
                              )}
                            >
                              {p.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Carrera goals + Quick sort row */}
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setShowGoals(!showGoals)}
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all border",
                  showGoals || careerGoal
                    ? "bg-brand-blue/20 border-brand-blue/40 text-brand-blue"
                    : "bg-white/5 border-white/10 text-white/40 hover:text-white/70 hover:bg-white/10"
                )}
              >
                <Sparkles className="h-3 w-3" />
                {careerGoal ? careerGoals.find(g => g.id === careerGoal)?.label : "Personalizar"}
                <ChevronDown className={cn("h-3 w-3 opacity-50 transition-transform", showGoals && "rotate-180")} />
              </button>

              {showGoals && (
                <div className="flex flex-wrap items-center gap-1.5">
                  {careerGoals.map((goal) => (
                    <button
                      key={goal.id}
                      onClick={() => { setCareerGoal(careerGoal === goal.id ? null : goal.id); setShowGoals(false); }}
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all border whitespace-nowrap",
                        careerGoal === goal.id
                          ? "bg-brand-mint/15 border-brand-mint/30 text-brand-mint"
                          : "bg-white/5 border-white/10 text-white/50 hover:text-white/70 hover:bg-white/10"
                      )}
                      title={goal.desc}
                    >
                      <goal.icon className="h-3 w-3" />
                      {goal.label}
                    </button>
                  ))}
                </div>
              )}

              <span className="text-white/15 mx-0.5 hidden sm:inline">|</span>

              <span className="text-[10px] font-bold text-white/30 uppercase tracking-widest hidden sm:inline">Ordenar:</span>
              {[
                { id: 'popular', label: 'Populares', icon: TrendingUp },
                { id: 'recent', label: 'Recientes', icon: Clock },
              ].map((qs) => (
                <button
                  key={qs.id}
                  onClick={() => setSortOrder(prev => prev === qs.id ? null : qs.id)}
                  className={cn(
                    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all border",
                    sortOrder === qs.id
                      ? "bg-brand-mint/15 border-brand-mint/30 text-brand-mint"
                      : "bg-white/5 border-white/10 text-white/50 hover:text-white/70 hover:bg-white/10"
                  )}
                >
                  <qs.icon className="h-3 w-3" />
                  {qs.label}
                </button>
              ))}
              {!['popular', 'recent'].includes(sortOrder || '') && sortOrder && (
                <button
                  onClick={() => setSortOrder(null)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium border bg-brand-mint/15 border-brand-mint/30 text-brand-mint transition-all"
                >
                  <RotateCcw className="h-3 w-3" />
                  {sortOrder === 'roi' ? 'Mejor ROI' : sortOrder === 'price' ? 'Más accesibles' : sortOrder === 'asc' ? 'Precio ↑' : sortOrder === 'desc' ? 'Precio ↓' : sortOrder}
                </button>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Catalog */}
      <div id="programas" className="mx-auto max-w-6xl px-6 py-8 md:py-12 scroll-mt-16">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-brand-slate">Catálogo de Programas</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <p className="text-[13px] text-slate-400 font-medium">{filteredCourses.length} resultados encontrados</p>
              <span className="text-slate-300 mx-0.5">·</span>
              <p className="text-[13px] text-slate-400 font-medium tabular-nums">
                <span className="text-brand-blue font-semibold">{allCourses.length || 0}</span> programas | <span className="text-brand-mint font-semibold">{Object.keys(stats.institutions).length}</span> instituciones
              </p>
              {lastUpdated && (
                <p className="text-[10px] text-slate-300">
                  · Actualizado {lastUpdated.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })}
                </p>
              )}
              {(searchTerm || selectedCategory !== "Todos" || selectedType !== "Todos" || activeFilters.selectedInstitution !== "Todas" || activeFilters.modes.length > 0 || activeFilters.priceMax || sortOrder) && (
                <>
                  <span className="text-slate-300">·</span>
                  <button 
                    onClick={() => {
                      setSearchTerm("");
                      setSelectedCategory("Todos");
                      setSelectedType("Todos");
                      setSortOrder(null);
                      setCareerGoal(null);
                      setDurationFilter(null);
                      setPriceRange(null);
                      setSelectedRegion("Todas");
                      setActiveFilters({
                        priceMin: "",
                        priceMax: "",
                        modes: [],
                        durations: [],
                        selectedInstitution: "Todas",
                        includeConsultar: true
                      });
                    }}
                    className="text-[11px] font-bold text-brand-blue hover:text-brand-blue/80 uppercase tracking-wider flex items-center gap-1 transition-colors group"
                  >
                    <RotateCcw className="h-3 w-3 group-hover:rotate-[-45deg] transition-transform" />
                    Limpiar todo
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6 relative items-start">
          <main className="flex-1 min-w-0">
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-40 rounded-xl bg-slate-50 animate-pulse" style={{ animationDelay: `${(i - 1) * 100}ms` }} />
                ))}
              </div>
            ) : filteredCourses.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 transition-all duration-300">
                  {paginatedCourses.map((course) => {
                  const modeBadge = course.mode?.toLowerCase() === 'presencial' ? { icon: '🏫', label: 'Presencial', color: 'bg-blue-50 text-blue-700' }
                    : course.mode?.toLowerCase() === 'remoto' ? { icon: '🌐', label: 'Remoto', color: 'bg-emerald-50 text-emerald-700' }
                    : course.mode?.toLowerCase() === 'híbrido' || course.mode?.toLowerCase() === 'hibrido' ? { icon: '🔀', label: 'Híbrido', color: 'bg-violet-50 text-violet-700' }
                    : null;
                  const price = course.price_pen;
                  const priceRangeBadge = price && price > 0
                    ? price <= 1500 ? { label: '🟢 Accesible' }
                    : price <= 5000 ? { label: '🟡 Estándar' }
                    : price <= 15000 ? { label: '🟠 Premium' }
                    : { label: '🔴 Ejecutivo' }
                    : null;
                  const canShowBadges = (b: { icon?: string; label: string; color: string } | null): b is { icon?: string; label: string; color: string } => b !== null;
                  const visibleBadges = [
                    modeBadge,
                    course.certification ? { icon: '🏆', label: 'Certificación', color: 'bg-amber-50 text-amber-700' } : null,
                    priceRangeBadge ? { label: priceRangeBadge.label, color: 'bg-slate-50 text-slate-600' } : null,
                  ].filter(canShowBadges).slice(0, 3);
                  return (
                  <article key={course.id} className="group flex flex-col bg-white rounded-xl border border-slate-100 hover:border-slate-200 transition-all duration-200 hover:shadow-card overflow-hidden">
                    <div className="p-5 flex-1 flex flex-col">
                      <Link href={`/courses/${cleanSlug(course.institution_slug || 'general')}/${course.slug}`} className="group/title">
                        <h3 className="text-[15px] font-semibold text-brand-slate leading-snug group-hover/title:text-brand-blue transition-colors line-clamp-2">
                          {course.name}
                        </h3>
                      </Link>

                      <div className="flex items-center gap-1.5 mt-1.5">
                        <span className="text-[12px] font-medium text-slate-400">{course.institution_name}</span>
                        {course.is_verified && (
                          <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-emerald-600">
                            <Verified className="h-2.5 w-2.5" />
                          </span>
                        )}
                        <span className="text-[11px] text-slate-300">·</span>
                        <span className="text-[11px] text-slate-400">{course.course_type || "Programa"}</span>
                      </div>

                      {course.category && (
                        <p className="text-[11px] text-slate-300 mt-1">{course.category}</p>
                      )}

                      <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
                        {visibleBadges.map((badge, i) => (
                          <span key={i} className={`inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded ${badge.color}`}>
                            {badge.icon && <span className="text-[11px]">{badge.icon}</span>}
                            {badge.label}
                          </span>
                        ))}
                        {(course.view_count ?? 0) > 0 && (
                          <span className="text-[10px] text-slate-300 tabular-nums">· {course.view_count} visitas</span>
                        )}
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-50">
                        <div className="grid grid-cols-2 gap-y-3">
                          <div>
                            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Inversión</p>
                            <p className="text-[13px] font-semibold text-brand-slate tabular-nums truncate">
                              {course.price_status === 'consultar' || !course.price_pen || course.price_pen <= 0 ? "Consultar" : `S/ ${course.price_pen.toLocaleString()}`}
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">ROI</p>
                            <p className="text-[13px] font-semibold text-brand-slate truncate">
                              {course.roi_months ? `${course.roi_months.toFixed(1)} meses` : "—"}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 mt-3 pt-2 border-t border-slate-50">
                        <Link
                          href={`/courses/${cleanSlug(course.institution_slug || 'general')}/${course.slug}`}
                          className="flex-1 flex items-center justify-center gap-1.5 h-9 rounded-lg bg-brand-blue hover:bg-brand-blue/90 text-white text-[13px] font-medium transition-all active:scale-[0.98]"
                        >
                          Ver detalle <ArrowRight className="h-3 w-3" />
                        </Link>
                      </div>
                    </div>
                  </article>
                );
                })}

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
              <div className="py-16 text-center rounded-xl border-2 border-dashed border-slate-100">
                <Search className="h-10 w-10 text-slate-200 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-400">Sin resultados</h3>
                <p className="text-[13px] text-slate-400 mt-1 mb-6 max-w-md mx-auto">
                  {selectedCategory !== "Todos" && activeFilters.selectedInstitution !== "Todas"
                    ? `No encontramos programas de ${selectedCategory} en ${activeFilters.selectedInstitution}.`
                    : selectedCategory !== "Todos"
                    ? `No encontramos programas de ${selectedCategory} con los filtros actuales.`
                    : activeFilters.selectedInstitution !== "Todas"
                    ? `No encontramos programas en ${activeFilters.selectedInstitution} con los filtros actuales.`
                    : "Intenta con otros filtros o términos de búsqueda."}
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  {selectedCategory !== "Todos" && (
                    <Button variant="outline" size="sm" onClick={() => setSelectedCategory("Todos")} className="rounded-lg text-[11px]">
                      Ver todas las áreas
                    </Button>
                  )}
                  {activeFilters.selectedInstitution !== "Todas" && (
                    <Button variant="outline" size="sm" onClick={() => setActiveFilters({ ...activeFilters, selectedInstitution: "Todas" })} className="rounded-lg text-[11px]">
                      Ver todas las instituciones
                    </Button>
                  )}
                  {activeFilters.modes.length > 0 && (
                    <Button variant="outline" size="sm" onClick={() => setActiveFilters({ ...activeFilters, modes: [] })} className="rounded-lg text-[11px]">
                      Ver todas las modalidades
                    </Button>
                  )}
                  <Button variant="outline" size="sm" onClick={() => { 
                    setSearchTerm(""); 
                    setSelectedCategory("Todos"); 
                    setSelectedType("Todos");
                    setSortOrder(null);
                    setCareerGoal(null);
                    setActiveFilters({ 
                      priceMin: "", 
                      priceMax: "", 
                      modes: [], 
                      durations: [], 
                      selectedInstitution: "Todas", 
                      includeConsultar: true 
                    }); 
                  }} className="rounded-lg text-[11px]">Reiniciar todos los filtros</Button>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Compare Bar */}
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

      {/* Cómo Funciona */}
      <section id="como-funciona" className="section-spacing bg-slate-50/50 scroll-mt-16">
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

      {/* Nosotros */}
      <section id="nosotros" className="section-spacing scroll-mt-16">
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

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 section-spacing">
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

      {/* Modal */}
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
                  <div>
                    <label className="text-[12px] font-medium text-slate-400 mb-1 block">Área de interés</label>
                    <select
                      className="w-full h-10 rounded-lg bg-slate-50 border-0 px-3 text-[13px] appearance-none focus:ring-1 focus:ring-brand-blue/30"
                      value={formData.area_interest}
                      onChange={(e) => setFormData({ ...formData, area_interest: e.target.value })}
                    >
                      <option value="">Selecciona un área</option>
                      {Array.from(new Set(allCourses.map(c => c.category).filter(Boolean))).sort().map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-slate-400 mb-1 block">Presupuesto estimado</label>
                    <select
                      className="w-full h-10 rounded-lg bg-slate-50 border-0 px-3 text-[13px] appearance-none focus:ring-1 focus:ring-brand-blue/30"
                      value={formData.budget}
                      onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                    >
                      <option value="">Selecciona un rango</option>
                      <option value="5000">S/ 0 - 5,000</option>
                      <option value="15000">S/ 5,000 - 15,000</option>
                      <option value="30000">S/ 15,000 - 30,000</option>
                      <option value="999999">S/ 30,000+</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-slate-400 mb-1 block">Modalidad preferida</label>
                    <select
                      className="w-full h-10 rounded-lg bg-slate-50 border-0 px-3 text-[13px] appearance-none focus:ring-1 focus:ring-brand-blue/30"
                      value={formData.modality}
                      onChange={(e) => setFormData({ ...formData, modality: e.target.value })}
                    >
                      <option value="Remoto">Remoto</option>
                      <option value="Presencial">Presencial</option>
                      <option value="Híbrido">Híbrido</option>
                      <option value="Sin preferencia">Sin preferencia</option>
                    </select>
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