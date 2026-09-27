'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Suspense, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { supabaseAdminLogin, saveAdminSession } from '@/lib/admin-auth';

function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const session = await supabaseAdminLogin(email, password);
      saveAdminSession(session);
      router.replace('/admin/');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Error al iniciar sesión.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <h1 className="text-xl font-bold text-slate-900">Admin</h1>
          <p className="text-sm text-slate-500">Panel editorial StudIAMatch</p>
        </div>

        <form method="post" onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm leading-6 text-slate-600">La contraseña valida tu identidad. Las operaciones editoriales sensibles pueden requerir MFA de forma explícita.</p>
          <div>
            <label htmlFor="admin-email" className="mb-1 block text-sm font-medium text-slate-700">Email</label>
            <Input id="admin-email" name="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
          </div>

          <div>
            <label htmlFor="admin-password" className="mb-1 block text-sm font-medium text-slate-700">Password</label>
            <Input id="admin-password" name="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" />
          </div>

          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Validando...' : 'Iniciar sesión'}
          </Button>
        </form>

         <p className="mt-4 text-center text-xs text-slate-400">
          <Link href="/" className="underline">Volver al inicio</Link>
        </p>
      </div>
    </div>
  );
}

export default function AdminLoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-slate-50"><p className="text-sm text-slate-600">Cargando...</p></div>}>
      <LoginForm />
    </Suspense>
  );
}
