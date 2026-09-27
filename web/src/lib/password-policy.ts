export const PASSWORD_MIN_LENGTH = 12;

// Keep this allow-list aligned with Supabase Auth's strongest password
// requirement. The browser never sends this value anywhere; it only provides
// immediate feedback before Auth performs the authoritative validation.
const PASSWORD_SYMBOLS = "!@#$%^&*()_+-=[]{};'\\:\"|<>?,./`~";

export type PasswordRuleId = 'length' | 'lowercase' | 'uppercase' | 'number' | 'symbol';

export interface PasswordChecks {
  length: boolean;
  lowercase: boolean;
  uppercase: boolean;
  number: boolean;
  symbol: boolean;
  matches: boolean;
}

export const PASSWORD_RULES: ReadonlyArray<{ id: PasswordRuleId; label: string }> = [
  { id: 'length', label: `Al menos ${PASSWORD_MIN_LENGTH} caracteres` },
  { id: 'uppercase', label: 'Una letra mayúscula' },
  { id: 'lowercase', label: 'Una letra minúscula' },
  { id: 'number', label: 'Un número' },
  { id: 'symbol', label: 'Un símbolo: ! @ # $ % …' },
];

export function getPasswordChecks(password: string, confirmation = ''): PasswordChecks {
  return {
    // Count Unicode code points so the UI's notion of "characters" is not
    // affected by UTF-16 surrogate pairs. Supabase remains authoritative.
    length: Array.from(password).length >= PASSWORD_MIN_LENGTH,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    number: /[0-9]/.test(password),
    symbol: Array.from(password).some((character) => PASSWORD_SYMBOLS.includes(character)),
    matches: Array.from(password).length > 0 && password === confirmation,
  };
}

export function isPasswordValid(password: string, confirmation = ''): boolean {
  return hasPasswordRequirements(password) && getPasswordChecks(password, confirmation).matches;
}

export function hasPasswordRequirements(password: string): boolean {
  const checks = getPasswordChecks(password);
  return PASSWORD_RULES.every(({ id }) => checks[id]);
}

export function getPasswordValidationMessage(password: string, confirmation = ''): string | null {
  if (!password && !confirmation) return 'Ingresa y confirma tu contraseña.';

  const checks = getPasswordChecks(password, confirmation);
  if (!checks.length) return `La contraseña debe tener al menos ${PASSWORD_MIN_LENGTH} caracteres.`;
  if (!checks.lowercase || !checks.uppercase || !checks.number || !checks.symbol) {
    return 'Completa todos los requisitos de seguridad indicados.';
  }
  if (!confirmation) return 'Confirma tu contraseña.';
  if (!checks.matches) return 'Las contraseñas no coinciden.';
  return null;
}

export function getPasswordStrength(checks: PasswordChecks): {
  score: number;
  label: string;
  tone: 'neutral' | 'progress' | 'strong';
} {
  const score = PASSWORD_RULES.reduce((total, { id }) => total + (checks[id] ? 1 : 0), 0);
  if (score === 0) return { score, label: 'Sin evaluar', tone: 'neutral' };
  if (score < PASSWORD_RULES.length) return { score, label: score >= 3 ? 'Casi lista' : 'En progreso', tone: 'progress' };
  return { score, label: checks.matches ? 'Lista para guardar' : 'Requisitos completos', tone: 'strong' };
}
