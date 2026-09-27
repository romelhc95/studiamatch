'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { challengeTotp, enrollTotp, getAuthenticatorAssuranceLevel, listFactors, unenrollTotp, verifyTotp } from '@/lib/admin-auth';

type MfaStep = 'idle' | 'starting' | 'challenge' | 'pending' | 'verifying' | 'complete';

interface MfaRequiredCardProps {
  title?: string;
  description?: string;
  onVerified?: () => void;
}

export function MfaRequiredCard({
  title = 'Configura MFA para continuar',
  description = 'Tu contraseña es válida. Esta operación editorial requiere un segundo factor de autenticación, pero no se configurará sin tu confirmación.',
  onVerified,
}: MfaRequiredCardProps) {
  const [step, setStep] = useState<MfaStep>('idle');
  const [factorId, setFactorId] = useState<string | null>(null);
  const [challengeId, setChallengeId] = useState<string | null>(null);
  const [pendingFactorId, setPendingFactorId] = useState<string | null>(null);
  const [enrollment, setEnrollment] = useState<{ secret: string | null; uri: string | null; qrCode: string | null } | null>(null);
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const prepareExistingFactorChallenge = async () => {
      setStep('starting');
      setError(null);
      try {
        const factors = await listFactors();
        if (!active) return;

        const verifiedFactor = factors.find((factor) => factor.status === 'verified');
        if (verifiedFactor) {
          const challenge = await challengeTotp(verifiedFactor.id);
          if (!active) return;
          setFactorId(verifiedFactor.id);
          setChallengeId(challenge.id);
          setStep('challenge');
          return;
        }

        const pendingFactor = factors.find((factor) => factor.status === 'unverified');
        if (pendingFactor) {
          setPendingFactorId(pendingFactor.id);
          setStep('pending');
          return;
        }

        setStep('idle');
      } catch (reason) {
        if (!active) return;
        setError(reason instanceof Error ? reason.message : 'No se pudo consultar la configuración MFA.');
        setStep('idle');
      }
    };

    void prepareExistingFactorChallenge();
    return () => {
      active = false;
    };
  }, []);

  const startChallenge = async (nextFactorId: string) => {
    const challenge = await challengeTotp(nextFactorId);
    setFactorId(nextFactorId);
    setChallengeId(challenge.id);
    setStep('challenge');
  };

  const startSetup = async () => {
    setStep('starting');
    setError(null);
    try {
      const factors = await listFactors();
      const verifiedFactor = factors.find((factor) => factor.status === 'verified');
      if (verifiedFactor) {
        await startChallenge(verifiedFactor.id);
        return;
      }

      const pendingFactor = factors.find((factor) => factor.status === 'unverified');
      if (pendingFactor) {
        setPendingFactorId(pendingFactor.id);
        setStep('pending');
        return;
      }

      const nextEnrollment = await enrollTotp();
      setEnrollment(nextEnrollment);
      await startChallenge(nextEnrollment.factorId);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo iniciar la configuración MFA.');
      setStep('idle');
    }
  };

  const restartPendingSetup = async () => {
    if (!pendingFactorId) return;
    setStep('starting');
    setError(null);
    try {
      await unenrollTotp(pendingFactorId);
      setPendingFactorId(null);
      const nextEnrollment = await enrollTotp();
      setEnrollment(nextEnrollment);
      await startChallenge(nextEnrollment.factorId);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo reiniciar la configuración MFA.');
      setStep('pending');
    }
  };

  const verify = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!factorId || !challengeId || code.length !== 6) return;
    setStep('verifying');
    setError(null);
    try {
      await verifyTotp(factorId, challengeId, code);
      const assurance = await getAuthenticatorAssuranceLevel();
      if (assurance.currentLevel !== 'aal2') throw new Error('No se pudo confirmar el segundo factor.');
      setCode('');
      setStep('complete');
      if (onVerified) onVerified();
      else window.location.reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Código MFA inválido.');
      setStep('challenge');
    }
  };

  const existingFactorChallenge = step === 'challenge' && !enrollment;

  return (
    <Card className="border-amber-200 bg-amber-50/80 p-6 shadow-sm" role="region" aria-labelledby="mfa-required-title">
      <div className="max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">Seguridad de la operación</p>
        <h2 id="mfa-required-title" className="mt-2 text-xl font-bold text-slate-900">{existingFactorChallenge ? 'Verifica MFA para continuar' : title}</h2>
        <p className="mt-2 text-sm leading-6 text-slate-700">{existingFactorChallenge ? 'Tu autenticador ya está configurado. Ingresa el código de 6 dígitos para continuar.' : description}</p>

        {step === 'idle' && (
          <Button type="button" className="mt-5" onClick={() => void startSetup()}>
            Configurar MFA
          </Button>
        )}

        {step === 'starting' && <p className="mt-5 text-sm text-slate-600" role="status">Comprobando tu configuración MFA...</p>}

        {step === 'pending' && (
          <div className="mt-5 space-y-3 rounded-xl border border-amber-200 bg-white/70 p-4">
            <p className="text-sm leading-6 text-slate-700">
              Hay una configuración MFA pendiente de confirmar. Puedes reiniciarla para recibir un nuevo QR; la configuración pendiente se retirará solo después de tu confirmación.
            </p>
            <Button type="button" variant="outline" onClick={() => void restartPendingSetup()}>
              Reiniciar configuración MFA
            </Button>
          </div>
        )}

        {(step === 'challenge' || step === 'verifying') && (
          <form method="post" className="mt-5 space-y-4 rounded-xl border border-amber-200 bg-white/70 p-4" onSubmit={verify}>
            {enrollment && (
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">Registra tu autenticador</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">Escanea el QR o ingresa la clave secreta en tu aplicación de autenticación. No compartas estos datos.</p>
                </div>
                {enrollment.qrCode?.startsWith('data:image') && (
                  <div className="flex justify-center rounded-lg border border-slate-200 bg-white p-3">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={enrollment.qrCode} alt="Código QR para configurar MFA" className="h-40 w-40" />
                  </div>
                )}
                {enrollment.secret && (
                  <div>
                    <Label htmlFor="mfa-secret">Clave secreta</Label>
                    <Input id="mfa-secret" value={enrollment.secret} readOnly className="mt-1 font-mono text-xs" />
                  </div>
                )}
                {enrollment.uri && <p className="break-all text-xs text-slate-500">URI: {enrollment.uri}</p>}
              </div>
            )}
            <div>
              <Label htmlFor="mfa-code">Código de 6 dígitos</Label>
              <Input
                id="mfa-code"
                name="mfa-code"
                className="mt-1"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                autoComplete="one-time-code"
                value={code}
                onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 6))}
                disabled={step === 'verifying'}
                required
              />
            </div>
            {error && <p className="text-sm leading-5 text-red-700" role="alert">{error}</p>}
            <Button type="submit" disabled={step === 'verifying' || code.length !== 6}>
              {step === 'verifying' ? 'Verificando...' : 'Verificar MFA'}
            </Button>
          </form>
        )}

        {step === 'complete' && (
          <p className="mt-5 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
            MFA verificada. Puedes continuar con la operación.
          </p>
        )}

        {error && step === 'idle' && <p className="mt-4 text-sm leading-5 text-red-700" role="alert">{error}</p>}
      </div>
    </Card>
  );
}
