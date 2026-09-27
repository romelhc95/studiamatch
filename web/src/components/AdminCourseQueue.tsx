'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, Building2, ChevronLeft, ChevronRight, CircleHelp, Filter, Search, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MfaRequiredCard } from '@/components/admin/MfaRequiredCard';
import { EDITORIAL_STATUS_META, QUALITY_STATUS_META, StatusBadge, type EditorialStatus, type QualityStatus } from '@/components/admin/editorial-ui';
import { adminRpc, getAuthenticatorAssuranceLevel, isMfaRequiredError } from '@/lib/admin-auth';

interface Course {
  course_id: string;
  course_name: string;
  course_slug: string;
  institution_name: string;
  institution_slug: string;
  editorial_status: EditorialStatus;
  quality_status: QualityStatus;
  missing_fields: string[];
  is_sponsored: boolean;
  version: number;
  updated_at: string;
}

interface QueueRow {
  courses: Course[];
  page_info: { hasNextPage: boolean; endCursor: Record<string, string> | null };
  error: string | null;
}

interface CountRow {
  total: number | null;
  error: string | null;
}

interface InstitutionOption {
  slug: string;
  name: string;
}

interface FacetsRow {
  editorial_counts: Partial<Record<EditorialStatus, number>>;
  quality_counts: Partial<Record<QualityStatus, number>>;
  institutions: InstitutionOption[];
  error: string | null;
}

const EDITORIAL_ORDER: EditorialStatus[] = ['draft', 'pending_review', 'published', 'archived'];
const QUALITY_ORDER: QualityStatus[] = ['pending', 'complete', 'blocked'];

function StatusCounter({ kind, value, count }: { kind: 'editorial' | 'quality'; value: string; count: number }) {
  const meta = kind === 'editorial'
    ? EDITORIAL_STATUS_META[value as EditorialStatus]
    : QUALITY_STATUS_META[value as QualityStatus];
  const Icon = meta.icon;

  return (
    <div className={`group rounded-2xl border p-4 transition-all hover:-translate-y-0.5 hover:shadow-lg ${meta.className}`} title={meta.description}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] opacity-70">{kind === 'editorial' ? 'Editorial' : 'Calidad'}</p>
          <p className="mt-2 text-sm font-bold">{meta.label}</p>
        </div>
        <Icon className="size-5 opacity-70 transition-transform group-hover:scale-110" aria-hidden="true" />
      </div>
      <p className="mt-3 text-3xl font-black tracking-tight">{count}</p>
    </div>
  );
}

function StatusLegend({ kind }: { kind: 'editorial' | 'quality' }) {
  const entries = kind === 'editorial'
    ? EDITORIAL_ORDER.map((value) => [value, EDITORIAL_STATUS_META[value]] as const)
    : QUALITY_ORDER.map((value) => [value, QUALITY_STATUS_META[value]] as const);

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {entries.map(([value, meta]) => (
        <div key={value} className="flex items-start gap-2 rounded-xl border border-slate-100 bg-white/70 p-3">
          <StatusBadge kind={kind} value={value} compact />
          <p className="text-xs leading-5 text-slate-500">{meta.description}</p>
        </div>
      ))}
    </div>
  );
}

