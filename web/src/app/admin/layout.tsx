import type { Metadata } from 'next';
import AdminSessionGuard from '@/components/admin/AdminSessionGuard';

export const metadata: Metadata = {
  title: 'Admin - StudIAMatch',
  description: 'Panel administrativo editorial',
  robots: { index: false, follow: false },
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AdminSessionGuard />
      {children}
    </>
  );
}
