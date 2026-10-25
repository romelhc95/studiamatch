const LOCAL_PATH_QUERY = /(^|[^A-Za-z0-9._~/-])((?:\/)?[A-Za-z0-9._~/-]+)[?#][^\s"'<>\x60]*/g;
const QUERY_OR_FRAGMENT = /[?#][^\s"'<>\x60]+/g;
const SENSITIVE_PATH_SEGMENT = /^(?:[0-9a-fA-F-]{32,}|(?=[A-Za-z0-9_+\/=\-]{32,}$)(?=.*[A-Z])(?=.*[a-z])(?=.*\d)[A-Za-z0-9_+\/=\-]+|(?=[A-Za-z0-9_+\/=\-]{32,}$)(?=.*[A-Za-z])(?=.*[+\/=])[A-Za-z0-9_+\/=\-]+|(?:[A-Za-z0-9._~-]{8,}\.){2}[A-Za-z0-9._~-]{8,})$/;
const SHORT_MIXED_TOKEN_PATH_SEGMENT = /^(?=.{12,23}$)(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9._~+/-]+$/;
const SHORT_LOWERCASE_TOKEN_PATH_SEGMENT = /^[a-z0-9]{12,23}$/;
const MIN_OPAQUE_PATH_SEGMENT_LENGTH = 24;
const OPAQUE_PATH_SEGMENT = /(^|\/)([^/\s?#"'<>\x60]{12,})(?=(?:\/|[?#\s"'<>\x60]|$))/g;
const ADMIN_AUTH_CALLBACK_SEGMENT = /(^|[^A-Za-z0-9._~-])(?:\/|%2f)?admin(?:\/|%2f)auth(?:\/|%2f)callback(?:(?:\/|%2f)[^/\s?#"'<>\x60]+)+/gi;
const MAX_PATH_PERCENT_DECODING_DEPTH = 8;

function hasAdminAuthCallbackPath(pathname) {
  let candidate = pathname;
  for (let depth = 0; depth <= MAX_PATH_PERCENT_DECODING_DEPTH; depth += 1) {
    if (/(?:^|\/)admin\/auth\/callback(?:\/|$)/i.test(candidate)) return true;
    try {
      const decoded = decodeURIComponent(candidate);
      if (decoded === candidate) return false;
      candidate = decoded;
    } catch {
      return false;
    }
  }
  return false;
}

function isSensitivePathSegment(segment) {
  let candidate = segment;
  for (let depth = 0; depth < MAX_PATH_PERCENT_DECODING_DEPTH; depth += 1) {
    if (SENSITIVE_PATH_SEGMENT.test(candidate)
      || SHORT_MIXED_TOKEN_PATH_SEGMENT.test(candidate)
      || SHORT_LOWERCASE_TOKEN_PATH_SEGMENT.test(candidate)) return true;
    try {
      const decoded = decodeURIComponent(candidate);
      if (decoded === candidate) break;
      candidate = decoded;
    } catch {
      return true;
    }
  }
  if (SENSITIVE_PATH_SEGMENT.test(candidate)
    || SHORT_MIXED_TOKEN_PATH_SEGMENT.test(candidate)
    || SHORT_LOWERCASE_TOKEN_PATH_SEGMENT.test(candidate)) return true;
  // Any unresolved opaque segment at or beyond the safe decode bound is
  // redacted, including slug-shaped and lowercase/alphanumeric tokens.
  return segment.length >= MIN_OPAQUE_PATH_SEGMENT_LENGTH
    || candidate.length >= MIN_OPAQUE_PATH_SEGMENT_LENGTH;
}

function safePathname(pathname) {
  if (hasAdminAuthCallbackPath(pathname)) return '/admin/auth/callback/[REDACTED]';
  const segments = pathname.split('/');
  return segments.map((segment) => isSensitivePathSegment(segment) ? '[REDACTED]' : segment).join('/');
}

export function safeLocalRequest(value, localOrigins) {
  try {
    const origins = Array.isArray(localOrigins) ? localOrigins : [];
    if (origins.length === 0) return { origin: 'invalid', path: '[invalid]' };
    const parsed = new URL(value, origins[0]);
    const allowedOrigins = new Set(origins.map((origin) => new URL(origin).origin));
    if (!allowedOrigins.has(parsed.origin)) return { origin: 'external', path: '[external]' };
    const originIndex = origins.findIndex((origin) => new URL(origin).origin === parsed.origin);
    return { origin: `local-${originIndex}`, path: safePathname(parsed.pathname || '/') };
  } catch {
    return { origin: 'invalid', path: '[invalid]' };
  }
}

export function safeLocalPath(value, localOrigins) {
  return safeLocalRequest(value, localOrigins).path;
}

export function safeLocalOrigin(value, localOrigins) {
  return safeLocalRequest(value, localOrigins).origin;
}

export function sanitize(value, localOrigins) {
  return String(value ?? '')
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, 'Bearer [REDACTED]')
    .replace(/(?:access|refresh)[_-]?token["'\s:=]+[A-Za-z0-9._~+/=-]+/gi, 'token=[REDACTED]')
    .replace(/https?:\/\/[^\s"'<>`]+/gi, (candidate) => safeLocalPath(candidate, localOrigins))
    .replace(ADMIN_AUTH_CALLBACK_SEGMENT, '$1/admin/auth/callback/[REDACTED]')
    .replace(LOCAL_PATH_QUERY, '$1[LOCAL_PATH]')
    .replace(OPAQUE_PATH_SEGMENT, (match, prefix, segment) => `${prefix}${isSensitivePathSegment(segment) ? '[REDACTED]' : segment}`)
    .replace(QUERY_OR_FRAGMENT, '[QUERY]')
    .slice(0, 4000);
}
