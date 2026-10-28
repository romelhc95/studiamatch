'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';
import { Archive, ArrowDown, ArrowLeft, CheckCircle2, Clock3, Eye, ExternalLink, History, Info, RotateCcw, Save, Send, ShieldCheck } from 'lucide-react';
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
  manual_overrides: Record<string, string | null>;
  current_values: Record<string, string | number | null>;
  pipeline_values: Record<string, string | number | null>;
  published_values: Record<string, string | number | null> | null;
  has_unpublished_changes: boolean;
  is_publicly_visible: boolean;
  public_visibility_reason: string | null;
  field_sources: Record<string, string>;
  field_timestamps: Record<string, string>;
  missing_fields: string[];
  is_sponsored: boolean;
  lead_cta_enabled: boolean;
  published_at: string | null;
  source_url: string;
  availability_status: 'available' | 'unavailable' | 'unknown';
  computed_availability_status: 'available' | 'unavailable' | 'unknown';
  availability_override_status: 'available' | 'unavailable' | null;
  availability_evidence_url: string | null;
  availability_observed_at: string | null;
  availability_valid_until: string | null;
  availability_override_active: boolean;
  is_active: boolean;
  is_verified: boolean;
  production_enabled: boolean;
  publication_source_gates: boolean;
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

interface AuditCursor {
  created_at: string;
  id: string;
}

interface AuditEvent {
  id: string;
  created_at: string;
  action: string;
  actor_label: string;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  reason: string | null;
}

interface AuditPageRow {
  events: AuditEvent[];
  page_info: { hasNextPage: boolean; endCursor: AuditCursor | null };
  error: string | null;
}

function toDateTimeLocal(value: string | null | undefined): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

function safeExternalUrl(value: string | null | undefined, requireHttps = false): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    if (requireHttps ? url.protocol !== 'https:' : !['https:', 'http:'].includes(url.protocol)) return null;
    return url.toString();
  } catch {
    return null;
  }
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function auditValue(value: unknown): string {
  if (value === null || value === undefined) return 'Sin dato';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  const serialized = JSON.stringify(value) ?? '—';
  return serialized.length > 500 ? `${serialized.slice(0, 497)}…` : serialized;
}

function auditChanges(event: AuditEvent): Array<{ field: string; before: unknown; after: unknown }> {
  const before = asRecord(event.old_values?.editorial_fields) || asRecord(event.old_values?.manual_overrides) || event.old_values || {};
  const after = asRecord(event.new_values?.editorial_fields) || asRecord(event.new_values?.manual_overrides) || event.new_values || {};
  return [...new Set([...Object.keys(before), ...Object.keys(after)])]
    .filter((key) => key !== 'version' && JSON.stringify(before[key]) !== JSON.stringify(after[key]))
    .map((field) => ({ field, before: before[field], after: after[field] }));
}

