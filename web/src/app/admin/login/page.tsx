'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { currentAdminRole, getAuthSession, getOnboardingStatus, supabaseAdminLogin } from '@/lib/admin-auth';

function LoginForm() {
  const router = useRouter();
  const [sessionState, setSessionState] = useState<'checking' | 'anonymous' | 'authenticated'>('checking');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    void getAuthSession()
      .then((session) => {
        if (!active) return;
        if (session) {
          void Promise.all([getOnboardingStatus(), currentAdminRole()])
            .then(([onboarding, role]) => {
              if (!active) return;
              setSessionState('authenticated');
              const needsOnboarding = role === 'authenticated'
                || onboarding.success !== true
                || (onboarding.account_status !== null && onboarding.account_status !== 'ready');
              router.replace(needsOnboarding ? '/admin/accept-invite/' : '/admin/');
            })
            .catch(() => {
              if (!active) return;
              setSessionState('authenticated');
              router.replace('/admin/accept-invite/');
            });
          return;
        }
        setSessionState('anonymous');
      })
      .catch(() => {
        // A missing/expired browser session leaves the login form available.
        if (active) setSessionState('anonymous');
      });

    return () => {
      active = false;
    };
  }, [router]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await supabaseAdminLogin(email, password);
      router.replace('/admin/');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Error al iniciar sesión.');
    } finally {
      setLoading(false);
    }
  };

  if (sessionState !== 'anonymous') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <p className="text-sm text-slate-600" role="status">
          {sessionState === 'authenticated' ? 'Sesión activa. Abriendo el panel...' : 'Validando sesión...'}
        </p>
      </div>
    );
  }

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
