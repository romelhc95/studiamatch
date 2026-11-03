'use client';

import { useState } from 'react';
import CoursePublicRenderer, { type CoursePublicTab, type PublicCourse } from '@/components/courses/CoursePublicRenderer';

export type CourseLivePreviewData = Omit<PublicCourse, 'id' | 'slug' | 'url'>;

const REQUIREMENT_FIELDS = new Set(['target_audience', 'requirements']);

interface CourseLivePreviewProps {
  draftCourse: CourseLivePreviewData;
  publishedCourse: CourseLivePreviewData | null;
  activeField?: string | null;
  hasUnsavedChanges: boolean;
  hasUnpublishedChanges: boolean;
  isPubliclyVisible: boolean;
  visibilityReason: string | null;
}

export default function CourseLivePreview({
  draftCourse,
  publishedCourse,
  activeField,
  hasUnsavedChanges,
  hasUnpublishedChanges,
  isPubliclyVisible,
  visibilityReason,
}: CourseLivePreviewProps) {
  const [manualTab, setManualTab] = useState<{ field: string | null; tab: CoursePublicTab } | null>(null);
  const [mode, setMode] = useState<'draft' | 'published'>(publishedCourse ? 'published' : 'draft');
  const activeTab: CoursePublicTab = manualTab?.field === (activeField || null)
    ? manualTab.tab
    : activeField && REQUIREMENT_FIELDS.has(activeField)
      ? 'requisitos'
      : 'info';
  const selectedCourse = mode === 'published' ? publishedCourse : draftCourse;
  const previewCourse: PublicCourse | null = selectedCourse
    ? { id: 'editorial-preview', slug: 'editorial-preview', url: '', ...selectedCourse }
    : null;

  return (
    <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-elevated" aria-label="Previsualización editorial">
      <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-50/80 px-5 py-5 sm:px-8 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-[10px] font-black uppercase tracking-[0.24em] text-brand-blue">
            {mode === 'published' ? 'Contenido publicado' : 'Previsualización del borrador'}
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-600">
            {mode === 'published'
              ? 'Instantánea de la última publicación de Admin; no incluye cambios posteriores sin publicar.'
              : hasUnsavedChanges
                ? 'Vista del formulario actual. Estos cambios todavía no están guardados ni publicados.'
                : hasUnpublishedChanges
                  ? 'Borrador guardado con cambios pendientes de una nueva publicación de Admin.'
                  : 'Vista del contenido que se enviaría al publicar el borrador actual.'}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2" role="group" aria-label="Versión del contenido para previsualizar">
          <button
            type="button"
            aria-pressed={mode === 'draft'}
            onClick={() => setMode('draft')}
            className={`rounded-full border px-3 py-2 text-xs font-bold transition ${mode === 'draft' ? 'border-brand-blue bg-brand-blue text-white' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'}`}
          >
            Borrador
          </button>
          <button
            type="button"
            aria-pressed={mode === 'published'}
            disabled={!publishedCourse}
            onClick={() => setMode('published')}
            className={`rounded-full border px-3 py-2 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-50 ${mode === 'published' ? 'border-emerald-700 bg-emerald-700 text-white' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'}`}
          >
            Publicado
          </button>
        </div>
      </div>

      {mode === 'published' && !isPubliclyVisible && (
        <p className="border-b border-amber-200 bg-amber-50 px-5 py-3 text-sm leading-5 text-amber-900 sm:px-8" role="status">
          Este contenido no está visible en el catálogo ahora. {visibilityReason || 'Hay un gate del catálogo pendiente.'}
        </p>
      )}
      {mode === 'published' && hasUnpublishedChanges && (
        <p className="border-b border-blue-100 bg-blue-50 px-5 py-3 text-sm leading-5 text-blue-900 sm:px-8" role="status">
          El borrador actual difiere de esta publicación. Admin debe volver a publicar para que el público reciba esos cambios.
        </p>
      )}
      {previewCourse ? (
        <div className="min-w-0 p-5 sm:p-8 lg:p-10">
          <CoursePublicRenderer
            course={previewCourse}
            activeTab={activeTab}
            onActiveTabChange={(tab) => setManualTab({ field: activeField || null, tab })}
            activeField={mode === 'draft' ? activeField : null}
            isPreview
          />
        </div>
      ) : (
        <div className="m-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm leading-6 text-slate-600 sm:m-8">
          Este curso todavía no tiene una publicación de Admin. El borrador no representa contenido visible al público.
        </div>
      )}
    </section>
  );
}
