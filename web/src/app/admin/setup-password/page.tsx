'use client';

import { useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { PasswordInput } from '@/components/admin/PasswordInput';
import { PasswordRequirements } from '@/components/admin/PasswordRequirements';
import { completePasswordSetup, getOnboardingStatus, updateAdminPassword } from '@/lib/admin-auth';
import { getPasswordValidationMessage, hasPasswordRequirements, isPasswordValid } from '@/lib/password-policy';

function SetupPasswordContent() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  useEffect(() => {
    void getOnboardingStatus().then((status) => {
      if (status.account_status !== 'password_pending') {
        setError(status.account_status === 'ready' ? 'Esta cuenta ya está preparada.' : 'Primero debes aceptar una invitación válida.');
      }
    }).catch((reason) => setError(reason instanceof Error ? reason.message : 'Sesión inexistente.')).finally(() => setLoading(false));
  }, []);

  const passwordError = getPasswordValidationMessage(password, confirmation);
  const canSubmit = !loading && !saving && !error && isPasswordValid(password, confirmation);
  const passwordDescription = ['setup-password-requirements', passwordError ? 'setup-password-error' : null].filter(Boolean).join(' ');
  const passwordInvalid = Boolean(password && !hasPasswordRequirements(password));
  const confirmationInvalid = Boolean(confirmation && password !== confirmation);

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
        <p className="mt-3 text-sm leading-6 text-slate-600">Crea una contraseña segura. Se valida en tiempo real y se envía únicamente a Auth, nunca al RPC de onboarding.</p>
        {loading ? <p className="mt-6 text-sm text-slate-600" role="status">Validando sesión...</p> : error ? <p className="mt-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700" role="alert" aria-live="assertive">{error}</p> : (
          <form method="post" className="mt-7 space-y-5" onSubmit={handleSubmit}>
            <PasswordInput
              id="setup-password"
              label="Nueva contraseña"
              value={password}
              visible={showPassword}
              onChange={setPassword}
              onToggle={() => setShowPassword((visible) => !visible)}
              describedBy={passwordDescription}
              invalid={passwordInvalid}
              disabled={saving}
            />
            <PasswordInput
              id="setup-password-confirmation"
              label="Confirmar contraseña"
              value={confirmation}
              visible={showConfirmation}
              onChange={setConfirmation}
              onToggle={() => setShowConfirmation((visible) => !visible)}
              describedBy={passwordDescription}
              invalid={confirmationInvalid}
              disabled={saving}
            />
            <PasswordRequirements id="setup-password-requirements" password={password} confirmation={confirmation} />
            {passwordError && <p id="setup-password-error" className="text-sm text-red-600" aria-live="polite">{passwordError}</p>}
            <Button type="submit" className="w-full" disabled={!canSubmit}>{saving ? 'Activando cuenta...' : 'Guardar password'}</Button>
          </form>
        )}
      </Card>
    </main>
  );
}

function passwordSetupMessage(code: string | null): string {
  if (code === 'password_setup_not_pending' || code === 'invitation_not_accepted') return 'La invitación todavía no está aceptada.';
  if (code === 'membership_not_found' || code === 'missing_auth_user') return 'La sesión ya no está disponible.';
  return 'No se pudo activar la cuenta. Intenta nuevamente o solicita reconciliación al administrador.';
}

export default function AdminSetupPasswordPage() {
  return <Suspense fallback={<main className="flex min-h-screen items-center justify-center bg-slate-50"><p className="text-sm text-slate-600">Cargando...</p></main>}><SetupPasswordContent /></Suspense>;
}
