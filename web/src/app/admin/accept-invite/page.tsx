'use client';

import { useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getOnboardingStatus, type OnboardingStatusResult } from '@/lib/admin-auth';

function AcceptInviteContent() {
  const router = useRouter();
  const [status, setStatus] = useState<OnboardingStatusResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getOnboardingStatus().then(setStatus).catch((reason) => setError(reason instanceof Error ? reason.message : 'No se pudo leer el estado de la invitación.'));
  }, []);

  const accountStatus = status?.account_status;
  const invitationStatus = status?.invitation_status;
  const pendingPassword = accountStatus === 'password_pending';
  const success = pendingPassword || accountStatus === 'ready' || invitationStatus === 'accepted';
  const title = pendingPassword ? 'Invitación aceptada' : accountStatus === 'ready' ? 'Cuenta lista' : invitationStatus === 'expired' ? 'Invitación expirada' : invitationStatus === 'revoked' ? 'Invitación revocada' : invitationStatus === 'superseded' ? 'Invitación reemplazada' : error ? 'Sesión no disponible' : success ? 'Invitación aceptada' : 'Invitación no disponible';

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <Card className="w-full max-w-lg border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-blue">StudIAMatch · invitación</p>
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-900">{title}</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">{error || invitationMessage(invitationStatus, accountStatus)}</p>
        {status?.email && <p className="mt-5 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">Cuenta: <strong>{status.email}</strong></p>}
        <div className="mt-7 flex flex-wrap gap-3">
          {pendingPassword && <Button type="button" onClick={() => router.push('/admin/setup-password/')}>Definir password</Button>}
          {accountStatus === 'ready' && <Button type="button" onClick={() => router.push('/admin/')}>Ir al panel</Button>}
          {!success && !error && <Button type="button" variant="outline" onClick={() => window.location.reload()}>Volver a validar</Button>}
          {(error || ['expired', 'revoked', 'superseded'].includes(invitationStatus || '')) && <Button type="button" variant="outline" onClick={() => router.push('/admin/login/')}>Ir al login</Button>}
        </div>
      </Card>
    </main>
  );
}

function invitationMessage(invitationStatus: string | null | undefined, accountStatus: string | null | undefined): string {
  if (accountStatus === 'password_pending') return 'La invitación quedó asociada a tu cuenta. Define tu password inicial para activar el acceso editorial.';
  if (accountStatus === 'ready') return 'Tu cuenta ya está activa. Puedes entrar al panel editorial.';
  if (invitationStatus === 'expired') return 'El plazo de 24 horas terminó. Solicita al administrador un nuevo envío.';
  if (invitationStatus === 'revoked') return 'Esta invitación ya no puede utilizarse. Solicita al administrador una nueva invitación.';
  if (invitationStatus === 'superseded') return 'El administrador emitió una invitación más reciente. Usa ese enlace.';
  return 'No hay una invitación pendiente asociada a esta sesión.';
}

export default function AdminAcceptInvitePage() {
  return <Suspense fallback={<main className="flex min-h-screen items-center justify-center bg-slate-50"><p className="text-sm text-slate-600">Cargando estado...</p></main>}><AcceptInviteContent /></Suspense>;
}
