'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Suspense, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { challengeTotp, enrollTotp, getAuthenticatorAssuranceLevel, listFactors, supabaseAdminLogin, saveAdminSession, verifyTotp } from '@/lib/admin-auth';

function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mfaFactorId, setMfaFactorId] = useState<string | null>(null);
  const [mfaChallengeId, setMfaChallengeId] = useState<string | null>(null);
  const [mfaEnrollment, setMfaEnrollment] = useState<{ secret: string | null; uri: string | null; qrCode: string | null } | null>(null);
  const [mfaCode, setMfaCode] = useState('');

  const handleMfaSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!mfaFactorId || !mfaChallengeId) return;
    setLoading(true);
    setError(null);
    try {
      await verifyTotp(mfaFactorId, mfaChallengeId, mfaCode);
      const assurance = await getAuthenticatorAssuranceLevel();
      if (assurance.currentLevel !== 'aal2') throw new Error('MFA no verificado');
      router.replace('/admin/');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Código MFA inválido.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
       const session = await supabaseAdminLogin(email, password);
      saveAdminSession(session);
       const factors = await listFactors();
       let factor = factors.find((item) => item.factor_type === 'totp' && item.status === 'verified');
       if (!factor) {
        const enrollment = await enrollTotp();
        setMfaEnrollment({ secret: enrollment.secret, uri: enrollment.uri, qrCode: enrollment.qrCode });
        factor = { id: enrollment.factorId, factor_type: 'totp', status: 'unverified' };
       }
       const challenge = await challengeTotp(factor.id);
       setMfaFactorId(factor.id);
       setMfaChallengeId(challenge.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Error al iniciar sesión.');
    } finally {
      setLoading(false);
    }
  };

  const formattedMfaSecret = mfaEnrollment?.secret ? mfaEnrollment.secret.replace(/(.{4})/g, '$1 ').trim() : '';

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <h1 className="text-xl font-bold text-slate-900">Admin</h1>
          <p className="text-sm text-slate-500">Panel editorial StudIAMatch</p>
        </div>

         {mfaChallengeId ? (
           <form onSubmit={handleMfaSubmit} className="space-y-4">
             {mfaEnrollment && (
               <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-left">
                 <p className="text-xs font-semibold text-slate-700">Registra tu autenticador</p>
                 <p className="mt-1 text-xs text-slate-600">
                   Escanea el código QR o ingresa la llave secreta en tu app de autenticación y luego escribe el código de 6 dígitos.
                 </p>
                 {mfaEnrollment.qrCode && mfaEnrollment.qrCode.startsWith('data:image') && (
                   <div className="mt-2 flex justify-center">
                     {/* eslint-disable-next-line @next/next/no-img-element */}
                     <img src={mfaEnrollment.qrCode} alt="Código QR de autenticación MFA" className="h-28 w-28 rounded-md border border-slate-200 bg-white object-contain" />
                   </div>
                 )}
                 {mfaEnrollment.secret && (
                   <div className="mt-2">
                     <p className="text-xs font-medium text-slate-600">Llave secreta</p>
                     <code className="block select-all break-all rounded bg-white px-2 py-1 text-xs text-slate-700">{formattedMfaSecret}</code>
                   </div>
                 )}
                 {mfaEnrollment.uri && (
                   <div className="mt-2">
                     <p className="text-xs font-medium text-slate-600">otpauth URI</p>
                     <code className="block select-all break-all rounded bg-white px-2 py-1 text-xs text-slate-500">{mfaEnrollment.uri}</code>
                   </div>
                 )}
               </div>
             )}
             <div>
               <label htmlFor="admin-mfa-code" className="mb-1 block text-sm font-medium text-slate-700">Código MFA</label>
               <Input id="admin-mfa-code" name="mfa-code" inputMode="numeric" pattern="[0-9]{6}" value={mfaCode} onChange={(event) => setMfaCode(event.target.value)} required autoComplete="one-time-code" />
             </div>
             {error && <p className="text-sm text-red-600">{error}</p>}
             <Button type="submit" className="w-full" disabled={loading}>{loading ? 'Verificando...' : 'Verificar MFA'}</Button>
           </form>
         ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="admin-email" className="mb-1 block text-sm font-medium text-slate-700">Email</label>
            <Input id="admin-email" name="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
          </div>

          <div>
            <label htmlFor="admin-password" className="mb-1 block text-sm font-medium text-slate-700">Password</label>
            <Input id="admin-password" name="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Validando...' : 'Iniciar sesión'}
          </Button>
         </form>
         )}
 
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
