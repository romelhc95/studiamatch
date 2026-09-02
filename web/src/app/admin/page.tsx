'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import AdminCourseQueue from '@/components/AdminCourseQueue';
import { requireActiveAdmin, signOutAdmin, type AdminRole } from '@/lib/admin-auth';

export default function AdminDashboardPage() {
  const router = useRouter();
  const [role, setRole] = useState<AdminRole | null>(null);

  useEffect(() => {
    requireActiveAdmin()
      .then(setRole)
      .catch(() => router.replace('/admin/login/'));
  }, [router]);

  const handleLogout = async () => {
    await signOutAdmin();
    router.replace('/admin/login/');
  };

  if (!role) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-brand-slate">
        <p className="text-sm text-brand-blue">Validando acceso...</p>
      </div>
    );
  }

  const isAdmin = role === 'admin';

  return (
    <div className="min-h-screen bg-brand-slate">
      <header className="border-b border-brand-blue/10 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-bold text-brand-blue">StudIAMatch Admin</h1>
            <p className="text-xs text-brand-slate/70">Panel editorial</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-brand-mint px-3 py-1 text-xs font-semibold text-brand-blue">
              {isAdmin ? 'Admin' : 'User'}
            </span>
            {isAdmin && (
              <Link href="/admin/users/" className="text-sm font-medium text-brand-blue">Usuarios</Link>
            )}
            <button type="button" onClick={handleLogout} className="rounded-lg border border-brand-blue/20 bg-white px-4 py-2 text-sm font-medium text-brand-blue hover:bg-brand-mint">
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-brand-blue">{isAdmin ? 'Cola editorial' : 'Panel de actualización de información'}</h2>
        </div>
        <Suspense fallback={<div className="text-sm text-brand-slate/70">Cargando cola...</div>}>
           <AdminCourseQueue role={role === 'admin' ? 'admin' : 'user'} />
        </Suspense>
      </main>
    </div>
  );
}
