'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { adminRpc } from '@/lib/admin-auth';

interface Course {
  course_id: string;
  course_name: string;
  course_slug: string;
  institution_name: string;
  institution_slug: string;
  editorial_status: string;
  quality_status: string;
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

export default function AdminCourseQueue({ role }: { role: 'admin' | 'user' }) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [endCursor, setEndCursor] = useState<Record<string, string> | null>(null);
  const [currentCursor, setCurrentCursor] = useState<Record<string, string> | null>(null);
  const [cursorHistory, setCursorHistory] = useState<Array<Record<string, string> | null>>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [filters, setFilters] = useState({
    editorial_status: role === 'admin' ? 'pending_review' : 'draft',
    quality_status: role === 'admin' ? 'complete' : 'pending',
  });
  const [searchTerm, setSearchTerm] = useState('');

  const fetchQueue = useCallback(async (cursor: Record<string, string> | null = null) => {
    setLoading(true);
    setError(null);

    try {
      const [queueRows, countRows] = await Promise.all([
        adminRpc('admin_get_course_queue', {
          p_first: 20,
          p_after_cursor: cursor ? JSON.stringify(cursor) : null,
          p_editorial_status: filters.editorial_status || null,
          p_quality_status: filters.quality_status || null,
        }) as Promise<QueueRow[]>,
        adminRpc('admin_count_course_queue', {
          p_editorial_status: filters.editorial_status || null,
          p_quality_status: filters.quality_status || null,
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
      setError(reason instanceof Error ? reason.message : 'Error al cargar la cola.');
    } finally {
      setLoading(false);
    }
  }, [filters.editorial_status, filters.quality_status]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void fetchQueue(null), 0);
    return () => window.clearTimeout(timeout);
  }, [fetchQueue]);

  const visibleCourses = courses.filter((course) => {
    const term = searchTerm.trim().toLocaleLowerCase('es');
    return !term || course.course_name.toLocaleLowerCase('es').includes(term) || course.institution_name.toLocaleLowerCase('es').includes(term);
  });

  if (loading && courses.length === 0) {
    return <Card className="p-12 text-center text-sm text-slate-600">Cargando cola editorial...</Card>;
  }

  if (error) {
    return (
      <Card className="p-8 text-center">
        <h3 className="text-lg font-semibold text-slate-900">Error al cargar</h3>
        <p className="mt-2 text-sm text-slate-600">{error}</p>
        <Button onClick={() => void fetchQueue(currentCursor)} className="mt-6" variant="outline">Reintentar</Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="grid gap-4 md:grid-cols-4">
          <div className="space-y-2">
            <Label htmlFor="editorial-status-filter">Estado editorial</Label>
            <Select value={filters.editorial_status || '__all__'} onValueChange={(value) => setFilters((current) => ({ ...current, editorial_status: value === '__all__' ? '' : value }))}>
              <SelectTrigger id="editorial-status-filter"><SelectValue placeholder="Todos" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Todos</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="pending_review">Pendiente</SelectItem>
                <SelectItem value="published">Publicado</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="quality-status-filter">Estado calidad</Label>
            <Select value={filters.quality_status || '__all__'} onValueChange={(value) => setFilters((current) => ({ ...current, quality_status: value === '__all__' ? '' : value }))}>
              <SelectTrigger id="quality-status-filter"><SelectValue placeholder="Todos" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Todos</SelectItem>
                <SelectItem value="pending">Pendiente</SelectItem>
                <SelectItem value="complete">Completo</SelectItem>
                <SelectItem value="blocked">Bloqueado</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="admin-search">Buscar en esta página</Label>
            <Input id="admin-search" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Nombre o institución" />
          </div>
        </div>
        <p className="mt-4 text-sm text-slate-600">Total: <span className="font-semibold text-slate-900">{totalCount}</span> cursos</p>
      </Card>

      {visibleCourses.length === 0 ? (
        <Card className="p-12 text-center text-sm text-slate-600">No se encontraron cursos con los filtros actuales.</Card>
      ) : (
        <div className="space-y-4">
          {visibleCourses.map((course) => (
            <Card key={course.course_id} className="p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="mb-2 flex items-center gap-2">
                    <h3 className="font-semibold text-slate-900">{course.course_name}</h3>
                    <Badge variant={course.is_sponsored ? 'default' : 'outline'}>{course.institution_name}</Badge>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">{course.editorial_status.replace('_', ' ')}</Badge>
                    <Badge variant="outline">{course.quality_status.replace('_', ' ')}</Badge>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                   <a href={`/admin/edit/?id=${encodeURIComponent(course.course_id)}`} className="text-sm font-medium text-brand-blue">Editar</a>
                   {course.editorial_status === 'published' && (
                     <Link href={`/courses/${course.institution_slug}/${course.course_slug}/`} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-slate-600">Ver</Link>
                   )}
                </div>
              </div>
              <p className="mt-4 text-xs text-slate-500">Versión: {course.version}</p>
            </Card>
          ))}
        </div>
      )}

      {(cursorHistory.length > 0 || hasNextPage) && (
        <div className="flex justify-center gap-4">
          <Button variant="outline" disabled={cursorHistory.length === 0} onClick={() => {
            const history = [...cursorHistory];
            const previous = history.pop() || null;
            setCursorHistory(history);
            void fetchQueue(previous);
          }}>Anterior</Button>
          <Button variant="outline" disabled={!hasNextPage || !endCursor} onClick={() => {
            setCursorHistory((history) => [...history, currentCursor]);
            void fetchQueue(endCursor);
          }}>Siguiente</Button>
        </div>
      )}
    </div>
  );
}
