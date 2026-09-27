'use client';

import { useState } from 'react';
import CoursePublicRenderer, { type CoursePublicTab, type PublicCourse } from '@/components/courses/CoursePublicRenderer';

export type CourseLivePreviewData = Omit<PublicCourse, 'id' | 'slug' | 'url'>;

const REQUIREMENT_FIELDS = new Set(['target_audience', 'requirements']);

export default function CourseLivePreview({ course, activeField }: { course: CourseLivePreviewData; activeField?: string | null }) {
  const [manualTab, setManualTab] = useState<{ field: string | null; tab: CoursePublicTab } | null>(null);
  const activeTab: CoursePublicTab = manualTab?.field === (activeField || null)
    ? manualTab.tab
    : activeField && REQUIREMENT_FIELDS.has(activeField)
      ? 'requisitos'
      : 'info';

  const previewCourse: PublicCourse = {
    id: 'editorial-preview',
    slug: 'editorial-preview',
    url: '',
    ...course,
  };

  return (
    <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-elevated">
      <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-50/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.24em] text-brand-blue">Vista previa pública</p>
          <p className="mt-1 text-xs text-slate-500">La misma composición visual del detalle público, con los cambios todavía sin guardar.</p>
        </div>
        <span className="inline-flex items-center gap-2 self-start rounded-full border border-brand-mint/30 bg-brand-mint/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-wider text-emerald-700 sm:self-auto">
          <span className="size-1.5 animate-pulse rounded-full bg-brand-mint" /> Actualización en vivo
        </span>
      </div>
      <div className="p-6 sm:p-8 lg:p-10">
        <CoursePublicRenderer
          course={previewCourse}
          activeTab={activeTab}
          onActiveTabChange={(tab) => setManualTab({ field: activeField || null, tab })}
          activeField={activeField}
          isPreview
        />
      </div>
    </div>
  );
}
