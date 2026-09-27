'use client';

import { Eye, EyeOff } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { PASSWORD_MIN_LENGTH } from '@/lib/password-policy';

interface PasswordInputProps {
  id: string;
  label: string;
  value: string;
  visible: boolean;
  onChange: (value: string) => void;
  onToggle: () => void;
  describedBy?: string;
  disabled?: boolean;
  invalid?: boolean;
}

export function PasswordInput({
  id,
  label,
  value,
  visible,
  onChange,
  onToggle,
  describedBy,
  disabled = false,
  invalid = false,
}: PasswordInputProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-medium text-slate-700">{label}</label>
      <div className="relative">
        <Input
          id={id}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          autoComplete="new-password"
          minLength={PASSWORD_MIN_LENGTH}
          required
          disabled={disabled}
          aria-describedby={describedBy}
          aria-invalid={invalid || undefined}
          className="h-11 pr-12"
        />
        <button
          type="button"
          className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-slate-500 transition-colors hover:text-brand-blue focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/50 disabled:cursor-not-allowed disabled:opacity-50"
          onClick={onToggle}
          aria-label={visible ? `Ocultar ${label.toLowerCase()}` : `Mostrar ${label.toLowerCase()}`}
          aria-pressed={visible}
          disabled={disabled}
        >
          {visible ? <EyeOff className="size-4" aria-hidden="true" /> : <Eye className="size-4" aria-hidden="true" />}
        </button>
      </div>
    </div>
  );
}
