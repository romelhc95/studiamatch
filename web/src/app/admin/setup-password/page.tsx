'use client';

import { useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { completePasswordSetup, getOnboardingStatus, updateAdminPassword } from '@/lib/admin-auth';

const MIN_PASSWORD_LENGTH = 12;

function SetupPasswordContent() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getOnboardingStatus().then((status) => {
      if (status.account_status !== 'password_pending') {
        setError(status.account_status === 'ready' ? 'Esta cuenta ya está preparada.' : 'Primero debes aceptar una invitación válida.');
      }
    }).catch((reason) => setError(reason instanceof Error ? reason.message : 'Sesión inexistente.')).finally(() => setLoading(false));
  }, []);

  const passwordError = validatePassword(password, confirmation);
  const canSubmit = !loading && !saving && !error && passwordError === null;

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit) return;
    setSaving(true);
    setError(null);
    try {
      await updateAdminPassword(password);
      const result = await completePasswordSetup();
      if (!result.success) throw new Error(passwordSetupMessage(result.error_code));
      setPassword('');
      setConfirmation('');
      router.replace('/admin/');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo completar la configuración.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <Card className="w-full max-w-md border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-blue">StudIAMatch · primer acceso</p>
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-900">Crea tu password</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">Usa una password de al menos {MIN_PASSWORD_LENGTH} caracteres. La password se envía únicamente a Auth y nunca al RPC de onboarding.</p>
        {loading ? <p className="mt-6 text-sm text-slate-600">Validando sesión...</p> : error ? <p className="mt-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : (
          <form className="mt-7 space-y-5" onSubmit={handleSubmit}>
            <div><label htmlFor="setup-password" className="mb-1 block text-sm font-medium text-slate-700">Password</label><Input id="setup-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" minLength={MIN_PASSWORD_LENGTH} required /></div>
            <div><label htmlFor="setup-password-confirmation" className="mb-1 block text-sm font-medium text-slate-700">Confirmar password</label><Input id="setup-password-confirmation" type="password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} autoComplete="new-password" minLength={MIN_PASSWORD_LENGTH} required /></div>
            {passwordError && <p className="text-sm text-red-600">{passwordError}</p>}
            <Button type="submit" className="w-full" disabled={!canSubmit}>{saving ? 'Activando cuenta...' : 'Guardar password'}</Button>
          </form>
        )}
      </Card>
    </main>
  );
}

function validatePassword(password: string, confirmation: string): string | null {
  if (!password && !confirmation) return 'Ingresa y confirma tu password.';
  if (password.length < MIN_PASSWORD_LENGTH) return `La password debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
  if (!/[a-z]/.test(password) || !/[A-Z]/.test(password) || !/[0-9]/.test(password)) return 'Incluye mayúsculas, minúsculas y al menos un número.';
  if (password !== confirmation) return 'Las passwords no coinciden.';
  return null;
}

function passwordSetupMessage(code: string | null): string {
  if (code === 'password_setup_not_pending' || code === 'invitation_not_accepted') return 'La invitación todavía no está aceptada.';
  if (code === 'membership_not_found' || code === 'missing_auth_user') return 'La sesión ya no está disponible.';
  return 'No se pudo activar la cuenta. Intenta nuevamente o solicita reconciliación al administrador.';
}

export default function AdminSetupPasswordPage() {
  return <Suspense fallback={<main className="flex min-h-screen items-center justify-center bg-slate-50"><p className="text-sm text-slate-600">Cargando...</p></main>}><SetupPasswordContent /></Suspense>;
}