const AUDIT_ACTION_LABELS: Record<string, string> = {
  update: 'Edición editorial',
  publish: 'Publicación',
  unpublish: 'Despublicación',
  archive: 'Archivo',
  update_quality_status: 'Actualización de calidad',
  quality_recomputed: 'Revisión automática de calidad',
  availability_override: 'Verificación de disponibilidad',
};

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
  const [resetOverrideFields, setResetOverrideFields] = useState<string[]>([]);
  const [editReason, setEditReason] = useState('');
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditCursor, setAuditCursor] = useState<AuditCursor | null>(null);
  const [auditHasNext, setAuditHasNext] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [availabilityChoice, setAvailabilityChoice] = useState<'available' | 'unavailable'>('available');
  const [availabilityEvidenceUrl, setAvailabilityEvidenceUrl] = useState('');
  const [availabilityObservedAt, setAvailabilityObservedAt] = useState('');
  const [availabilityValidUntil, setAvailabilityValidUntil] = useState('');
  const [availabilityReason, setAvailabilityReason] = useState('');

  const isAdmin = role === 'admin';

  const loadAuditPage = useCallback(async (cursor: AuditCursor | null = null, append = false) => {
    setAuditLoading(true);
    setAuditError(null);
    try {
      const rows = (await adminRpc('admin_get_course_audit', {
        p_course_id: courseId,
        p_first: 20,
        p_after_created_at: cursor?.created_at ?? null,
        p_after_id: cursor?.id ?? null,
      })) as AuditPageRow[];
      const page = rows[0];
      if (!page || page.error) throw new Error(page?.error || 'No se pudo cargar el historial.');
      setAuditEvents((current) => append ? [...current, ...(page.events || [])] : (page.events || []));
      setAuditCursor(page.page_info?.endCursor || null);
      setAuditHasNext(page.page_info?.hasNextPage === true);
    } catch (reason) {
      setAuditError(reason instanceof Error ? reason.message : 'No se pudo cargar el historial.');
    } finally {
      setAuditLoading(false);
    }
  }, [courseId]);

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
        const effectiveValue = detail.course.current_values?.[field.field_key] ?? field.current_value;
        initial[field.field_key] = override !== undefined && override !== null ? String(override) : String(effectiveValue ?? '');
      }
      setFormData(initial);
      setInitialFormData(initial);
      setResetOverrideFields([]);
      setEditReason('');
      setAvailabilityChoice(detail.course.availability_override_status || 'available');
      setAvailabilityEvidenceUrl(detail.course.availability_evidence_url || '');
      setAvailabilityObservedAt(toDateTimeLocal(detail.course.availability_observed_at) || toDateTimeLocal(new Date().toISOString()));
      setAvailabilityValidUntil(toDateTimeLocal(detail.course.availability_valid_until));
      setAvailabilityReason('');
      setActivePreviewField(null);
      setConflict(false);
      if (currentRole === 'admin') {
        await loadAuditPage(null, false);
      } else {
        setAuditEvents([]);
      }
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al cargar el curso.');
    } finally {
      setLoading(false);
    }
  }, [courseId, loadAuditPage]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadCourse(), 0);
    return () => window.clearTimeout(timeout);
  }, [loadCourse]);

  const handleSave = async () => {
    if (!course) return;
    if (editReason.trim().length < 8) {
      setError('Explica el motivo del cambio (mínimo 8 caracteres) para dejarlo en la auditoría.');
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    setConflict(false);
    try {
      const allowedKeys = fieldDefinitions
        .filter((field) => field.is_editable !== false)
        .map((field) => field.field_key);
      const payload: Record<string, string | null> = {};
      for (const key of allowedKeys) {
        if (resetOverrideFields.includes(key)) {
          payload[key] = null;
        } else if (key in formData && (formData[key] || '') !== (initialFormData[key] || '')) {
          payload[key] = formData[key];
        }
      }
      if (Object.keys(payload).length === 0) {
        setSuccess('No hay cambios editoriales para guardar.');
        return;
      }
      const rows = (await adminRpc('admin_update_course', {
        p_course_id: course.course_id,
        p_manual_overrides: payload,
        p_version: course.version,
        p_reason: editReason.trim(),
      })) as UpdateRow[];
      const result = rows[0];
      if (!result || !result.success) {
        if (result?.error?.startsWith('Version conflict')) setConflict(true);
        throw new Error(result?.error || 'Error al guardar.');
      }
      await loadCourse();
      setEditReason('');
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

  const saveAvailabilityEvidence = async (clearOverride = false) => {
    if (!course || role !== 'admin') return;
    if (clearOverride && !window.confirm('¿Retirar la verificación manual? La disponibilidad volverá al valor calculado por el pipeline.')) return;
    if (!clearOverride) {
      if (!availabilityEvidenceUrl.trim().startsWith('https://')) {
        setError('La evidencia debe ser un enlace HTTPS del sitio oficial del curso.');
        return;
      }
      if (!availabilityObservedAt || !availabilityValidUntil || new Date(availabilityValidUntil) <= new Date()) {
        setError('Registra cuándo verificaste la fuente y hasta cuándo es válida la evidencia.');
        return;
      }
      const observedAt = new Date(availabilityObservedAt);
      const validUntil = new Date(availabilityValidUntil);
      const maxValidUntil = new Date(observedAt);
      maxValidUntil.setUTCDate(maxValidUntil.getUTCDate() + 90);
      if (!Number.isFinite(observedAt.getTime()) || !Number.isFinite(validUntil.getTime()) || validUntil > maxValidUntil) {
        setError('La evidencia puede tener una vigencia máxima global de 90 días calendario desde la verificación.');
        return;
      }
      if (availabilityReason.trim().length < 8) {
        setError('Explica la verificación (mínimo 8 caracteres) para dejarla en la auditoría.');
        return;
      }
    } else if (availabilityReason.trim().length < 8) {
      setError('Explica por qué retiras la verificación (mínimo 8 caracteres).');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const rows = (await adminRpc('admin_set_course_availability', {
        p_course_id: course.course_id,
        p_availability_status: clearOverride ? null : availabilityChoice,
        p_evidence_url: clearOverride ? null : availabilityEvidenceUrl.trim(),
        p_observed_at: clearOverride ? null : new Date(availabilityObservedAt).toISOString(),
        p_valid_until: clearOverride ? null : new Date(availabilityValidUntil).toISOString(),
        p_version: course.version,
        p_reason: availabilityReason.trim(),
      })) as UpdateRow[];
      const result = rows[0];
      if (!result || !result.success) {
        if (result?.error?.startsWith('Version conflict')) setConflict(true);
        throw new Error(result?.error || 'No se pudo actualizar la disponibilidad.');
      }
      await loadCourse();
      setAvailabilityReason('');
      setSuccess(clearOverride ? 'Verificación manual retirada.' : 'Evidencia de disponibilidad registrada.');
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al actualizar la disponibilidad.');
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
      await loadCourse();
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
      await loadAuditPage(null, false);
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
    setResetOverrideFields((current) => current.filter((key) => key !== fieldKey));
    setActivePreviewField(fieldKey);
  };

  const resetFieldToPipeline = (fieldKey: string) => {
    const pipelineValue = course?.pipeline_values?.[fieldKey];
    setFormData((current) => ({ ...current, [fieldKey]: String(pipelineValue ?? '') }));
    setResetOverrideFields((current) => current.includes(fieldKey) ? current : [...current, fieldKey]);
    setActivePreviewField(fieldKey);
  };

  const jumpToPreview = (fieldKey: string) => {
    setActivePreviewField(fieldKey);
    // Scrolling is deliberately restricted to this explicit user action.
    // Editing/focusing a field may highlight the preview, but never moves the
    // editor away from the form on its own.
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        document.getElementById(`preview-impact-${fieldKey}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    });
  };

  if (loading) return <Card className="p-12 text-center text-sm text-slate-600">Cargando curso...</Card>;
  if (mfaRequired && !course) return <div className="min-h-screen bg-slate-50 px-6 py-8"><main className="mx-auto max-w-5xl"><MfaRequiredCard onVerified={() => void loadCourse()} /></main></div>;
  if (!course) return <Card className="p-8 text-center text-sm text-red-600">{error || 'Curso no encontrado.'}</Card>;

  const editableFields = fieldDefinitions.filter((field) => isAdmin || field.is_editable !== false);
  const readOnlyFields = fieldDefinitions.filter((field) => !isAdmin && field.is_editable === false);
  const hasDraftChanges = resetOverrideFields.length > 0 || Object.keys(initialFormData).some((key) => (formData[key] || '') !== (initialFormData[key] || ''));
  const qualityMeta = QUALITY_STATUS_META[qualityStatus as keyof typeof QUALITY_STATUS_META] || QUALITY_STATUS_META.pending;
  const canPublish = course.quality_status === 'complete'
    && course.missing_fields.length === 0
    && course.is_active !== false
    && course.is_verified !== false
    && course.production_enabled !== false
    && course.publication_source_gates !== false;
  const officialCourseUrl = safeExternalUrl(course.source_url);
  const availabilityProofUrl = safeExternalUrl(course.availability_evidence_url, true);
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
  const publishedPreviewCourse: CourseLivePreviewData | null = course.editorial_status === 'published' && course.published_values
    ? {
      name: String(course.published_values.name ?? ''),
      institution_name: course.institution_name,
      price_pen: course.published_values.price_pen ?? null,
      price_status: String(course.published_values.price_status ?? 'consultar'),
      mode: String(course.published_values.mode ?? ''),
      duration: String(course.published_values.duration ?? ''),
      description_long: String(course.published_values.description_long ?? ''),
      syllabus: String(course.published_values.syllabus ?? ''),
      target_audience: String(course.published_values.target_audience ?? ''),
      requirements: String(course.published_values.requirements ?? ''),
      certification: String(course.published_values.certification ?? ''),
      benefits: String(course.published_values.benefits ?? ''),
      objectives: String(course.published_values.objectives ?? ''),
      start_date_text: String(course.published_values.start_date_text ?? ''),
      category: course.category,
      course_type: course.course_type,
      expected_monthly_salary: course.expected_monthly_salary,
      roi_months: course.roi_months,
      seniority_level: course.seniority_level,
    }
    : null;

  const renderField = (field: FieldDefinition, readOnly = false) => {
    const copy = getFieldCopy(field.field_key);
    const value = formData[field.field_key] || '';
    const inputId = `${readOnly ? 'readonly-' : ''}${field.field_key}`;
    const hasOptions = Boolean(copy.options?.length);
    const hasManualOverride = course.manual_overrides?.[field.field_key] !== undefined && course.manual_overrides?.[field.field_key] !== null;
    const pipelineValue = course.pipeline_values?.[field.field_key];
    const currentEffectiveValue = course.current_values?.[field.field_key] ?? field.current_value;
    const differsFromPipeline = hasManualOverride
      && String(currentEffectiveValue ?? '') !== String(pipelineValue ?? '');
    const isMissing = course.missing_fields.includes(field.field_key);
    const fieldSource = hasManualOverride ? 'manual_override' : course.field_sources?.[field.field_key] || 'pipeline';
    const sourceLabel = fieldSource === 'manual_override'
      ? 'Corrección manual'
      : fieldSource === 'display_default'
        ? 'Valor de presentación'
        : 'Pipeline / fuente institucional';

    return (
      <div key={`${readOnly ? 'readonly-' : ''}${field.field_key}`} className={`rounded-2xl border p-4 transition-all ${activePreviewField === field.field_key ? 'border-brand-mint/50 bg-brand-mint/5 shadow-[0_0_0_4px_rgba(16,185,129,0.08)]' : 'border-slate-100 bg-white'}`}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <Label htmlFor={inputId} className="text-sm font-bold text-slate-800">{copy.label}{field.is_required_for_publish && <span className="ml-1 text-rose-600" aria-label="requerido">*</span>}</Label>
            {field.is_required_for_publish && <span className="mt-1 block text-[10px] font-bold uppercase tracking-wider text-rose-600">Requerido para publicar</span>}
            {isMissing && <span className="mt-1 inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-800">Faltante</span>}
            {differsFromPipeline && <span className="mt-1 inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-blue-800">Difiere del pipeline</span>}
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
        <p className="mt-2 text-[11px] font-semibold text-slate-500">
          Origen actual: <span className="text-slate-700">{sourceLabel}</span>
          {course.field_timestamps?.[field.field_key] && (
            <span>
              {' · '}
              {hasManualOverride ? 'Fecha del dato base del pipeline:' : 'Fecha del dato de origen:'}{' '}
              {new Date(course.field_timestamps[field.field_key]).toLocaleDateString('es-PE')}
            </span>
          )}
        </p>
        {hasManualOverride && <p className="mt-1 break-words text-[11px] leading-5 text-slate-500">Valor base del pipeline: <span className="font-semibold text-slate-700">{String(pipelineValue ?? 'Sin dato')}</span></p>}
        {isAdmin && hasManualOverride && !readOnly && (
          <button type="button" onClick={() => resetFieldToPipeline(field.field_key)} className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-bold text-brand-blue hover:underline">
            <RotateCcw className="size-3" aria-hidden="true" /> Restaurar valor del pipeline
          </button>
        )}
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
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge kind="editorial" value={course.editorial_status} />
              <StatusBadge kind="quality" value={qualityStatus} />
              <span data-testid="editorial-version" aria-label={`Versión editorial ${course.version}`} className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-2.5 py-1 text-[11px] font-bold tabular-nums text-white">v{course.version}</span>
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
        </div>

        <Card className="border-slate-200/80 bg-white p-5 shadow-card sm:p-7">
          <div className="mb-6 flex flex-col gap-3 border-b border-slate-100 pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div><p className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-blue">Contenido público</p><h2 className="mt-2 text-2xl font-black tracking-tight text-brand-slate">Edita con contexto</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Puedes corregir cualquiera de los 13 campos editoriales permitidos. Guardar crea un borrador; Admin publica su instantánea para el catálogo.</p></div>
            {hasDraftChanges && <span className="inline-flex items-center gap-2 self-start rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-800"><span className="size-1.5 rounded-full bg-amber-500" /> Cambios sin guardar</span>}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {editableFields.map((field) => renderField(field))}
            {readOnlyFields.map((field) => renderField(field, true))}
          </div>

          {hasDraftChanges && (
            <div className="mt-6 rounded-2xl border border-brand-blue/15 bg-brand-blue/5 p-4">
              <Label htmlFor="editorial-reason" className="text-sm font-bold text-slate-800">Motivo de la corrección</Label>
              <Input id="editorial-reason" value={editReason} onChange={(event) => setEditReason(event.target.value)} maxLength={1000} placeholder="Ej.: La fuente oficial indica modalidad remota" className="mt-2 bg-white" />
              <p className="mt-2 text-xs text-slate-500">Se guardará con el actor y los valores anteriores y nuevos. Mínimo 8 caracteres.</p>
            </div>
          )}

          {conflict && <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">El registro cambió. Recarga antes de guardar otra vez.</div>}
          {error && <div className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700" role="alert">{error}</div>}
          {success && <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700" role="status">{success}</div>}

          <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-5">
              <Button className="bg-brand-blue text-white shadow-lg shadow-brand-blue/20 hover:bg-brand-blue/90" onClick={() => void handleSave()} disabled={saving || conflict || mfaRequired || !hasDraftChanges}><Save className="size-4" /> {saving ? 'Guardando...' : isAdmin ? 'Guardar cambios' : 'Actualizar información'}</Button>
              {isAdmin && (
                <>
                  {course.editorial_status === 'published' ? (
                    <>
                      {course.has_unpublished_changes && <Button className="bg-emerald-600 text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-700" onClick={() => void updatePublication('admin_publish_course')} disabled={saving || mfaRequired || !canPublish || hasDraftChanges}><Send className="size-4" /> Publicar cambios</Button>}
                      <Button variant="outline" className="border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100" onClick={() => void updatePublication('admin_unpublish_course')} disabled={saving || mfaRequired}><ArrowDown className="size-4" /> Despublicar</Button>
                    </>
                  ) : <Button className="bg-emerald-600 text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-700" onClick={() => void updatePublication('admin_publish_course')} disabled={saving || mfaRequired || !canPublish || hasDraftChanges}><Send className="size-4" /> Publicar</Button>}
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
          {isAdmin && !canPublish && course.editorial_status !== 'published' && (
            <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900" role="status">
              Publicación bloqueada: confirma calidad completa, campos sin faltantes, curso activo/verificado e institución habilitada. La disponibilidad de inscripción se registra por separado.
            </p>
          )}
        </Card>

        <Card className="border-slate-200/80 bg-white p-5 shadow-card sm:p-7">
          <div className="flex flex-col gap-4 border-b border-slate-100 pb-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="flex items-center gap-2"><Clock3 className="size-5 text-brand-blue" aria-hidden="true" /><h2 className="text-xl font-black text-brand-slate">Disponibilidad y fuente oficial</h2></div>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">La disponibilidad de inscripción se mantiene separada del contenido editorial y de la existencia del curso. La evidencia HTTPS y su vencimiento solo describen una comprobación de inscripción; al vencer, el estado vuelve a desconocido o al valor calculado, sin retirar la publicación ni borrar correcciones.</p>
              {officialCourseUrl && <a href={officialCourseUrl} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-1.5 text-sm font-bold text-brand-blue hover:underline">Abrir página oficial del curso <ExternalLink className="size-3.5" aria-hidden="true" /></a>}
            </div>
            <span className={`inline-flex shrink-0 rounded-full px-3 py-1.5 text-xs font-black uppercase tracking-wide ${course.availability_status === 'available' ? 'bg-emerald-50 text-emerald-700' : course.availability_status === 'unavailable' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-800'}`}>
              {course.availability_status === 'available' ? 'Disponible' : course.availability_status === 'unavailable' ? 'No disponible' : 'Sin confirmar'}
            </span>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-3"><p className="text-[10px] font-black uppercase tracking-wider text-slate-400">Estado del pipeline</p><p className="mt-1 text-sm font-bold text-slate-800">{course.computed_availability_status || 'unknown'}</p></div>
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-3"><p className="text-[10px] font-black uppercase tracking-wider text-slate-400">Overrides editoriales</p><p className="mt-1 text-sm font-bold text-slate-800">{course.manual_overrides ? Object.keys(course.manual_overrides).filter((key) => course.manual_overrides[key] !== null).length : 0} campos manuales</p></div>
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-3"><p className="text-[10px] font-black uppercase tracking-wider text-slate-400">Gates del catálogo</p><p className="mt-1 text-sm font-bold text-slate-800">{course.is_active === false ? 'Inactivo' : 'Activo'} · {course.is_verified === false ? 'No verificado' : 'Verificado'} · {course.production_enabled === false ? 'Institución deshabilitada' : 'Institución habilitada'}</p></div>
          </div>
          {course.availability_override_status && (
            <p className="mt-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-xs leading-5 text-blue-900">
              Verificación manual: <strong>{course.availability_override_status}</strong>{course.availability_override_active ? ' vigente' : ' vencida'} · evidencia {availabilityProofUrl ? <a className="break-all font-semibold underline" href={availabilityProofUrl} target="_blank" rel="noopener noreferrer">{course.availability_evidence_url}</a> : 'no disponible'} · verificada {course.availability_observed_at ? new Date(course.availability_observed_at).toLocaleString('es-PE') : 'sin fecha'} · válida hasta {course.availability_valid_until ? new Date(course.availability_valid_until).toLocaleString('es-PE') : 'sin fecha'}.
            </p>
          )}
          {isAdmin && (
            <div className="mt-6 rounded-2xl border border-slate-100 p-4 sm:p-5">
              <h3 className="font-bold text-slate-900">Registrar comprobación respaldada</h3>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="availability-decision">Resultado verificado</Label>
                  <Select value={availabilityChoice} onValueChange={(value) => setAvailabilityChoice(value as 'available' | 'unavailable')}>
                    <SelectTrigger id="availability-decision" className="mt-2"><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="available">Disponible</SelectItem><SelectItem value="unavailable">No disponible</SelectItem></SelectContent>
                  </Select>
                </div>
                <div><Label htmlFor="availability-evidence">Enlace de evidencia oficial</Label><Input id="availability-evidence" type="url" value={availabilityEvidenceUrl} onChange={(event) => setAvailabilityEvidenceUrl(event.target.value)} placeholder="https://institucion.edu/curso" className="mt-2" /></div>
                <div><Label htmlFor="availability-observed">Verificado el</Label><Input id="availability-observed" type="datetime-local" value={availabilityObservedAt} onChange={(event) => setAvailabilityObservedAt(event.target.value)} className="mt-2" /></div>
                <div><Label htmlFor="availability-valid-until">Evidencia válida hasta</Label><Input id="availability-valid-until" type="datetime-local" value={availabilityValidUntil} onChange={(event) => setAvailabilityValidUntil(event.target.value)} className="mt-2" /><p className="mt-1 text-xs text-slate-500">Máximo global: 90 días calendario desde la verificación.</p></div>
                <div className="md:col-span-2"><Label htmlFor="availability-reason">Nota de verificación</Label><Input id="availability-reason" value={availabilityReason} onChange={(event) => setAvailabilityReason(event.target.value)} maxLength={1000} placeholder="Qué confirma la fuente oficial" className="mt-2" /></div>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <Button onClick={() => void saveAvailabilityEvidence()} disabled={saving || conflict || mfaRequired}><CheckCircle2 className="size-4" /> Guardar verificación</Button>
                {course.availability_override_status && <Button variant="outline" onClick={() => void saveAvailabilityEvidence(true)} disabled={saving || conflict || mfaRequired}><RotateCcw className="size-4" /> Retirar override</Button>}
              </div>
              <p className="mt-3 text-xs leading-5 text-slate-500">No se modifica el estado calculado ni se confirma disponibilidad sin evidencia. Esta comprobación no controla la publicación ni la vigencia del curso en el catálogo.</p>
            </div>
          )}
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

        {isAdmin && (
          <Card className="border-slate-200/80 bg-white p-5 shadow-card sm:p-7">
            <details data-testid="editorial-audit-details" className="group">
              <summary className="flex cursor-pointer list-none flex-col gap-3 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2 sm:flex-row sm:items-center sm:justify-between">
                <span className="min-w-0">
                  <span className="flex items-center gap-2"><History className="size-5 shrink-0 text-brand-blue" aria-hidden="true" /><span className="text-xl font-black text-brand-slate">Historial de auditoría</span><span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold tabular-nums text-slate-600">{auditEvents.length}{auditHasNext ? '+' : ''}</span></span>
                  <span className="mt-2 block text-sm leading-6 text-slate-600">Registro de solo lectura con actor, fecha, motivo y valores modificados. Acceso restringido a Admin con MFA.</span>
                </span>
                <span className="shrink-0 rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 group-open:bg-slate-100">Abrir o cerrar historial</span>
              </summary>
              <div className="mt-5 border-t border-slate-100 pt-5">
                <div className="flex justify-end"><Button variant="outline" onClick={() => void loadAuditPage(null, false)} disabled={auditLoading}><History className="size-4" aria-hidden="true" /> {auditLoading ? 'Actualizando…' : 'Actualizar historial'}</Button></div>
                {auditError && <p className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">{auditError}</p>}
                {!auditError && auditEvents.length === 0 && !auditLoading && <p className="mt-5 rounded-xl bg-slate-50 px-4 py-5 text-sm text-slate-600">Todavía no hay eventos registrados para este curso.</p>}
                <ol className="mt-5 space-y-4">
                  {auditEvents.map((event) => {
                    const changes = auditChanges(event);
                    return (
                      <li key={event.id} className="min-w-0 rounded-2xl border border-slate-100 bg-slate-50/70 p-4 sm:p-5">
                        <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <div className="min-w-0"><h3 className="break-words font-bold text-slate-900">{AUDIT_ACTION_LABELS[event.action] || event.action}</h3><p className="mt-1 break-words text-xs text-slate-600">{event.actor_label || 'Actor no disponible'} · {new Date(event.created_at).toLocaleString('es-PE')}</p></div>
                          {event.reason && <p className="min-w-0 max-w-xl break-words rounded-lg bg-white px-3 py-2 text-xs leading-5 text-slate-700">{event.reason}</p>}
                        </div>
                        {changes.length > 0 && <dl className="mt-4 grid min-w-0 gap-2 sm:grid-cols-2">{changes.map(({ field, before, after }) => <div key={`${event.id}-${field}`} className="min-w-0 rounded-xl border border-slate-100 bg-white p-3"><dt className="break-words text-[10px] font-black uppercase tracking-wider text-slate-500">{field}</dt><dd className="mt-1 break-words text-xs leading-5 text-slate-700"><span className="font-semibold">Antes:</span> {auditValue(before)}</dd><dd className="break-words text-xs leading-5 text-slate-700"><span className="font-semibold">Después:</span> {auditValue(after)}</dd></div>)}</dl>}
                        {changes.length === 0 && <p className="mt-3 text-xs text-slate-500">Evento registrado; no contiene diferencias de campos visibles.</p>}
                      </li>
                    );
                  })}
                </ol>
                {auditHasNext && <div className="mt-5 text-center"><Button variant="outline" onClick={() => void loadAuditPage(auditCursor, true)} disabled={auditLoading}>{auditLoading ? 'Cargando…' : 'Cargar eventos anteriores'}</Button></div>}
              </div>
            </details>
          </Card>
        )}

        <CourseLivePreview
          draftCourse={previewCourse}
          publishedCourse={publishedPreviewCourse}
          activeField={activePreviewField}
          hasUnsavedChanges={hasDraftChanges}
          hasUnpublishedChanges={course.has_unpublished_changes}
          isPubliclyVisible={course.is_publicly_visible}
          visibilityReason={course.public_visibility_reason}
        />
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