export default function AdminCourseQueue({ role }: { role: 'admin' | 'user' }) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [facetsLoading, setFacetsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [endCursor, setEndCursor] = useState<Record<string, string> | null>(null);
  const [currentCursor, setCurrentCursor] = useState<Record<string, string> | null>(null);
  const [cursorHistory, setCursorHistory] = useState<Array<Record<string, string> | null>>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [institutionSlug, setInstitutionSlug] = useState('__all__');
  const [editorialCounts, setEditorialCounts] = useState<Partial<Record<EditorialStatus, number>>>({});
  const [qualityCounts, setQualityCounts] = useState<Partial<Record<QualityStatus, number>>>({});
  const [institutions, setInstitutions] = useState<InstitutionOption[]>([]);
  const [showLegend, setShowLegend] = useState(false);
  const [assurance, setAssurance] = useState<'checking' | 'aal1' | 'aal2'>('checking');
  const [filters, setFilters] = useState({
    editorial_status: role === 'admin' ? 'pending_review' : 'draft',
    quality_status: role === 'admin' ? 'complete' : 'pending',
  });

  const fetchFacets = useCallback(async () => {
    setFacetsLoading(true);
    try {
      const rows = (await adminRpc('admin_get_course_queue_facets', {})) as FacetsRow[];
      const facets = rows[0];
      if (!facets || facets.error) throw new Error(facets?.error || 'No se pudo cargar el resumen de la cola.');
      setEditorialCounts(facets.editorial_counts || {});
      setQualityCounts(facets.quality_counts || {});
      setInstitutions(Array.isArray(facets.institutions) ? facets.institutions : []);
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
      } else if (!error) {
        setError(reason instanceof Error ? reason.message : 'No se pudo cargar el resumen de la cola.');
      }
    } finally {
      setFacetsLoading(false);
    }
  }, [error]);

  const fetchQueue = useCallback(async (cursor: Record<string, string> | null = null) => {
    setLoading(true);
    setError(null);
    setMfaRequired(false);

    try {
      const institution = institutionSlug === '__all__' ? null : institutionSlug;
      const [queueRows, countRows] = await Promise.all([
        adminRpc('admin_get_course_queue_filtered', {
          p_first: 20,
          p_after_cursor: cursor ? JSON.stringify(cursor) : null,
          p_editorial_status: filters.editorial_status || null,
          p_quality_status: filters.quality_status || null,
          p_institution_slug: institution,
        }) as Promise<QueueRow[]>,
        adminRpc('admin_count_course_queue_filtered', {
          p_editorial_status: filters.editorial_status || null,
          p_quality_status: filters.quality_status || null,
          p_institution_slug: institution,
        }) as Promise<CountRow[]>,
      ]);

      const queue = queueRows[0];
      const count = countRows[0];
      if (!queue || queue.error) throw new Error(queue?.error || 'Respuesta inválida de la cola.');
      if (!count || count.error) throw new Error(count?.error || 'Respuesta inválida del contador.');

      setCourses(Array.isArray(queue.courses) ? queue.courses : []);
      setCurrentCursor(cursor);
      setHasNextPage(Boolean(queue.page_info?.hasNextPage));
      setEndCursor(queue.page_info?.endCursor || null);
      setTotalCount(count.total || 0);
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al cargar la cola.');
    } finally {
      setLoading(false);
    }
  }, [filters.editorial_status, filters.quality_status, institutionSlug]);

  const reloadAll = useCallback(() => {
    setCursorHistory([]);
    setMfaRequired(false);
    setAssurance('aal2');
    void Promise.all([fetchFacets(), fetchQueue(null)]);
  }, [fetchFacets, fetchQueue]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void getAuthenticatorAssuranceLevel()
        .then(({ currentLevel }) => {
          setAssurance(currentLevel);
          setMfaRequired(currentLevel !== 'aal2');
        })
        .catch((reason) => {
          if (isMfaRequiredError(reason)) {
            setAssurance('aal1');
            setMfaRequired(true);
          } else {
            setError(reason instanceof Error ? reason.message : 'No se pudo verificar el nivel de autenticación.');
          }
        });
    }, 0);
    return () => window.clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (assurance !== 'aal2') return;
    const timeout = window.setTimeout(() => {
      void fetchQueue(null);
    }, 0);
    return () => window.clearTimeout(timeout);
  }, [assurance, fetchQueue]);

  useEffect(() => {
    if (assurance !== 'aal2') return;
    const timeout = window.setTimeout(() => {
      void fetchFacets();
    }, 0);
    return () => window.clearTimeout(timeout);
  }, [assurance, fetchFacets]);

  const visibleCourses = useMemo(() => {
    const term = searchTerm.trim().toLocaleLowerCase('es');
    if (!term) return courses;
    return courses.filter((course) => course.course_name.toLocaleLowerCase('es').includes(term));
  }, [courses, searchTerm]);

  const updateFilter = (key: 'editorial_status' | 'quality_status', value: string) => {
    setCursorHistory([]);
    setFilters((current) => ({ ...current, [key]: value === '__all__' ? '' : value }));
  };

  const updateInstitution = (value: string) => {
    setCursorHistory([]);
    setInstitutionSlug(value);
  };

  if (mfaRequired) {
    return <MfaRequiredCard onVerified={reloadAll} />;
  }

  if (assurance === 'checking') {
    return <Card className="border-0 bg-white/80 p-12 text-center text-sm text-slate-600 shadow-card">Verificando la seguridad de la sesión...</Card>;
  }

  if (loading && courses.length === 0) {
    return <Card className="border-0 bg-white/80 p-12 text-center text-sm text-slate-600 shadow-card">Cargando cola editorial...</Card>;
  }

  if (error) {
    return (
      <Card className="border-0 bg-white p-8 text-center shadow-card">
        <h3 className="text-lg font-semibold text-slate-900">No pudimos cargar la cola</h3>
        <p className="mt-2 text-sm text-slate-600">{error}</p>
        <Button onClick={reloadAll} className="mt-6" variant="outline">Reintentar</Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] bg-brand-slate p-6 text-white shadow-elevated sm:p-8">
        <div className="pointer-events-none absolute -right-24 -top-28 size-72 rounded-full bg-brand-blue/30 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-36 left-1/3 size-72 rounded-full bg-brand-mint/10 blur-3xl" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <div className="mb-4 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.25em] text-brand-mint">
              <Sparkles className="size-4" aria-hidden="true" /> Control editorial
            </div>
            <h2 className="text-3xl font-black tracking-tight sm:text-4xl">Una vista clara para decidir qué sigue.</h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">Revisa completitud, calidad y publicación desde un mismo espacio. Cada color explica el estado del programa.</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/10 px-5 py-4 backdrop-blur-sm">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-300">Vista actual</p>
            <p className="mt-1 text-3xl font-black text-white">{totalCount}</p>
            <p className="text-xs text-slate-300">programas en este filtro</p>
          </div>
        </div>
      </section>

      <section aria-labelledby="queue-status-title" className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-blue">Lectura rápida</p>
            <h2 id="queue-status-title" className="mt-1 text-xl font-bold text-brand-slate">Estado de la operación</h2>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={() => setShowLegend((current) => !current)}>
            <CircleHelp className="size-4" /> {showLegend ? 'Ocultar guía' : 'Entender estados'}
          </Button>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {EDITORIAL_ORDER.map((status) => <StatusCounter key={status} kind="editorial" value={status} count={editorialCounts[status] || 0} />)}
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {QUALITY_ORDER.map((status) => <StatusCounter key={status} kind="quality" value={status} count={qualityCounts[status] || 0} />)}
        </div>
        {showLegend && (
          <div className="grid gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 lg:grid-cols-2">
            <div><p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-slate-500">Editorial</p><StatusLegend kind="editorial" /></div>
            <div><p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-slate-500">Calidad</p><StatusLegend kind="quality" /></div>
          </div>
        )}
      </section>

      <Card className="border-slate-200/80 bg-white/90 p-5 shadow-card sm:p-6">
        <div className="mb-5 flex items-center gap-2">
          <Filter className="size-4 text-brand-blue" aria-hidden="true" />
          <div>
            <h2 className="text-base font-bold text-brand-slate">Filtrar programas</h2>
            <p className="text-xs text-slate-500">La institución se selecciona del catálogo; no se escribe manualmente.</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="space-y-2">
            <Label htmlFor="editorial-status-filter">Estado editorial</Label>
            <Select value={filters.editorial_status || '__all__'} onValueChange={(value) => updateFilter('editorial_status', value)}>
              <SelectTrigger id="editorial-status-filter"><SelectValue placeholder="Todos los estados" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Todos los estados</SelectItem>
                {EDITORIAL_ORDER.map((status) => <SelectItem key={status} value={status}>{EDITORIAL_STATUS_META[status].label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="quality-status-filter">Estado de calidad</Label>
            <Select value={filters.quality_status || '__all__'} onValueChange={(value) => updateFilter('quality_status', value)}>
              <SelectTrigger id="quality-status-filter"><SelectValue placeholder="Todas las calidades" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Todas las calidades</SelectItem>
                {QUALITY_ORDER.map((status) => <SelectItem key={status} value={status}>{QUALITY_STATUS_META[status].label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="institution-filter">Institución</Label>
            <Select value={institutionSlug} onValueChange={updateInstitution} disabled={facetsLoading}>
              <SelectTrigger id="institution-filter"><SelectValue placeholder={facetsLoading ? 'Cargando instituciones...' : 'Todas las instituciones'} /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Todas las instituciones</SelectItem>
                {institutions.map((institution) => <SelectItem key={institution.slug} value={institution.slug}>{institution.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="admin-search">Buscar curso</Label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
              <Input id="admin-search" className="pl-9" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Nombre del curso" />
            </div>
          </div>
        </div>
      </Card>

      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Resultados</p>
          <p className="mt-1 text-sm text-slate-600">Mostrando <span className="font-bold text-slate-900">{visibleCourses.length}</span> en esta página de <span className="font-bold text-slate-900">{totalCount}</span>.</p>
        </div>
        {loading && <span className="text-xs font-semibold text-brand-blue" role="status">Actualizando...</span>}
      </div>

      {visibleCourses.length === 0 ? (
        <Card className="border-dashed border-slate-300 bg-white/70 p-12 text-center shadow-none">
          <Building2 className="mx-auto size-8 text-slate-300" aria-hidden="true" />
          <p className="mt-4 text-sm font-semibold text-slate-700">No encontramos programas con estos filtros.</p>
          <p className="mt-1 text-xs text-slate-500">Prueba otra institución o combina los estados disponibles.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {visibleCourses.map((course) => (
            <Card key={course.course_id} className="group border-slate-200/80 bg-white p-5 shadow-card transition-all hover:-translate-y-0.5 hover:border-brand-blue/30 hover:shadow-elevated sm:p-6">
              <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-blue/5 px-2.5 py-1 text-[10px] font-black uppercase tracking-wider text-brand-blue">
                      <Building2 className="size-3" aria-hidden="true" /> {course.institution_name}
                    </span>
                    {course.is_sponsored && <Badge className="border-amber-200 bg-amber-50 text-[10px] text-amber-700">Patrocinado</Badge>}
                  </div>
                  <h3 className="mt-3 truncate text-lg font-bold tracking-tight text-brand-slate sm:text-xl">{course.course_name}</h3>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <StatusBadge kind="editorial" value={course.editorial_status} />
                    <StatusBadge kind="quality" value={course.quality_status} />
                    {course.missing_fields.length > 0 && <span className="text-xs text-slate-500">{course.missing_fields.length} campos por completar</span>}
                  </div>
                </div>
                <div className="flex items-center gap-3 lg:pl-6">
                  <span className="hidden text-right text-[10px] font-semibold uppercase tracking-wider text-slate-400 sm:block">Versión {course.version}</span>
                  <Link href={`/admin/edit/?id=${encodeURIComponent(course.course_id)}`} className="inline-flex items-center gap-2 rounded-xl bg-brand-blue px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-brand-blue/20 transition hover:-translate-y-0.5 hover:bg-brand-blue/90">
                    Editar <ArrowUpRight className="size-4" aria-hidden="true" />
                  </Link>
                  {course.editorial_status === 'published' && (
                    <Link href={`/courses/${course.institution_slug}/${course.course_slug}/`} target="_blank" rel="noopener noreferrer" className="hidden items-center gap-1 text-sm font-semibold text-slate-500 transition hover:text-brand-blue sm:inline-flex">
                      Ver <ArrowUpRight className="size-3.5" aria-hidden="true" />
                    </Link>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {(cursorHistory.length > 0 || hasNextPage) && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <Button variant="outline" disabled={cursorHistory.length === 0 || loading} onClick={() => {
            const history = [...cursorHistory];
            const previous = history.pop() || null;
            setCursorHistory(history);
            void fetchQueue(previous);
          }}><ChevronLeft className="size-4" /> Anterior</Button>
          <Button variant="outline" disabled={!hasNextPage || !endCursor || loading} onClick={() => {
            setCursorHistory((history) => [...history, currentCursor]);
            void fetchQueue(endCursor);
          }}>Siguiente <ChevronRight className="size-4" /></Button>
        </div>
      )}
    </div>
  );
}
