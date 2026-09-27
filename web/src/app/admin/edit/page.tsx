'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';
import { Archive, ArrowDown, ArrowLeft, CheckCircle2, Eye, Info, Save, Send, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import CourseLivePreview, { type CourseLivePreviewData } from '@/components/admin/CourseLivePreview';
import { getFieldCopy, QUALITY_STATUS_META, StatusBadge } from '@/components/admin/editorial-ui';
import { MfaRequiredCard } from '@/components/admin/MfaRequiredCard';
import { adminRpc, getAuthenticatorAssuranceLevel, isMfaRequiredError, requireActiveAdmin, type AdminRole } from '@/lib/admin-auth';

interface CourseData {
  course_id: string;
  course_name: string;
  institution_name: string;
  editorial_status: string;
  quality_status: string;
  version: number;
  manual_overrides: Record<string, string>;
  missing_fields: string[];
  is_sponsored: boolean;
  lead_cta_enabled: boolean;
  published_at: string | null;
  category?: string;
  course_type?: string;
  expected_monthly_salary?: number | null;
  roi_months?: number | null;
  seniority_level?: string;
}

interface FieldDefinition {
  field_key: string;
  target_column: string;
  description: string;
  is_required_for_publish: boolean;
  is_editable?: boolean;
  current_value?: string | number | null;
}

interface DetailRow {
  course: CourseData | null;
  field_definitions: FieldDefinition[];
  error: string | null;
}

interface UpdateRow {
  success: boolean;
  course_id: string | null;
  new_version: number | null;
  error: string | null;
}

interface StatusRow {
  success: boolean;
  course_id: string | null;
  new_status: string | null;
  error: string | null;
}

function AdminCourseEditor() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const courseId = searchParams.get('id') || '';
  const [course, setCourse] = useState<CourseData | null>(null);
  const [fieldDefinitions, setFieldDefinitions] = useState<FieldDefinition[]>([]);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [role, setRole] = useState<AdminRole>('anon');
  const [qualityStatus, setQualityStatus] = useState('pending');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [initialFormData, setInitialFormData] = useState<Record<string, string>>({});
  const [activePreviewField, setActivePreviewField] = useState<string | null>(null);

  const isAdmin = role === 'admin';

  const loadCourse = useCallback(async () => {
    setLoading(true);
    setError(null);
    setMfaRequired(false);
    try {
      const currentRole = await requireActiveAdmin();
      setRole(currentRole);
      const assurance = await getAuthenticatorAssuranceLevel();
      if (assurance.currentLevel !== 'aal2') {
        setMfaRequired(true);
        return;
      }
      if (!courseId) throw new Error('Identificador de curso inválido.');
      const rows = (await adminRpc('admin_get_course_editorial', { p_course_id: courseId })) as DetailRow[];
      const detail = rows[0];
      if (!detail || detail.error || !detail.course) throw new Error(detail?.error || 'Curso no encontrado.');
      setCourse(detail.course);
      setQualityStatus(detail.course.quality_status);
      const defs = Array.isArray(detail.field_definitions) ? detail.field_definitions : [];
      setFieldDefinitions(defs);
      const initial: Record<string, string> = {};
      for (const field of defs) {
        const override = detail.course.manual_overrides?.[field.field_key];
        initial[field.field_key] = override !== undefined ? String(override) : String(field.current_value ?? '');
      }
      setFormData(initial);
      setInitialFormData(initial);
      setActivePreviewField(null);
      setConflict(false);
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al cargar el curso.');
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadCourse(), 0);
    return () => window.clearTimeout(timeout);
  }, [loadCourse]);

  useEffect(() => {
    if (!activePreviewField) return;
    const frame = window.requestAnimationFrame(() => {
      document.getElementById(`preview-impact-${activePreviewField}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [activePreviewField]);

  const handleSave = async () => {
    if (!course) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    setConflict(false);
    try {
      const allowedKeys = isAdmin
        ? fieldDefinitions.map((field) => field.field_key)
        : fieldDefinitions.filter((field) => course.missing_fields.includes(field.field_key)).map((field) => field.field_key);
      const payload: Record<string, string> = {};
      for (const key of allowedKeys) {
        if (key in formData) {
          payload[key] = formData[key];
        }
      }
      const rows = (await adminRpc('admin_update_course', {
        p_course_id: course.course_id,
        p_manual_overrides: payload,
        p_version: course.version,
        p_reason: 'Edición desde panel admin',
      })) as UpdateRow[];
      const result = rows[0];
      if (!result || !result.success) {
        if (result?.error?.startsWith('Version conflict')) setConflict(true);
        throw new Error(result?.error || 'Error al guardar.');
      }
      setCourse((current) => current && result.new_version ? { ...current, version: result.new_version, manual_overrides: { ...current.manual_overrides, ...payload } } : current);
      setInitialFormData((current) => ({ ...current, ...payload }));
      setSuccess('Cambios guardados correctamente.');
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al guardar.');
    } finally {
      setSaving(false);
    }
  };

  const updatePublication = async (action: 'admin_publish_course' | 'admin_unpublish_course') => {
    if (!course || role !== 'admin') return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const rows = (await adminRpc(action, {
        p_course_id: course.course_id,
        p_reason: action === 'admin_publish_course' ? 'Publicación desde panel admin' : 'Despublicación desde panel admin',
      })) as StatusRow[];
      const result = rows[0];
      if (!result || !result.success || !result.new_status) throw new Error(result?.error || 'No se pudo cambiar el estado.');
      setCourse((current) => current ? { ...current, editorial_status: result.new_status as string, version: current.version + 1 } : current);
      setSuccess(action === 'admin_publish_course' ? 'Curso publicado.' : 'Curso despublicado.');
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al cambiar el estado.');
    } finally {
      setSaving(false);
    }
  };

  const updateAdminStatus = async (action: 'admin_archive_course' | 'admin_update_quality_status', qualityStatus?: string) => {
    if (!course || role !== 'admin') return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const rows = action === 'admin_archive_course'
        ? await adminRpc(action, { p_course_id: course.course_id, p_reason: 'Archivado desde panel admin' })
        : await adminRpc(action, { p_course_id: course.course_id, p_quality_status: qualityStatus, p_reason: 'Actualización de calidad desde panel admin' });
      const result = (rows as StatusRow[])[0];
      if (!result || !result.success || !result.new_status) throw new Error(result?.error || 'No se pudo cambiar el estado.');
      setCourse((current) => current ? {
        ...current,
        editorial_status: action === 'admin_archive_course' ? result.new_status || current.editorial_status : current.editorial_status,
        quality_status: action === 'admin_update_quality_status' ? result.new_status || current.quality_status : current.quality_status,
        version: current.version + 1,
      } : current);
      setSuccess(action === 'admin_archive_course' ? 'Curso archivado.' : 'Calidad actualizada.');
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al cambiar el estado.');
    } finally {
      setSaving(false);
    }
  };

  const updateField = (fieldKey: string, value: string) => {
    setFormData((current) => ({ ...current, [fieldKey]: value }));
    setActivePreviewField(fieldKey);
  };

  const jumpToPreview = (fieldKey: string) => {
    if (activePreviewField === fieldKey) {
      window.requestAnimationFrame(() => {
        document.getElementById(`preview-impact-${fieldKey}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
      return;
    }
    setActivePreviewField(fieldKey);
  };

  if (loading) return <Card className="p-12 text-center text-sm text-slate-600">Cargando curso...</Card>;
  if (mfaRequired && !course) return <div className="min-h-screen bg-slate-50 px-6 py-8"><main className="mx-auto max-w-5xl"><MfaRequiredCard onVerified={() => void loadCourse()} /></main></div>;
  if (!course) return <Card className="p-8 text-center text-sm text-red-600">{error || 'Curso no encontrado.'}</Card>;

  const editableFields = fieldDefinitions.filter((field) => isAdmin || field.is_editable !== false);
  const readOnlyFields = fieldDefinitions.filter((field) => !isAdmin && field.is_editable === false);
  const hasDraftChanges = Object.keys(initialFormData).some((key) => (formData[key] || '') !== (initialFormData[key] || ''));
  const qualityMeta = QUALITY_STATUS_META[qualityStatus as keyof typeof QUALITY_STATUS_META] || QUALITY_STATUS_META.pending;
  const previewCourse: CourseLivePreviewData = {
    name: formData.name || course.course_name,
    institution_name: course.institution_name,
    price_pen: formData.price_pen || null,
    price_status: formData.price_status || 'consultar',
    mode: formData.mode || '',
    duration: formData.duration || '',
    description_long: formData.description_long || '',
    syllabus: formData.syllabus || '',
    target_audience: formData.target_audience || '',
    requirements: formData.requirements || '',
    certification: formData.certification || '',
    benefits: formData.benefits || '',
    objectives: formData.objectives || '',
    start_date_text: formData.start_date_text || '',
    category: course.category,
    course_type: course.course_type,
    expected_monthly_salary: course.expected_monthly_salary,
    roi_months: course.roi_months,
    seniority_level: course.seniority_level,
  };

  const renderField = (field: FieldDefinition, readOnly = false) => {
    const copy = getFieldCopy(field.field_key);
    const value = formData[field.field_key] || '';
    const inputId = `${readOnly ? 'readonly-' : ''}${field.field_key}`;
    const hasOptions = Boolean(copy.options?.length);

    return (
      <div key={`${readOnly ? 'readonly-' : ''}${field.field_key}`} className={`rounded-2xl border p-4 transition-all ${activePreviewField === field.field_key ? 'border-brand-mint/50 bg-brand-mint/5 shadow-[0_0_0_4px_rgba(16,185,129,0.08)]' : 'border-slate-100 bg-white'}`}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <Label htmlFor={inputId} className="text-sm font-bold text-slate-800">{copy.label}{field.is_required_for_publish && <span className="ml-1 text-rose-600" aria-label="requerido">*</span>}</Label>
            {field.is_required_for_publish && <span className="mt-1 block text-[10px] font-bold uppercase tracking-wider text-rose-600">Requerido para publicar</span>}
          </div>
          {!readOnly && (
            <button type="button" onClick={() => jumpToPreview(field.field_key)} className="inline-flex shrink-0 items-center gap-1 rounded-full border border-brand-blue/20 bg-brand-blue/5 px-2.5 py-1 text-[10px] font-bold text-brand-blue transition hover:bg-brand-blue/10" aria-controls={`preview-impact-${field.field_key}`}>
              <Eye className="size-3" aria-hidden="true" /> Ver impacto
            </button>
          )}
        </div>
        <div className="mt-3">
          {hasOptions && !readOnly ? (
            <Select value={value || '__empty__'} onValueChange={(next) => updateField(field.field_key, next === '__empty__' ? '' : next)}>
              <SelectTrigger id={inputId} onFocus={() => setActivePreviewField(field.field_key)}><SelectValue placeholder={copy.placeholder} /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__empty__">Sin definir</SelectItem>
                {copy.options?.map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}
              </SelectContent>
            </Select>
          ) : copy.multiline && !readOnly ? (
            <textarea
              id={inputId}
              name={field.field_key}
              value={value}
              onFocus={() => setActivePreviewField(field.field_key)}
              onChange={(event) => updateField(field.field_key, event.target.value)}
              placeholder={copy.placeholder}
              rows={field.field_key === 'description_long' ? 6 : 4}
              className="flex min-h-24 w-full resize-y rounded-xl border border-input bg-background px-3 py-2.5 text-sm leading-6 outline-none transition placeholder:text-muted-foreground focus-visible:border-brand-blue focus-visible:ring-2 focus-visible:ring-brand-blue/20"
            />
          ) : (
            <Input
              id={inputId}
              name={field.field_key}
              type={field.field_key === 'price_pen' ? 'number' : 'text'}
              step={field.field_key === 'price_pen' ? '0.01' : undefined}
              inputMode={field.field_key === 'price_pen' ? 'decimal' : undefined}
              value={value}
              onFocus={() => setActivePreviewField(field.field_key)}
              onChange={(event) => updateField(field.field_key, event.target.value)}
              placeholder={copy.placeholder}
              disabled={readOnly}
              readOnly={readOnly}
              className={readOnly ? 'bg-slate-100 text-slate-500' : ''}
            />
          )}
        </div>
        <p className="mt-2 text-xs leading-5 text-slate-500">{copy.help}</p>
        <p className="mt-2 flex items-start gap-1.5 text-[11px] font-semibold leading-5 text-brand-blue"><ArrowDown className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />Impacto: {copy.impact}</p>
        {readOnly && <p className="mt-2 text-[11px] font-semibold text-slate-400">Solo lectura para este rol.</p>}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-brand-gray px-4 py-6 sm:px-6 sm:py-8">
      <main className="mx-auto max-w-7xl space-y-6">
        <div className="relative overflow-hidden rounded-[2rem] bg-brand-slate p-6 text-white shadow-elevated sm:p-8">
          <div className="pointer-events-none absolute -right-20 -top-24 size-64 rounded-full bg-brand-blue/30 blur-3xl" />
          <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <button type="button" onClick={() => router.push('/admin/')} className="mb-5 inline-flex items-center gap-2 text-xs font-bold text-slate-300 transition hover:text-white"><ArrowLeft className="size-4" /> Volver a la cola</button>
              <p className="text-[10px] font-black uppercase tracking-[0.24em] text-brand-mint">Editor editorial</p>
              <h1 className="mt-3 max-w-3xl text-3xl font-black tracking-tight sm:text-4xl">{course.course_name}</h1>
              <p className="mt-2 text-sm text-slate-300">{course.institution_name}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge kind="editorial" value={course.editorial_status} />
              <StatusBadge kind="quality" value={qualityStatus} />
            </div>
          </div>
        </div>

        {mfaRequired && <MfaRequiredCard onVerified={() => void loadCourse()} />}

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(250px,0.32fr)]">
          <Card className="border-slate-200/80 bg-white p-5 shadow-card sm:p-6">
            <div className="flex items-start gap-3">
              <div className="rounded-xl bg-brand-blue/10 p-2.5 text-brand-blue"><ShieldCheck className="size-5" aria-hidden="true" /></div>
              <div><h2 className="font-bold text-slate-900">Identidad del catálogo</h2><p className="mt-1 text-xs leading-5 text-slate-500">La institución se selecciona desde la cola y no se modifica desde este editor.</p></div>
            </div>
            <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3"><p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Institución</p><p className="mt-1 text-sm font-bold text-slate-800">{course.institution_name}</p></div>
          </Card>
          <Card className="border-slate-200/80 bg-white p-5 shadow-card sm:p-6">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-brand-blue">Sesión editorial</p>
            <p className="mt-2 text-2xl font-black text-slate-900">v{course.version}</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">Control de versión activo para evitar sobrescribir cambios de otra persona.</p>
          </Card>
        </div>

        {!isAdmin && readOnlyFields.length > 0 && <p className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800" role="note">Solo puedes editar campos que el sistema marcó como faltantes.</p>}

        <Card className="border-slate-200/80 bg-white p-5 shadow-card sm:p-7">
          <div className="mb-6 flex flex-col gap-3 border-b border-slate-100 pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div><p className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-blue">Contenido público</p><h2 className="mt-2 text-2xl font-black tracking-tight text-brand-slate">Edita con contexto</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Cada campo explica su propósito y señala exactamente qué bloque cambiará en la previsualización.</p></div>
            {hasDraftChanges && <span className="inline-flex items-center gap-2 self-start rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-800"><span className="size-1.5 rounded-full bg-amber-500" /> Cambios sin guardar</span>}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {editableFields.map((field) => renderField(field))}
            {readOnlyFields.map((field) => renderField(field, true))}
          </div>

          {conflict && <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">El registro cambió. Recarga antes de guardar otra vez.</div>}
          {error && <div className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700" role="alert">{error}</div>}
          {success && <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700" role="status">{success}</div>}

          <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-5">
             <Button className="bg-brand-blue text-white shadow-lg shadow-brand-blue/20 hover:bg-brand-blue/90" onClick={() => void handleSave()} disabled={saving || conflict || mfaRequired}><Save className="size-4" /> {saving ? 'Guardando...' : isAdmin ? 'Guardar cambios' : 'Actualizar información'}</Button>
              {isAdmin && (
                <>
                  {course.editorial_status === 'published'
                    ? <Button variant="outline" className="border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100" onClick={() => void updatePublication('admin_unpublish_course')} disabled={saving || mfaRequired}><ArrowDown className="size-4" /> Despublicar</Button>
                    : <Button className="bg-emerald-600 text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-700" onClick={() => void updatePublication('admin_publish_course')} disabled={saving || mfaRequired}><Send className="size-4" /> Publicar</Button>}
                  <Button variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100" onClick={() => void updateAdminStatus('admin_archive_course')} disabled={saving || mfaRequired || course.editorial_status === 'archived'}><Archive className="size-4" /> Archivar</Button>
                  <div className={`rounded-xl border p-1 ${qualityMeta.className}`}>
                    <Select value={qualityStatus} onValueChange={setQualityStatus} disabled={saving || mfaRequired}>
                      <SelectTrigger aria-label="Estado de calidad" className="h-8 min-w-36 border-0 bg-transparent text-xs font-bold shadow-none focus:ring-0"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {Object.entries(QUALITY_STATUS_META).map(([value, meta]) => <SelectItem key={value} value={value}>{meta.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button variant="outline" className="border-brand-blue/20 bg-brand-blue/5 text-brand-blue hover:bg-brand-blue/10" onClick={() => void updateAdminStatus('admin_update_quality_status', qualityStatus)} disabled={saving || mfaRequired || qualityStatus === course.quality_status}><CheckCircle2 className="size-4" /> Actualizar calidad</Button>
                </>
              )}
              {conflict && <Button variant="outline" onClick={() => void loadCourse()}>Recargar</Button>}
             <Button variant="outline" className="border-slate-200 text-slate-600" onClick={() => router.push('/admin/')}><ArrowLeft className="size-4" /> Volver</Button>
          </div>
        </Card>

        <Card className="border-slate-200/80 bg-white p-5 shadow-card sm:p-7">
          <div className="mb-5 flex items-center gap-3"><div className="rounded-xl bg-brand-mint/10 p-2.5 text-emerald-700"><Info className="size-5" /></div><div><h2 className="text-xl font-black text-brand-slate">Qué hace cada acción</h2><p className="mt-1 text-xs text-slate-500">Las acciones se ejecutan con tu rol, control de versión, MFA y auditoría.</p></div></div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4"><p className="font-bold text-blue-900">Guardar cambios</p><p className="mt-1 text-xs leading-5 text-blue-800/80">Guarda el contenido editorial. No publica por sí solo.</p></div>
            <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4"><p className="font-bold text-emerald-900">Publicar</p><p className="mt-1 text-xs leading-5 text-emerald-800/80">Hace visible el curso cuando calidad y campos requeridos están completos.</p></div>
            <div className="rounded-2xl border border-rose-100 bg-rose-50 p-4"><p className="font-bold text-rose-900">Archivar</p><p className="mt-1 text-xs leading-5 text-rose-800/80">Retira el curso del flujo editorial activo y deja trazabilidad.</p></div>
            <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4"><p className="font-bold text-amber-900">Calidad</p><p className="mt-1 text-xs leading-5 text-amber-800/80">Pendiente, completo o bloqueado explica si el curso puede avanzar.</p></div>
          </div>
        </Card>

        <CourseLivePreview course={previewCourse} activeField={activePreviewField} />
      </main>
    </div>
  );
}

export default function AdminEditPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-slate-50"><p className="text-sm text-slate-600">Cargando...</p></div>}>
      <AdminCourseEditor />
    </Suspense>
  );
}
