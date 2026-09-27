import type { ComponentType } from 'react';
import { Archive, CheckCircle2, CircleAlert, CircleDashed, FilePenLine, LockKeyhole, Send, ShieldAlert } from 'lucide-react';

export type EditorialStatus = 'draft' | 'pending_review' | 'published' | 'archived';
export type QualityStatus = 'pending' | 'complete' | 'blocked';

type StatusMeta = {
  label: string;
  description: string;
  className: string;
  icon: ComponentType<{ className?: string }>;
};

export const EDITORIAL_STATUS_META: Record<EditorialStatus, StatusMeta> = {
  draft: {
    label: 'Borrador',
    description: 'Curso en preparación, todavía no enviado a revisión final.',
    className: 'border-blue-200 bg-blue-50 text-blue-700',
    icon: FilePenLine,
  },
  pending_review: {
    label: 'Pendiente de revisión',
    description: 'El contenido espera una revisión editorial antes de publicarse.',
    className: 'border-amber-200 bg-amber-50 text-amber-800',
    icon: CircleAlert,
  },
  published: {
    label: 'Publicado',
    description: 'El curso puede aparecer en la experiencia pública si está disponible.',
    className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    icon: Send,
  },
  archived: {
    label: 'Archivado',
    description: 'Curso retirado del flujo editorial activo.',
    className: 'border-slate-200 bg-slate-100 text-slate-600',
    icon: Archive,
  },
};

export const QUALITY_STATUS_META: Record<QualityStatus, StatusMeta> = {
  pending: {
    label: 'Pendiente',
    description: 'Faltan campos requeridos o una validación de calidad.',
    className: 'border-amber-200 bg-amber-50 text-amber-800',
    icon: CircleDashed,
  },
  complete: {
    label: 'Completo',
    description: 'Los campos requeridos están completos y el curso puede evaluarse para publicación.',
    className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    icon: CheckCircle2,
  },
  blocked: {
    label: 'Bloqueado',
    description: 'Existe una condición que impide continuar o publicar el curso.',
    className: 'border-rose-200 bg-rose-50 text-rose-700',
    icon: ShieldAlert,
  },
};

export const FIELD_COPY: Record<string, {
  label: string;
  help: string;
  impact: string;
  placeholder: string;
  multiline?: boolean;
  inputMode?: 'text' | 'decimal';
  options?: Array<{ value: string; label: string }>;
}> = {
  name: {
    label: 'Nombre del curso',
    help: 'Título público que identifica el programa en la cola, la página de detalle y las tarjetas.',
    impact: 'Encabezado principal de la página pública.',
    placeholder: 'Ej. Analítica de Datos Aplicada',
  },
  price_pen: {
    label: 'Precio en soles',
    help: 'Monto numérico de la inversión cuando la institución publica un precio confirmado.',
    impact: 'Bloque de inversión y cálculo de retorno educativo.',
    placeholder: 'Ej. 1800',
    inputMode: 'decimal',
  },
  price_status: {
    label: 'Estado del precio',
    help: 'Define si la página muestra un monto o invita a consultar el precio.',
    impact: 'Etiqueta de inversión y valor mostrado en el bloque de retorno.',
    placeholder: 'Selecciona una opción',
    options: [
      { value: 'available', label: 'Precio disponible' },
      { value: 'consultar', label: 'Consultar precio' },
    ],
  },
  mode: {
    label: 'Modalidad',
    help: 'Forma en que se dicta el programa: presencial, remoto o híbrido.',
    impact: 'Chip de modalidad y resumen superior de la página pública.',
    placeholder: 'Selecciona una modalidad',
    options: [
      { value: 'Presencial', label: 'Presencial' },
      { value: 'Remoto', label: 'Remoto' },
      { value: 'Híbrido', label: 'Híbrido' },
    ],
  },
  duration: {
    label: 'Duración',
    help: 'Duración legible para una persona; evita placeholders que no expliquen el tiempo real.',
    impact: 'Resumen de duración del programa.',
    placeholder: 'Ej. 6 meses',
  },
  description_long: {
    label: 'Descripción pública',
    help: 'Explica qué es el programa y por qué puede ser relevante para el estudiante.',
    impact: 'Sección “Visión del Programa”.',
    placeholder: 'Describe el programa con información verificable...',
    multiline: true,
  },
  syllabus: {
    label: 'Temario',
    help: 'Resume los módulos, contenidos o temas que se desarrollan durante el programa.',
    impact: 'Sección “Temario Detallado”.',
    placeholder: 'Módulo 1...\nMódulo 2...',
    multiline: true,
  },
  target_audience: {
    label: 'Público objetivo',
    help: 'Indica a qué perfil de persona está dirigido el programa.',
    impact: 'Pestaña “Requisitos”, bloque “Perfil del Estudiante”.',
    placeholder: 'Personas que buscan...',
    multiline: true,
  },
  requirements: {
    label: 'Requisitos',
    help: 'Detalla conocimientos, documentos o condiciones previas para participar.',
    impact: 'Pestaña “Requisitos”, bloque “Requisitos Previos”.',
    placeholder: 'Conocimientos previos, documentos o condiciones...',
    multiline: true,
  },
  certification: {
    label: 'Certificación',
    help: 'Describe la certificación o credencial que la institución entrega al completar el programa.',
    impact: 'Chip de certificación en la cabecera pública.',
    placeholder: 'Certificado de...',
    multiline: true,
  },
  benefits: {
    label: 'Beneficios',
    help: 'Resume resultados, recursos o beneficios públicos que el programa ofrece.',
    impact: 'Sección “Qué Incluye”.',
    placeholder: '• Beneficio 1\n• Beneficio 2',
    multiline: true,
  },
  objectives: {
    label: 'Objetivos de aprendizaje',
    help: 'Explica qué podrá hacer o comprender la persona al finalizar el programa.',
    impact: 'Sección “Qué Aprenderás”.',
    placeholder: 'Al finalizar, la persona podrá...',
    multiline: true,
  },
  start_date_text: {
    label: 'Fecha de inicio',
    help: 'Fecha o texto de inicio que se mostrará cuando exista información confirmada.',
    impact: 'Resumen superior de inicio del programa.',
    placeholder: 'Ej. Marzo de 2027',
  },
};

export function getFieldCopy(fieldKey: string) {
  return FIELD_COPY[fieldKey] || {
    label: fieldKey.replaceAll('_', ' '),
    help: 'Información editorial del programa.',
    impact: 'Contenido público del programa.',
    placeholder: '',
  };
}

export function StatusBadge({ kind, value, compact = false }: { kind: 'editorial' | 'quality'; value: string; compact?: boolean }) {
  const meta = kind === 'editorial'
    ? EDITORIAL_STATUS_META[value as EditorialStatus]
    : QUALITY_STATUS_META[value as QualityStatus];
  const Icon = meta?.icon || LockKeyhole;
  const fallback = value.replaceAll('_', ' ');

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${compact ? 'px-2.5 py-1 text-[10px]' : 'px-3 py-1.5 text-xs'} ${meta?.className || 'border-slate-200 bg-slate-50 text-slate-600'}`} title={meta?.description || fallback}>
      <Icon className={compact ? 'size-3' : 'size-3.5'} aria-hidden="true" />
      {meta?.label || fallback}
    </span>
  );
}
