'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MfaRequiredCard } from '@/components/admin/MfaRequiredCard';
import { AdminApiError, adminRpc, getAuthenticatorAssuranceLevel, inviteAdminMember, isMfaRequiredError, requireAdmin, signOutAdmin } from '@/lib/admin-auth';

interface Member {
  user_id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  invitation_status?: string | null;
  account_status?: string | null;
  expires_at?: string | null;
}

interface UpdateRow {
  success: boolean;
  user_id: string;
  role: string;
  is_active: boolean;
  error: string | null;
}

interface InviteAttempt {
  email: string;
  role: 'admin' | 'user';
  resend: boolean;
  requestId: string;
  memberId?: string;
}

function shouldRetainInviteAttempt(reason: unknown): boolean {
  if (reason instanceof AdminApiError) {
    return reason.code === 'reconciliation_required' || (reason.status !== null && reason.status >= 500);
  }
  return reason instanceof TypeError;
}

function AdminUsersManager() {
  const router = useRouter();
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('user');
  const [creating, setCreating] = useState(false);
  const [resendingUserId, setResendingUserId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [inviteRetry, setInviteRetry] = useState<InviteAttempt | null>(null);

  const loadMembers = useCallback(async () => {
    setLoading(true);
      setError(null);
      setMfaRequired(false);
      try {
       await requireAdmin();
       const assurance = await getAuthenticatorAssuranceLevel();
       if (assurance.currentLevel !== 'aal2') {
         setMfaRequired(true);
         return;
       }
       const rows = (await adminRpc('admin_list_members_onboarding', {})) as Member[];
      setMembers(Array.isArray(rows) ? rows : []);
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      if (reason instanceof Error && reason.message === 'Admin required') {
        router.replace('/admin/');
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al cargar usuarios.');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadMembers(), 0);
    return () => window.clearTimeout(timeout);
  }, [loadMembers]);

  const handleCreate = async () => {
    const attempt: InviteAttempt = {
      email: email.trim(),
      role: role as 'admin' | 'user',
      resend: false,
      requestId: globalThis.crypto.randomUUID(),
    };
    setCreating(true);
    setMessage(null);
    setError(null);
    try {
      await requireAdmin();
      const result = await inviteAdminMember(attempt.email, attempt.role, { requestId: attempt.requestId });
      setInviteRetry(null);
      setMessage(result.resent ? 'Invitación reenviada correctamente. Estado: pendiente.' : 'Invitación creada correctamente. Estado: pendiente; se envió el correo de acceso.');
      setEmail('');
      void loadMembers();
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      if (shouldRetainInviteAttempt(reason)) {
        setInviteRetry(attempt);
        const reference = reason instanceof AdminApiError ? reason.requestId || attempt.requestId : attempt.requestId;
        setError(`${reason instanceof Error ? reason.message : 'No se pudo confirmar la entrega.'} Referencia: ${reference}. Reintenta la misma operación para consultar su estado sin duplicar el envío.`);
      } else {
        setInviteRetry(null);
        setError(reason instanceof AdminApiError && reason.code === 'invalid_invitation'
          ? 'Ingresa un correo válido y selecciona un rol permitido.'
          : reason instanceof Error ? reason.message : 'Error al invitar al usuario.');
      }
    } finally {
      setCreating(false);
    }
  };

  const handleMemberUpdate = async (member: Member, updates: { role?: string; is_active?: boolean }, action: string) => {
    setError(null);
    setMessage(null);
    try {
      const rows = (await adminRpc('admin_update_member', {
        p_user_id: member.user_id,
        p_role: updates.role ?? null,
        p_is_active: updates.is_active ?? null,
        p_action: action,
      })) as UpdateRow[];
      const result = rows[0];
      if (!result?.success) throw new Error(result?.error || 'No se pudo actualizar la membresía.');
      setMessage('Membresía actualizada.');
      await loadMembers();
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      setError(reason instanceof Error ? reason.message : 'Error al actualizar la membresía.');
    }
  };

  const handleResend = async (member: Member) => {
    const attempt: InviteAttempt = {
      email: member.email,
      role: member.role as 'admin' | 'user',
      resend: true,
      requestId: globalThis.crypto.randomUUID(),
      memberId: member.user_id,
    };
    setResendingUserId(member.user_id);
    setMessage(null);
    setError(null);
    try {
      await requireAdmin();
      const result = await inviteAdminMember(attempt.email, attempt.role, { resend: true, requestId: attempt.requestId });
      setInviteRetry(null);
      setMessage(result.recovery_sent
        ? 'Correo de recuperación reenviado. Usa el enlace para definir la contraseña y luego inicia sesión en el panel.'
        : result.resent
          ? 'Invitación reenviada correctamente. Estado: pendiente.'
          : 'Correo de acceso enviado.');
      await loadMembers();
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      if (shouldRetainInviteAttempt(reason)) {
        setInviteRetry(attempt);
        const reference = reason instanceof AdminApiError ? reason.requestId || attempt.requestId : attempt.requestId;
        setError(`${reason instanceof Error ? reason.message : 'No se pudo confirmar la entrega.'} Referencia: ${reference}. Reintenta la misma operación para consultar su estado sin duplicar el envío.`);
      } else {
        setInviteRetry(null);
        setError(reason instanceof Error ? reason.message : 'Error al reenviar la invitación.');
      }
    } finally {
      setResendingUserId(null);
    }
  };

  const handleRetryInvite = async () => {
    if (!inviteRetry) return;
    const attempt = inviteRetry;
    setCreating(!attempt.resend);
    setResendingUserId(attempt.resend ? attempt.memberId || attempt.email : null);
    setMessage(null);
    setError(null);
    try {
      await requireAdmin();
      const result = await inviteAdminMember(attempt.email, attempt.role, {
        resend: attempt.resend,
        requestId: attempt.requestId,
      });
      setInviteRetry(null);
      setMessage(result.recovery_sent
        ? 'Correo de recuperación reenviado. Usa el enlace para definir la contraseña y luego inicia sesión en el panel.'
        : result.resent
          ? 'Invitación reenviada correctamente. Estado: pendiente.'
          : 'Invitación confirmada correctamente. Estado: pendiente.');
      if (!attempt.resend) setEmail('');
      await loadMembers();
    } catch (reason) {
      if (isMfaRequiredError(reason)) {
        setMfaRequired(true);
        return;
      }
      if (!shouldRetainInviteAttempt(reason)) setInviteRetry(null);
      const reference = reason instanceof AdminApiError ? reason.requestId || attempt.requestId : attempt.requestId;
      setError(`${reason instanceof Error ? reason.message : 'No se pudo confirmar la entrega.'} Referencia: ${reference}.`);
    } finally {
      setCreating(false);
      setResendingUserId(null);
    }
  };

  const handleLogout = async () => {
    await signOutAdmin();
    router.replace('/admin/login/');
  };

  const formatDate = (value: string | null | undefined) => value ? new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : 'No disponible';

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-8">
      <main className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Gestión de usuarios</h1>
            <p className="text-sm text-slate-600">Usuarios editoriales (admin / user)</p>
          </div>
          <div className="flex gap-2">
            <Link href="/admin/" className="text-sm font-medium text-brand-blue">Volver al panel</Link>
            <button type="button" onClick={handleLogout} className="text-sm font-medium text-slate-500">Cerrar sesión</button>
          </div>
        </div>

        {mfaRequired && <MfaRequiredCard onVerified={() => void loadMembers()} />}

        <Card className="p-6">
          <h2 className="text-lg font-semibold text-slate-900">Agregar usuario</h2>
          <p className="mt-1 text-xs text-slate-500">Invita por correo al usuario editorial y registra su membresía (admin/user).</p>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="member-email">Email</Label>
              <Input id="member-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="usuario@studiamatch.com" />
            </div>
            <div className="space-y-2">
              <Label id="member-role-label">Rol</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger aria-labelledby="member-role-label"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={() => void handleCreate()} disabled={creating || mfaRequired || !email || inviteRetry !== null} className="w-full">
                {creating ? 'Agregando...' : 'Agregar usuario'}
              </Button>
            </div>
          </div>
          {message && <p className="mt-4 text-sm text-green-700" role="status">{message}</p>}
          {error && <p className="mt-4 text-sm text-red-600" role="alert">{error}</p>}
          {inviteRetry && (
            <div className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-3" role="group" aria-label="Conciliación de invitación">
              <p className="text-sm text-amber-950">La entrega sigue sin confirmarse. Esta acción reutiliza la misma referencia y no repite el envío de correo.</p>
              <Button type="button" variant="outline" className="mt-2" disabled={creating || resendingUserId !== null || mfaRequired} onClick={() => void handleRetryInvite()}>
                {creating || resendingUserId !== null ? 'Consultando…' : 'Consultar/reintentar misma operación'}
              </Button>
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold text-slate-900">Usuarios existentes</h2>
          {loading ? (
            <p className="mt-4 text-sm text-slate-600">Cargando...</p>
          ) : members.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">No hay usuarios registrados.</p>
          ) : (
               <div
                 aria-label="Membresías existentes"
                 data-membership-scroll
                 role="region"
                 tabIndex={0}
                 onKeyDown={(event) => {
                   if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
                   const region = event.currentTarget;
                   const maxScroll = region.scrollWidth - region.clientWidth;
                   if (maxScroll <= 0) return;
                   const direction = event.key === 'ArrowRight' ? 1 : -1;
                   const distance = Math.max(48, Math.round(region.clientWidth * 0.75));
                   region.scrollLeft = Math.min(maxScroll, Math.max(0, region.scrollLeft + direction * distance));
                   event.preventDefault();
                 }}
                 className="mt-4 overflow-x-auto rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
               >
               <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                  <th scope="col" className="whitespace-nowrap px-3 py-2">Email</th>
                  <th scope="col" className="whitespace-nowrap px-3 py-2">Rol</th>
                  <th scope="col" className="whitespace-nowrap px-3 py-2">Estado</th>
                  <th scope="col" className="whitespace-nowrap px-3 py-2">Invitación</th>
                  <th scope="col" className="whitespace-nowrap px-3 py-2">Cuenta</th>
                  <th scope="col" className="whitespace-nowrap px-3 py-2">Expira</th>
                  <th scope="col" className="whitespace-nowrap px-3 py-2">Acciones</th>
                 </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.user_id} data-membership-row className="border-b border-slate-100">
                    <td className="whitespace-nowrap px-3 py-2">{member.email}</td>
                    <td className="whitespace-nowrap px-3 py-2">{member.role}</td>
                    <td className="whitespace-nowrap px-3 py-2">{member.is_active ? 'Activo' : 'Inactivo'}</td>
                    <td className="whitespace-nowrap px-3 py-2">{member.invitation_status || 'No expuesta'}</td>
                    <td className="whitespace-nowrap px-3 py-2">{member.account_status || (member.is_active ? 'ready (legacy)' : 'No expuesto')}</td>
                    <td className="whitespace-nowrap px-3 py-2">{formatDate(member.expires_at)}</td>
                    <td className="whitespace-nowrap px-3 py-2">
                      <div className="flex items-center gap-2">
                         {member.invitation_status === 'pending' && member.account_status === 'invited' && (
                           <Button type="button" variant="outline" size="sm" aria-label={`Reenviar invitación — ${member.email}`} disabled={mfaRequired || resendingUserId !== null || inviteRetry !== null} onClick={() => void handleResend(member)}>
                            {resendingUserId === member.user_id ? 'Reenviando…' : 'Reenviar invitación'}
                          </Button>
                        )}
                         <Button type="button" variant="outline" size="sm" aria-label={`${member.is_active ? 'Desactivar' : 'Activar'} — ${member.email}`} disabled={mfaRequired} onClick={() => { if (window.confirm(`¿Confirmar cambio de estado para ${member.email}?`)) void handleMemberUpdate(member, { is_active: !member.is_active }, member.is_active ? 'deactivation' : 'activation'); }}>
                         {member.is_active ? 'Desactivar' : 'Activar'}
                       </Button>
                         <Button type="button" variant="outline" size="sm" aria-label={`Hacer ${member.role === 'admin' ? 'user' : 'admin'} — ${member.email}`} disabled={mfaRequired} onClick={() => { if (window.confirm(`¿Cambiar rol de ${member.email}?`)) void handleMemberUpdate(member, { role: member.role === 'admin' ? 'user' : 'admin' }, 'role_change'); }}>
                         Hacer {member.role === 'admin' ? 'user' : 'admin'}
                       </Button>
                      </div>
                     </td>
                   </tr>
                ))}
               </tbody>
             </table>
             </div>
          )}
        </Card>
      </main>
    </div>
  );
}

export default function AdminUsersPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-slate-50"><p className="text-sm text-slate-600">Cargando...</p></div>}>
      <AdminUsersManager />
    </Suspense>
  );
}
