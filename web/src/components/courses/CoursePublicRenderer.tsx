"use client";

import { useMemo, type ReactNode } from "react";
import Link from "next/link";
import {
  Award,
  CheckCircle,
  Download,
  GraduationCap,
  Info,
  MapPin,
  ShieldCheck,
  Sprout,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { cleanSlug } from "@/lib/supabase";

export type CoursePublicTab = "info" | "requisitos";

export interface PublicCourse {
  id: string;
  name: string;
  slug: string;
  institution_name: string;
  institution_slug?: string;
  institution_id?: string;
  price_pen?: number | string | null;
  price_status?: string;
  mode?: string;
  address?: string;
  duration?: string;
  url?: string;
  roi_months?: number | null;
  expected_monthly_salary?: number | null;
  category?: string;
  category_id?: string;
  description_long?: string;
  objectives?: string;
  target_audience?: string;
  requirements?: string;
  syllabus?: string;
  course_type?: string;
  brochure_url?: string;
  brochure_text?: string;
  is_active?: boolean;
  start_date_text?: string;
  certification?: string;
  benefits?: string;
  seniority_level?: string;
}

type CompareItem = { id: string; name: string };

interface CoursePublicRendererProps {
  course: PublicCourse;
  activeTab: CoursePublicTab;
  onActiveTabChange?: (tab: CoursePublicTab) => void;
  activeField?: string | null;
  isPreview?: boolean;
  compareList?: CompareItem[];
  onToggleCompare?: () => void;
  relatedCourses?: PublicCourse[];
}

function ImpactBlock({
  field,
  activeField,
  children,
  className,
  activeFields = [],
  anchor = true,
}: {
  field: string;
  activeField?: string | null;
  children: ReactNode;
  className?: string;
  activeFields?: string[];
  anchor?: boolean;
}) {
  const active = activeField === field || activeFields.includes(activeField || "");
  return (
    <div
      id={anchor && active ? `preview-impact-${activeField}` : undefined}
      data-preview-field={field}
      className={cn(
        "rounded-2xl transition-all duration-500",
        active && "bg-brand-mint/10 ring-4 ring-brand-mint/30 shadow-[0_0_0_8px_rgba(16,185,129,0.08)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

function isValidUrl(value: string | undefined) {
  if (!value) return false;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" || parsed.protocol === "http:";
  } catch {
    return false;
  }
}

function formatPrice(course: PublicCourse, roi = false) {
  const amount = Number(course.price_pen);
  const hasPrice = course.price_status !== "consultar" && Number.isFinite(amount) && amount > 0;
  if (!hasPrice) return roi ? "S/ --" : "Consultar";
  return `S/ ${amount.toLocaleString("es-PE")}`;
}

function renderPublicText(text: string | undefined, empty = "Información en proceso de validación.") {
  if (!text?.trim()) return <span className="italic text-slate-400">{empty}</span>;

  const trimmedText = text.trim();
  if (trimmedText.startsWith("{") && trimmedText.endsWith("}")) {
    try {
      const parsed: unknown = JSON.parse(trimmedText);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        const elements: ReactNode[] = [];
        Object.entries(parsed as Record<string, unknown>).forEach(([key, value], index) => {
          const label = key.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
          elements.push(
            <h4 key={`json-heading-${index}`} className="mb-2 mt-4 text-sm font-black uppercase tracking-wider text-brand-blue">
              {label}
            </h4>,
          );
          if (Array.isArray(value)) {
            elements.push(
              <ul key={`json-list-${index}`} className="my-2 space-y-1 pl-2">
                {value.map((item, itemIndex) => (
                  <li key={`json-item-${index}-${itemIndex}`} className="flex items-start gap-2">
                    <span className="mt-1.5 shrink-0 text-brand-mint">•</span>
                    <span>{String(item)}</span>
                  </li>
                ))}
              </ul>,
            );
          } else if (value && typeof value === "object") {
            elements.push(<p key={`json-value-${index}`} className="mb-2 italic">Información estructurada disponible.</p>);
          } else {
            elements.push(<p key={`json-value-${index}`} className="mb-2">{String(value)}</p>);
          }
        });
        return <div className="text-lg text-slate-600 dark:text-slate-400">{elements}</div>;
      }
    } catch {
      // Plain-text fallback below.
    }
  }

  let displayLines: string[];
  let isJsonArrayInput = false;
  if (trimmedText.startsWith("[") && trimmedText.endsWith("]")) {
    try {
      const parsed: unknown = JSON.parse(trimmedText);
      if (Array.isArray(parsed)) {
        displayLines = parsed.map((item) => String(item));
        isJsonArrayInput = true;
      } else {
        displayLines = text.split("\n");
      }
    } catch {
      displayLines = text.split("\n");
    }
  } else {
    displayLines = text.split("\n");
  }

  const lines = displayLines.map((line) => line.trim()).filter(Boolean);
  const elements: ReactNode[] = [];
  let currentList: string[] = [];
  const flushList = () => {
    if (currentList.length === 0) return;
    elements.push(
      <ul key={`list-${elements.length}`} className="my-4 space-y-2 pl-2">
        {currentList.map((item, index) => (
          <li key={`list-item-${index}`} className="flex items-start gap-2">
            <span className="mt-1.5 shrink-0 text-brand-mint">•</span>
            <span>{item.replace(/^[-*•]\s*/, "")}</span>
          </li>
        ))}
      </ul>,
    );
    currentList = [];
  };

  lines.forEach((line, index) => {
    if (/^[-*•]\s+/.test(line) || isJsonArrayInput) {
      currentList.push(line);
    } else {
      flushList();
      elements.push(
        <p key={`paragraph-${index}`} className="mb-4 leading-relaxed last:mb-0">
          {line}
        </p>,
      );
    }
  });
  flushList();

  return <div className="text-lg text-slate-600 dark:text-slate-400">{elements}</div>;
}

function ComparePanel({
  course,
  compareList,
  onToggleCompare,
  isPreview,
}: {
  course: PublicCourse;
  compareList?: CompareItem[];
  onToggleCompare?: () => void;
  isPreview: boolean;
}) {
  const selected = Boolean(compareList?.some((item) => item.id === course.id));
  if (!onToggleCompare && !isPreview) return null;

  return (
    <div className="mt-6">
      <button
        type="button"
        onClick={onToggleCompare}
        disabled={!onToggleCompare}
        className={cn(
          "flex h-12 w-full items-center justify-center gap-2 rounded-xl border text-[12px] font-bold uppercase tracking-wider transition-all",
          selected
            ? "border-brand-blue bg-brand-blue text-white shadow-lg shadow-brand-blue/20"
            : "border-slate-200 bg-white text-slate-600 shadow-md hover:border-brand-blue hover:text-brand-blue",
          !onToggleCompare && "cursor-default opacity-70 hover:border-slate-200 hover:text-slate-600",
        )}
      >
        {selected ? "✓ En comparativa" : "+ Agregar a comparativa"}
      </button>
      {compareList && compareList.length > 0 && onToggleCompare && (
        <div className="mt-3 rounded-xl border border-slate-100 bg-slate-50 p-3 text-center">
          <p className="text-[10px] font-medium text-slate-400">{compareList.length}/3 programas seleccionados</p>
          <Link
            href={`/compare?ids=${compareList.map((item) => encodeURIComponent(item.id)).join(",")}`}
            className="mt-2 inline-block text-[11px] font-bold text-brand-blue underline underline-offset-2 hover:text-brand-blue/80"
          >
            Ver comparativa
          </Link>
        </div>
      )}
    </div>
  );
}

export default function CoursePublicRenderer({
  course,
  activeTab,
  onActiveTabChange,
  activeField,
  isPreview = false,
  compareList,
  onToggleCompare,
  relatedCourses = [],
}: CoursePublicRendererProps) {
  const overview = useMemo(() => course.description_long?.split("\n\n")[0], [course.description_long]);
  const showBenefits = isPreview || Boolean(course.benefits);
  const showObjectives = isPreview || Boolean(course.objectives);
  const showSyllabus = isPreview || Boolean(course.syllabus);
  const showTargetAudience = isPreview || Boolean(course.target_audience);
  const showRequirements = isPreview || Boolean(course.requirements);

  return (
    <div className={cn(
      "text-brand-slate dark:text-white font-sans selection:bg-brand-mint/30",
      isPreview ? "bg-white" : "min-h-screen bg-white pb-20 dark:bg-brand-slate",
    )}>
      <main className={cn("mx-auto max-w-6xl", isPreview ? "px-0 py-0" : "px-6 py-10")}>
        <nav className="mb-10 flex items-center gap-2 text-[11px] font-medium text-slate-400">
          <Link href="/" className="transition-colors hover:text-brand-blue">Home</Link>
          {course.category && <><span className="text-slate-300">/</span><span className="text-slate-600">{course.category}</span></>}
          {course.institution_name && <><span className="text-slate-300">/</span><span className="text-slate-600">{course.institution_name}</span></>}
          <span className="text-slate-300">/</span>
          <span className="max-w-[200px] truncate font-semibold text-brand-slate dark:text-white">{course.name}</span>
        </nav>

        <div className="grid grid-cols-1 gap-16 lg:grid-cols-3">
          <div className="space-y-10 lg:col-span-2">
            {!isPreview && course.is_active === false && (
              <div className="flex items-center gap-3 rounded-xl border border-red-100 bg-red-50 p-4 text-[11px] font-black uppercase tracking-wider text-red-600">
                <Info className="size-4" /> Programa finalizado o inscripciones cerradas.
              </div>
            )}

            <header className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-brand-blue/5 px-2 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-brand-blue">{course.institution_name}</span>
                  <span className="size-1 rounded-full bg-slate-300" />
                  <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">{course.course_type || "Programa"}</span>
                </div>

                <ImpactBlock field="name" activeField={activeField}>
                  <h1 className="text-4xl font-black uppercase leading-[1.1] tracking-tighter text-brand-slate md:text-5xl">{course.name}</h1>
                </ImpactBlock>

                <div className="flex flex-wrap items-center gap-2 pt-2">
                  {course.category && <Badge variant="outline" className="border-brand-mint/30 bg-brand-mint/5 px-3 py-1 text-[9px] font-bold uppercase tracking-widest text-brand-mint">{course.category}</Badge>}
                  <ImpactBlock field="mode" activeField={activeField} className="rounded-full">
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-600">
                      {course.mode?.toLowerCase() === "presencial" ? "🏫" : course.mode?.toLowerCase() === "remoto" ? "🌐" : course.mode?.toLowerCase() === "híbrido" || course.mode?.toLowerCase() === "hibrido" ? "🔀" : ""}{course.mode || "Modalidad por confirmar"}
                    </span>
                  </ImpactBlock>
                  {(isPreview || course.certification) && (
                    <ImpactBlock field="certification" activeField={activeField} className="rounded-full">
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-1 text-[10px] font-semibold text-amber-700"><Award className="size-3" /> {course.certification ? "Certificación" : "Certificación por confirmar"}</span>
                    </ImpactBlock>
                  )}
                  {course.seniority_level && <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-semibold text-emerald-700"><Sprout className="size-3" /> {course.seniority_level}</span>}
                </div>
              </div>

              {course.brochure_url && isValidUrl(course.brochure_url) && !isPreview && (
                <div className="pt-4">
                  <a href={course.brochure_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-3 rounded-xl bg-brand-blue px-8 py-3.5 text-[10px] font-black uppercase tracking-widest text-white shadow-xl shadow-brand-blue/20 transition-all hover:scale-105 active:scale-95">
                    <Download className="size-4" /> Descargar Brochure (PDF)
                  </a>
                </div>
              )}

              <div className="grid grid-cols-2 gap-8 border-y border-brand-gray/50 py-8 md:grid-cols-4">
                <ImpactBlock field="start_date_text" activeField={activeField} className="rounded-none"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Inicio</p><p className="mt-1 text-xs font-black uppercase text-brand-blue">{course.start_date_text || "Consultar"}</p></ImpactBlock>
                <ImpactBlock field="price_pen" activeField={activeField} activeFields={["price_status"]} className="rounded-none"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Inversión</p><p className="mt-1 truncate text-xs font-black uppercase text-brand-slate">{formatPrice(course)}</p></ImpactBlock>
                <ImpactBlock field="duration" activeField={activeField} className="rounded-none"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Duración</p><p className="mt-1 text-xs font-black uppercase text-brand-slate">{course.duration || "N/A"}</p></ImpactBlock>
                <ImpactBlock field="mode" activeField={activeField} anchor={false} className="rounded-none"><p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Modalidad</p><p className="mt-1 text-xs font-black uppercase text-brand-slate">{course.mode || "Consultar"}</p></ImpactBlock>
              </div>
            </header>

            <ImpactBlock field="price_pen" activeField={activeField} activeFields={["price_status"]} anchor={false} className="relative overflow-hidden rounded-[2rem] border border-white/5 bg-brand-slate p-10 text-white shadow-2xl">
              <div className="relative z-10">
                <div className="mb-8 flex items-center gap-2"><TrendingUp className="size-4 text-brand-mint" /><h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-brand-mint">Análisis de Retorno Educativo</h2></div>
                <div className="grid grid-cols-1 gap-10 md:grid-cols-3">
                  <div className="space-y-1"><p className="text-[9px] font-bold uppercase tracking-widest text-white/40">Inversión Total</p><p className="text-3xl font-black">{formatPrice(course, true)}</p></div>
                  <div className="space-y-1"><p className="text-[9px] font-bold uppercase tracking-widest text-white/40">Salario Sugerido</p><p className="text-3xl font-black text-brand-mint">{course.expected_monthly_salary ? `S/ ${Number(course.expected_monthly_salary).toLocaleString("es-PE")}` : "S/ --"}</p></div>
                  <div className="space-y-1"><p className="text-[9px] font-bold uppercase tracking-widest text-white/40">ROI (Estimado)</p><p className="text-3xl font-black">{course.roi_months ? `x${Number(course.roi_months).toFixed(1)}` : "—"}</p></div>
                </div>
                <p className="mt-8 border-t border-white/5 pt-4 text-[9px] font-bold uppercase leading-relaxed tracking-wider text-white/30">* Cálculos basados en Big Data laboral 2026 para {course.category || "tu área"}.</p>
              </div>
            </ImpactBlock>

            <section className="space-y-8">
              <div className="flex w-full items-center gap-4 overflow-x-auto rounded-2xl bg-slate-100 p-2 whitespace-nowrap [scrollbar-width:none] md:w-fit [&::-webkit-scrollbar]:hidden">
                <button type="button" onClick={() => onActiveTabChange?.("info")} className={cn("flex-shrink-0 rounded-xl px-6 py-2.5 text-[10px] font-black uppercase tracking-widest transition-all md:text-xs", activeTab === "info" ? "bg-white text-brand-blue shadow-sm" : "text-slate-500 hover:text-slate-700")}>GENERAL</button>
                <button type="button" onClick={() => onActiveTabChange?.("requisitos")} className={cn("flex-shrink-0 rounded-xl px-6 py-2.5 text-[10px] font-black uppercase tracking-widest transition-all md:text-xs", activeTab === "requisitos" ? "bg-white text-brand-blue shadow-sm" : "text-slate-500 hover:text-slate-700")}>REQUISITOS</button>
              </div>

              <div className="min-h-[200px] animate-in fade-in slide-in-from-bottom-2 duration-500">
                {activeTab === "info" && (
                  <div className="space-y-12">
                    <ImpactBlock field="description_long" activeField={activeField} className="space-y-4"><h2 className="flex items-center gap-2 text-2xl font-bold"><ShieldCheck className="size-6 text-brand-blue" /> Visión del Programa</h2><div className="prose max-w-none leading-relaxed text-slate-600 dark:prose-invert dark:text-slate-400">{renderPublicText(overview || (isPreview ? undefined : "Este programa representa una oportunidad estratégica de especialización."))}</div></ImpactBlock>
                    {showBenefits && <ImpactBlock field="benefits" activeField={activeField} className="space-y-4 border-t border-brand-gray/30 pt-6"><h2 className="flex items-center gap-2 text-2xl font-bold"><ShieldCheck className="size-6 text-brand-blue" /> Qué Incluye</h2><div className="prose max-w-none leading-relaxed text-slate-600 dark:prose-invert dark:text-slate-400">{renderPublicText(course.benefits)}</div></ImpactBlock>}
                    {showObjectives && <ImpactBlock field="objectives" activeField={activeField} className="space-y-4 border-t border-brand-gray/30 pt-6"><h2 className="flex items-center gap-2 text-2xl font-bold"><GraduationCap className="size-6 text-brand-blue" /> Qué Aprenderás (Objetivos)</h2><div className="prose max-w-none leading-relaxed text-slate-600 dark:prose-invert dark:text-slate-400">{renderPublicText(course.objectives)}</div></ImpactBlock>}
                    {showSyllabus && <ImpactBlock field="syllabus" activeField={activeField} className="space-y-4 border-t border-brand-gray/30 pt-6"><h2 className="flex items-center gap-2 text-2xl font-bold"><MapPin className="size-6 text-brand-blue" /> Temario Detallado</h2><div className="prose max-w-none rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-8 leading-relaxed text-slate-600 dark:prose-invert dark:border-white/10 dark:bg-white/5 dark:text-slate-400">{renderPublicText(course.syllabus)}</div></ImpactBlock>}
                  </div>
                )}

                {activeTab === "requisitos" && (
                  <div className="space-y-12">
                    {showTargetAudience && <ImpactBlock field="target_audience" activeField={activeField} className="space-y-4"><h2 className="flex items-center gap-2 text-2xl font-bold"><CheckCircle className="size-6 text-brand-blue" /> Perfil del Estudiante</h2><h4 className="text-xs font-black uppercase tracking-widest text-brand-blue">Dirigido a:</h4><div className="prose max-w-none text-lg italic leading-relaxed text-slate-600 dark:prose-invert dark:text-slate-400">{renderPublicText(course.target_audience)}</div></ImpactBlock>}
                    {showRequirements && <ImpactBlock field="requirements" activeField={activeField} className="space-y-4 border-t border-brand-gray/30 pt-6"><h2 className="flex items-center gap-2 text-2xl font-bold"><CheckCircle className="size-6 text-brand-blue" /> Requisitos Previos (Obligatorios)</h2><div className="prose max-w-none text-lg leading-relaxed text-slate-600 dark:prose-invert dark:text-slate-400">{renderPublicText(course.requirements, "No existen prerrequisitos técnicos estrictos reportados para este programa.")}</div></ImpactBlock>}
                    {!isPreview && !course.target_audience && !course.requirements && <div className="py-10 italic text-slate-400">No existen prerrequisitos técnicos estrictos reportados para este programa.</div>}
                  </div>
                )}
              </div>
            </section>
          </div>

          <div className="lg:col-span-1">
            <Card className="sticky top-24 overflow-hidden rounded-[2rem] border-0 border-brand-gray/50 bg-white p-10 shadow-2xl">
              <div className="mb-10 text-center lg:text-left"><h3 className="mb-2 text-2xl font-black uppercase tracking-tight">Solicitar Asesoría</h3><p className="text-[11px] font-bold uppercase leading-relaxed tracking-wider text-slate-400">Recibe el plan detallado y asesoría imparcial sobre este programa.</p></div>
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5"><p className="text-[11px] font-black uppercase tracking-widest text-amber-900">Canal cerrado temporalmente</p><p className="mt-3 text-[12px] font-semibold leading-6 text-amber-800/80">StudIAMatch no está capturando datos personales ni enviando solicitudes comerciales mientras se completa la validación editorial H2.</p></div>
              <ComparePanel course={course} compareList={compareList} onToggleCompare={onToggleCompare} isPreview={isPreview} />
            </Card>
          </div>
        </div>

        {relatedCourses.length > 0 && (
          <section className="mt-16 border-t border-brand-gray/50 pt-8">
            <div className="mb-12 flex flex-col justify-between gap-6 md:flex-row md:items-end"><div className="space-y-3"><div className="text-[10px] font-black uppercase tracking-[0.3em] text-brand-blue">Recomendaciones</div><h2 className="text-3xl font-black uppercase tracking-tight">Programas <span className="text-slate-400">Similares</span></h2></div><p className="text-[11px] font-bold uppercase tracking-widest text-slate-400">Basado en {course.category}</p></div>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              {relatedCourses.map((related) => {
                const relatedInstitution = cleanSlug(related.institution_slug || "general");
                return <article key={related.id} className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-brand-gray/50 bg-white p-6 shadow-premium transition-all hover:-translate-y-1 hover:border-brand-blue/30 hover:shadow-2xl"><div className="space-y-5"><div className="flex items-center justify-between"><span className="rounded bg-brand-blue/5 px-2 py-1 text-[9px] font-black uppercase tracking-widest text-brand-blue">{related.institution_name}</span><GraduationCap className="size-4 text-slate-200" /></div><Link href={`/courses/${relatedInstitution}/${related.slug}`}><h3 className="h-10 line-clamp-2 text-base font-black uppercase leading-tight text-brand-slate transition-colors group-hover:text-brand-blue">{related.name}</h3></Link><div className="flex items-center justify-between border-t border-brand-gray/30 pt-4"><span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">Inversión</span><span className="text-sm font-black uppercase text-brand-slate">{formatPrice(related, true)}</span></div></div><Link href={`/courses/${relatedInstitution}/${related.slug}`} className="mt-8 flex items-center justify-center rounded-xl border border-brand-gray/20 bg-slate-50 py-3.5 text-[10px] font-black uppercase tracking-widest text-slate-600 transition-all hover:bg-brand-blue hover:text-white">Ver Programa</Link></article>;
              })}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
