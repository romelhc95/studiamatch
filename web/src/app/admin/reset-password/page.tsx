'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowRight, Check, KeyRound, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { PasswordInput } from '@/components/admin/PasswordInput';
import { PasswordRequirements } from '@/components/admin/PasswordRequirements';
import {
  consumeRecoverySessionFromHash,
  exchangeRecoveryCodeForSession,
  getAuthSession,
  signOutAdmin,
  updateAdminPassword,
} from '@/lib/admin-auth';
import { getPasswordValidationMessage, hasPasswordRequirements, isPasswordValid, PASSWORD_MIN_LENGTH } from '@/lib/password-policy';

type PageState = 'preparing' | 'ready' | 'saving' | 'complete' | 'error';

export default function ResetPasswordPage() {
  const router = useRouter();
  const [pageState, setPageState] = useState<PageState>('preparing');
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  useEffect(() => {
    let active = true;

    const prepareRecoverySession = async () => {
      const url = new URL(window.location.href);
      const code = url.searchParams.get('code');
      const queryError = url.searchParams.get('error') || url.searchParams.get('error_description');
      const hash = window.location.hash;
      const hashParams = new URLSearchParams(hash.startsWith('#') ? hash.slice(1) : hash);
      const callbackType = url.searchParams.get('type') || hashParams.get('type');

      // Remove code, hash and provider errors before doing any async work so
      // recovery credentials do not remain in browser history or screenshots.
      window.history.replaceState({}, document.title, '/admin/reset-password/');

      try {
        if (queryError || hashParams.get('error') || hashParams.get('error_description')) {
          throw new Error('El enlace de recuperación es inválido, expiró o ya fue utilizado.');
        }
        if (callbackType && callbackType !== 'recovery') {
          throw new Error('Este enlace no corresponde a una recuperación de contraseña.');
        }

        if (code) {
          await exchangeRecoveryCodeForSession(code);
        } else if (hash) {
          await consumeRecoverySessionFromHash(hash);
        } else if (!(await getAuthSession())) {
          throw new Error('Abre esta pantalla desde el enlace de recuperación recibido por correo.');
        }

        if (active) setPageState('ready');
      } catch (reason) {
        if (!active) return;
        setError(reason instanceof Error ? reason.message : 'No se pudo preparar la recuperación.');
        setPageState('error');
      }
    };

    void prepareRecoverySession();
    return () => {
      active = false;
    };
  }, []);

  const passwordError = getPasswordValidationMessage(password, confirmation);
  const canSubmit = pageState === 'ready' && isPasswordValid(password, confirmation);
  const passwordDescription = ['recovery-password-requirements', passwordError ? 'recovery-password-error' : null].filter(Boolean).join(' ');
  const passwordInvalid = Boolean(password && !hasPasswordRequirements(password));
  const confirmationInvalid = Boolean(confirmation && password !== confirmation);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit) return;

    setPageState('saving');
    setError(null);
    try {
      // Passwords are sent only to Supabase Auth. No onboarding RPC receives it.
      await updateAdminPassword(password);
      setPassword('');
      setConfirmation('');
      await signOutAdmin().catch(() => undefined);
      setPageState('complete');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo actualizar la contraseña.');
      setPageState('ready');
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-brand-slate px-4 py-10 text-slate-900 sm:px-6">
      <div aria-hidden="true" className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full bg-brand-blue/30 blur-3xl" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-48 -left-24 h-96 w-96 rounded-full bg-brand-mint/20 blur-3xl" />

      <div className="relative mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-8 lg:grid-cols-[0.82fr_1.18fr]">
        <section className="hidden px-4 text-white lg:block">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-lg font-black text-brand-blue shadow-lg shadow-black/10">SM</div>
            <div>
              <p className="font-semibold tracking-tight">StudIAMatch</p>
              <p className="text-xs text-slate-300">Acceso editorial</p>
            </div>
          </div>
          <p className="mb-4 text-xs font-semibold uppercase tracking-[0.24em] text-brand-mint">Recuperación segura</p>
          <h1 className="max-w-md text-4xl font-bold leading-tight tracking-tight xl:text-5xl">Vuelve a tener el control de tu panel.</h1>
          <p className="mt-6 max-w-md text-sm leading-7 text-slate-300">Define una nueva contraseña para tu cuenta administrativa. Tu contraseña se procesa exclusivamente en Supabase Auth.</p>
          <div className="mt-10 space-y-4 text-sm text-slate-200">
            <div className="flex items-start gap-3"><ShieldCheck className="mt-0.5 size-5 text-brand-mint" /><span>La sesión temporal se limpia al terminar.</span></div>
            <div className="flex items-start gap-3"><KeyRound className="mt-0.5 size-5 text-brand-mint" /><span>La contraseña nunca se envía a las RPC de onboarding.</span></div>
          </div>
        </section>

        <Card className="border-white/10 bg-white p-6 shadow-2xl shadow-black/20 sm:p-10">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-blue">StudIAMatch · seguridad</p>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-brand-slate">Restablece tu contraseña</h2>
              <p className="mt-3 text-sm leading-6 text-slate-600">Usa una contraseña nueva para recuperar el acceso al panel editorial.</p>
            </div>
            <div className="hidden rounded-2xl bg-brand-gray p-3 text-brand-blue sm:block"><KeyRound className="size-6" /></div>
          </div>

          {pageState === 'preparing' && <StatusMessage>Validando el enlace de recuperación…</StatusMessage>}

          {pageState === 'error' && (
            <div className="space-y-5" aria-live="polite">
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700">{error}</div>
              <Button type="button" variant="outline" className="w-full" onClick={() => router.replace('/admin/login/')}>Volver al login <ArrowRight /></Button>
            </div>
          )}

          {pageState === 'complete' && (
            <div className="space-y-5" aria-live="polite">
              <div className="flex gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-sm leading-6 text-emerald-800">
                <Check className="mt-0.5 size-5 shrink-0" />
                <p>Contraseña actualizada correctamente. Inicia sesión nuevamente y completa MFA si se solicita.</p>
              </div>
              <Button type="button" className="w-full" onClick={() => router.replace('/admin/login/')}>Ir al login <ArrowRight /></Button>
            </div>
          )}

          {(pageState === 'ready' || pageState === 'saving') && (
            <form method="post" className="space-y-5" onSubmit={handleSubmit}>
              <PasswordInput
                id="recovery-password"
                label="Nueva contraseña"
                value={password}
                visible={showPassword}
                onChange={setPassword}
                onToggle={() => setShowPassword((visible) => !visible)}
                describedBy={passwordDescription}
                invalid={passwordInvalid}
                disabled={pageState === 'saving'}
              />
              <PasswordInput
                id="recovery-password-confirmation"
                label="Confirmar contraseña"
                value={confirmation}
                visible={showConfirmation}
                onChange={setConfirmation}
                onToggle={() => setShowConfirmation((visible) => !visible)}
                describedBy={passwordDescription}
                invalid={confirmationInvalid}
                disabled={pageState === 'saving'}
              />
              <PasswordRequirements id="recovery-password-requirements" password={password} confirmation={confirmation} />
              {passwordError && <p id="recovery-password-error" className="text-sm leading-5 text-red-600" aria-live="polite">{passwordError}</p>}
              {error && <p className="text-sm leading-5 text-red-600" aria-live="polite">{error}</p>}
              <Button type="submit" className="h-11 w-full" disabled={!canSubmit}>{pageState === 'saving' ? 'Guardando…' : 'Guardar nueva contraseña'} <ArrowRight /></Button>
              <p className="text-center text-xs leading-5 text-slate-500">Mínimo {PASSWORD_MIN_LENGTH} caracteres, con mayúscula, minúscula, número y símbolo.</p>
            </form>
          )}
        </Card>
      </div>
    </main>
  );
}

function StatusMessage({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl bg-brand-gray px-4 py-4 text-sm text-slate-600" role="status">{children}</div>;
}
