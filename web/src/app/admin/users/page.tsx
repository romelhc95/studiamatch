'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { adminRpc, inviteAdminMember, requireAdmin, signOutAdmin } from '@/lib/admin-auth';

interface Member {
  user_id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface UpdateRow {
  success: boolean;
  user_id: string;
  role: string;
  is_active: boolean;
  error: string | null;
}

function AdminUsersManager() {
  const router = useRouter();
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('user');
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadMembers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await requireAdmin();
      const rows = (await adminRpc('admin_list_members', {})) as Member[];
      setMembers(Array.isArray(rows) ? rows : []);
    } catch (reason) {
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
    setCreating(true);
    setMessage(null);
    setError(null);
    try {
      await requireAdmin();
      await inviteAdminMember(email, role as 'admin' | 'user');
      setMessage('Usuario invitado correctamente. Se le envió un correo para confirmar su acceso.');
      setEmail('');
      void loadMembers();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Error al invitar al usuario.');
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
      setError(reason instanceof Error ? reason.message : 'Error al actualizar la membresía.');
    }
  };

  const handleLogout = async () => {
    await signOutAdmin();
    router.replace('/admin/login/');
  };

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

        <Card className="p-6">
          <h2 className="text-lg font-semibold text-slate-900">Agregar usuario</h2>
          <p className="mt-1 text-xs text-slate-500">Invita por correo al usuario editorial y registra su membresía (admin/user).</p>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="member-email">Email</Label>
              <Input id="member-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="usuario@studiamatch.com" />
            </div>
            <div className="space-y-2">
              <Label>Rol</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={() => void handleCreate()} disabled={creating || !email} className="w-full">
                {creating ? 'Agregando...' : 'Agregar usuario'}
              </Button>
            </div>
          </div>
          {message && <p className="mt-4 text-sm text-green-700">{message}</p>}
          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold text-slate-900">Usuarios existentes</h2>
          {loading ? (
            <p className="mt-4 text-sm text-slate-600">Cargando...</p>
          ) : members.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">No hay usuarios registrados.</p>
          ) : (
            <table className="mt-4 w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                  <th className="py-2">Email</th>
                  <th className="py-2">Rol</th>
                   <th className="py-2">Estado</th>
                   <th className="py-2">Acciones</th>
                 </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.user_id} data-membership-row className="border-b border-slate-100">
                    <td className="py-2">{member.email}</td>
                    <td className="py-2">{member.role}</td>
                     <td className="py-2">{member.is_active ? 'Activo' : 'Inactivo'}</td>
                     <td className="space-x-2 py-2">
                       <Button type="button" variant="outline" size="sm" onClick={() => { if (window.confirm('¿Confirmar cambio de estado?')) void handleMemberUpdate(member, { is_active: !member.is_active }, member.is_active ? 'deactivation' : 'activation'); }}>
                         {member.is_active ? 'Desactivar' : 'Activar'}
                       </Button>
                       <Button type="button" variant="outline" size="sm" onClick={() => { if (window.confirm('¿Cambiar rol de esta membresía?')) void handleMemberUpdate(member, { role: member.role === 'admin' ? 'user' : 'admin' }, 'role_change'); }}>
                         Hacer {member.role === 'admin' ? 'user' : 'admin'}
                       </Button>
                     </td>
                   </tr>
                ))}
              </tbody>
            </table>
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
