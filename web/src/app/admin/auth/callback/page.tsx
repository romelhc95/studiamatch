'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useRef, useState } from 'react';
import { acceptCurrentInvitation, consumeInviteSessionFromHash, exchangeCodeForSession, signOutAdmin } from '@/lib/admin-auth';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hasStarted = useRef(false);
  const [message, setMessage] = useState('Validando tu invitación...');

  useEffect(() => {
    void (async () => {
      if (hasStarted.current) return;
      hasStarted.current = true;

      const code = searchParams.get('code');
      const error = searchParams.get('error');
      const hash = document.location.hash;
      window.history.replaceState({}, document.title, '/admin/auth/callback/');

      if (error || (!code && !hash)) {
        setMessage('El enlace de invitación es inválido, expiró o ya fue utilizado.');
        return;
      }

      try {
        if (code) {
          await exchangeCodeForSession(code);
        } else {
          await consumeInviteSessionFromHash(hash);
        }
        const acceptance = await acceptCurrentInvitation();
        if (!acceptance.success) {
          await signOutAdmin();
          setMessage(messageForInvitationError(acceptance.error_code));
          return;
        }
        router.replace('/admin/accept-invite/');
      } catch (reason) {
        await signOutAdmin();
        setMessage(reason instanceof Error ? reason.message : 'No se pudo validar la invitación.');
      }
    })();
  }, [router, searchParams]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-blue">StudIAMatch · acceso editorial</p>
        <h1 className="mt-4 text-2xl font-bold text-slate-900">{message.includes('inválido') || message.includes('disponible') ? 'Invitación no disponible' : 'Preparando tu acceso'}</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">{message}</p>
      </section>
    </main>
  );
}

function messageForInvitationError(code: string | null): string {
  switch (code) {
    case 'invitation_expired': return 'La invitación expiró. Solicita al administrador que la envíe nuevamente.';
    case 'invitation_revoked': return 'La invitación fue revocada. Solicita una nueva invitación al administrador.';
    case 'invitation_superseded': return 'Esta invitación fue reemplazada. Usa el enlace más reciente.';
    case 'auth_identity_mismatch': return 'No se pudo asociar esta sesión con la invitación.';
    case 'invitation_not_pending': return 'La invitación ya fue utilizada o no está pendiente.';
    default: return 'No se pudo validar la invitación. Solicita una nueva invitación al administrador.';
  }
}

export default function AdminAuthCallbackPage() {
  return (
    <Suspense fallback={<main className="flex min-h-screen items-center justify-center bg-slate-50"><p className="text-sm text-slate-600">Validando...</p></main>}>
      <CallbackContent />
    </Suspense>
  );
}
