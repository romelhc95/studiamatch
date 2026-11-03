// StudIAMatch-Docs: .context/componentes/admin_portal.md#admin-session-guard
'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useRef } from 'react';
import {
  ADMIN_ACTIVITY_EVENT_KEY,
  ADMIN_IDLE_TIMEOUT_MS,
  ADMIN_LOGOUT_EVENT_KEY,
  getAdminLastActivity,
  getAuthSession,
  recordAdminActivity,
  signOutAdmin,
  touchAdminSession,
} from '@/lib/admin-auth';

function isProtectedAdminPath(pathname: string | null): boolean {
  return pathname === '/admin' || pathname === '/admin/' || pathname?.startsWith('/admin/edit') === true || pathname?.startsWith('/admin/users') === true;
}

export default function AdminSessionGuard() {
  const pathname = usePathname();
  const router = useRouter();
  const loggingOut = useRef(false);
  const sessionGeneration = useRef(0);

  useEffect(() => {
    if (!isProtectedAdminPath(pathname)) return undefined;

    let active = true;
    let activityTimer: number | undefined;
    let lastRecordedActivity = 0;
    let lastServerTouch = 0;
    let sessionValidated = false;
    let currentGeneration = 0;

    const goToLogin = () => {
      if (active) router.replace('/admin/login/');
    };

    const expireSession = async (broadcast: boolean) => {
      if (!active || !sessionValidated || currentGeneration !== sessionGeneration.current || loggingOut.current) return;
      loggingOut.current = true;
      sessionValidated = false;
      await signOutAdmin({ broadcast }).catch(() => undefined);
      if (!active || currentGeneration !== sessionGeneration.current) return;
      goToLogin();
    };

    const scheduleExpiryCheck = () => {
      if (activityTimer !== undefined) window.clearTimeout(activityTimer);
      if (!active || !sessionValidated || loggingOut.current) return;
      const lastActivity = getAdminLastActivity();
      const remaining = lastActivity === null ? ADMIN_IDLE_TIMEOUT_MS : ADMIN_IDLE_TIMEOUT_MS - (Date.now() - lastActivity);
      activityTimer = window.setTimeout(() => {
        const currentLastActivity = getAdminLastActivity();
        if (currentLastActivity !== null && Date.now() - currentLastActivity >= ADMIN_IDLE_TIMEOUT_MS) {
          void expireSession(true);
          return;
        }
        scheduleExpiryCheck();
      }, Math.max(250, Math.min(remaining, 1000)));
    };

    const markActivity = () => {
      if (!active || !sessionValidated || currentGeneration !== sessionGeneration.current || loggingOut.current) return;
      const now = Date.now();
      if (now - lastRecordedActivity < 1000) return;
      const lastActivity = getAdminLastActivity();
      if (lastActivity !== null && now - lastActivity >= ADMIN_IDLE_TIMEOUT_MS) {
        void expireSession(true);
        return;
      }
      lastRecordedActivity = now;
      recordAdminActivity(now);
      if (now - lastServerTouch >= 60_000) {
        lastServerTouch = now;
        void touchAdminSession().catch(() => undefined);
      }
      scheduleExpiryCheck();
    };

    const handleStorage = (event: StorageEvent) => {
      if (event.key === ADMIN_LOGOUT_EVENT_KEY && event.newValue) {
        if (sessionValidated) {
          void expireSession(false);
        } else {
          sessionGeneration.current += 1;
          loggingOut.current = true;
          if (activityTimer !== undefined) window.clearTimeout(activityTimer);
          goToLogin();
        }
        return;
      }
      if (event.key === ADMIN_ACTIVITY_EVENT_KEY && sessionValidated) scheduleExpiryCheck();
    };

    const activityEvents: Array<keyof WindowEventMap> = ['pointerdown', 'keydown', 'touchstart', 'scroll', 'focus'];
    for (const eventName of activityEvents) window.addEventListener(eventName, markActivity, { passive: true });
    window.addEventListener('storage', handleStorage);

    const initialize = async () => {
      const requestGeneration = sessionGeneration.current;
      const session = await getAuthSession().catch(() => null);
      if (!active || requestGeneration !== sessionGeneration.current) return;
      if (!session) {
        goToLogin();
        return;
      }

      currentGeneration = requestGeneration + 1;
      sessionGeneration.current = currentGeneration;
      sessionValidated = true;
      loggingOut.current = false;

      const lastActivity = getAdminLastActivity();
      if (lastActivity !== null && Date.now() - lastActivity >= ADMIN_IDLE_TIMEOUT_MS) {
        await expireSession(true);
        return;
      }
      markActivity();
      scheduleExpiryCheck();
    };

    void initialize();

    return () => {
      active = false;
      sessionValidated = false;
      if (activityTimer !== undefined) window.clearTimeout(activityTimer);
      for (const eventName of activityEvents) window.removeEventListener(eventName, markActivity);
      window.removeEventListener('storage', handleStorage);
    };
  }, [pathname, router]);

  return null;
}
