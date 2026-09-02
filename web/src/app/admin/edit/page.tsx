'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { adminRpc, requireActiveAdmin, type AdminRole } from '@/lib/admin-auth';

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

  const loadCourse = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const currentRole = await requireActiveAdmin();
      setRole(currentRole);
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
      setConflict(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Error al cargar el curso.');
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadCourse(), 0);
    return () => window.clearTimeout(timeout);
  }, [loadCourse]);

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
      setSuccess('Cambios guardados correctamente.');
    } catch (reason) {
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
      setError(reason instanceof Error ? reason.message : 'Error al cambiar el estado.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Card className="p-12 text-center text-sm text-slate-600">Cargando curso...</Card>;
  if (!course) return <Card className="p-8 text-center text-sm text-red-600">{error || 'Curso no encontrado.'}</Card>;

  const isAdmin = role === 'admin';
  const editableFields = fieldDefinitions.filter((field) => isAdmin || field.is_editable !== false);
  const readOnlyFields = fieldDefinitions.filter((field) => !isAdmin && field.is_editable === false);

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-8">
      <main className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{course.course_name}</h1>
            <p className="text-sm text-slate-600">{course.institution_name}</p>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline">{course.editorial_status.replace('_', ' ')}</Badge>
            <Badge variant="outline">{course.quality_status.replace('_', ' ')}</Badge>
          </div>
        </div>

        {!isAdmin && readOnlyFields.length > 0 && (
          <p className="text-sm text-slate-500" role="note">
            Solo puedes editar campos con información faltante.
          </p>
        )}

        <Card className="p-6">
          <div className="grid gap-6 md:grid-cols-2">
            {editableFields.map((field) => (
              <div key={field.field_key} className="space-y-2">
                <Label htmlFor={field.field_key}>{field.field_key.replaceAll('_', ' ')}{field.is_required_for_publish ? ' *' : ''}</Label>
                <Input id={field.field_key} value={formData[field.field_key] || ''} onChange={(event) => setFormData((current) => ({ ...current, [field.field_key]: event.target.value }))} />
                <p className="text-xs text-slate-500">{field.description}</p>
              </div>
            ))}
            {readOnlyFields.map((field) => (
              <div key={field.field_key} className="space-y-2 opacity-70">
                <Label htmlFor={`${field.field_key}-ro`}>{field.field_key.replaceAll('_', ' ')}</Label>
                <Input id={`${field.field_key}-ro`} value={formData[field.field_key] || ''} disabled readOnly />
                <p className="text-xs text-slate-400">Solo lectura</p>
              </div>
            ))}
          </div>

          {conflict && <div className="mt-6 rounded-lg bg-amber-50 p-4 text-sm text-amber-800">El registro cambió. Recarga antes de guardar otra vez.</div>}
          {error && <div className="mt-6 rounded-lg bg-red-50 p-4 text-sm text-red-600">{error}</div>}
          {success && <div className="mt-6 rounded-lg bg-green-50 p-4 text-sm text-green-700">{success}</div>}

          <div className="mt-6 flex flex-wrap gap-3 border-t pt-4">
            <Button onClick={() => void handleSave()} disabled={saving || conflict}>{saving ? 'Guardando...' : isAdmin ? 'Guardar cambios' : 'Actualizar información'}</Button>
             {isAdmin && (
               <>
                 {course.editorial_status === 'published'
                   ? <Button variant="outline" onClick={() => void updatePublication('admin_unpublish_course')} disabled={saving}>Despublicar</Button>
                   : <Button onClick={() => void updatePublication('admin_publish_course')} disabled={saving}>Publicar</Button>}
                 <Button variant="outline" onClick={() => void updateAdminStatus('admin_archive_course')} disabled={saving || course.editorial_status === 'archived'}>Archivar</Button>
                 <select aria-label="Estado de calidad" value={qualityStatus} onChange={(event) => setQualityStatus(event.target.value)} disabled={saving} className="h-8 rounded-lg border border-input bg-background px-2 text-sm">
                   <option value="pending">Pendiente</option>
                   <option value="complete">Completo</option>
                   <option value="blocked">Bloqueado</option>
                 </select>
                 <Button variant="outline" onClick={() => void updateAdminStatus('admin_update_quality_status', qualityStatus)} disabled={saving || qualityStatus === course.quality_status}>Actualizar calidad</Button>
               </>
             )}
             {conflict && <Button variant="outline" onClick={() => void loadCourse()}>Recargar</Button>}
            <Button variant="ghost" onClick={() => router.push('/admin/')}>Volver</Button>
          </div>
        </Card>
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
