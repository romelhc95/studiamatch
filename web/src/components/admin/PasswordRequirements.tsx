'use client';

import { Check, Circle, ShieldCheck } from 'lucide-react';
import {
  getPasswordChecks,
  getPasswordStrength,
  PASSWORD_RULES,
  type PasswordRuleId,
} from '@/lib/password-policy';

interface PasswordRequirementsProps {
  id: string;
  password: string;
  confirmation: string;
}

export function PasswordRequirements({ id, password, confirmation }: PasswordRequirementsProps) {
  const checks = getPasswordChecks(password, confirmation);
  const strength = getPasswordStrength(checks);
  const progressWidth = `${(strength.score / PASSWORD_RULES.length) * 100}%`;

  return (
    <section id={id} className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4" aria-labelledby={`${id}-title`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-xl bg-brand-blue/10 text-brand-blue">
            <ShieldCheck className="size-4" aria-hidden="true" />
          </span>
          <div>
            <h3 id={`${id}-title`} className="text-sm font-semibold text-slate-800">Seguridad de la contraseña</h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">Se valida en tiempo real. La contraseña solo se envía a Supabase Auth.</p>
          </div>
        </div>
        <span className={`shrink-0 text-right text-xs font-semibold ${strength.tone === 'strong' ? 'text-emerald-700' : strength.tone === 'progress' ? 'text-amber-700' : 'text-slate-400'}`} aria-live="polite">
          {strength.label}
        </span>
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-200" aria-hidden="true">
        <div
          className={`h-full rounded-full transition-all duration-300 ${strength.tone === 'strong' ? 'bg-emerald-500' : strength.tone === 'progress' ? 'bg-amber-400' : 'bg-slate-300'}`}
          style={{ width: progressWidth }}
        />
      </div>

      <ul className="mt-4 grid gap-2 sm:grid-cols-2" aria-label="Requisitos de contraseña">
        {PASSWORD_RULES.map((rule) => (
          <Requirement key={rule.id} id={rule.id} label={rule.label} satisfied={checks[rule.id]} />
        ))}
      </ul>

      <div className="mt-3 border-t border-slate-200 pt-3" aria-live="polite">
        {confirmation ? (
          <p className={`flex items-center gap-2 text-xs font-medium ${checks.matches ? 'text-emerald-700' : 'text-red-600'}`}>
            {checks.matches ? <Check className="size-3.5" aria-hidden="true" /> : <Circle className="size-3.5" aria-hidden="true" />}
            {checks.matches ? 'Las contraseñas coinciden.' : 'Las contraseñas todavía no coinciden.'}
          </p>
        ) : (
          <p className="text-xs text-slate-500">Completa ambos campos para habilitar el botón.</p>
        )}
      </div>
    </section>
  );
}

function Requirement({ id, label, satisfied }: { id: PasswordRuleId; label: string; satisfied: boolean }) {
  return (
    <li data-rule={id} data-satisfied={satisfied} aria-label={`${label}: ${satisfied ? 'cumplido' : 'pendiente'}`} className={`flex items-center gap-2 text-xs transition-colors ${satisfied ? 'text-emerald-700' : 'text-slate-500'}`}>
      <span className={`flex size-4 shrink-0 items-center justify-center rounded-full border ${satisfied ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-300 bg-white text-transparent'}`}>
        <Check className="size-2.5" strokeWidth={3} aria-hidden="true" />
      </span>
      <span>{label}</span>
      <span className="sr-only">{satisfied ? 'Cumplido' : 'Pendiente'}</span>
    </li>
  );
}
