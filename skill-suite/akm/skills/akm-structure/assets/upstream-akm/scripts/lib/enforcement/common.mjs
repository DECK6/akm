import { createHash } from 'node:crypto';

const PLACEHOLDER_RE = /(?:<[^>]+>|\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b)/i;
const FORBIDDEN_PROMPT_PATH_TOKENS = new Set([
  'auth', 'oauth', 'token', 'tokens', 'cookie', 'cookies', 'session', 'sessions', 'log', 'logs',
]);

export function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

export function isSemver(value) {
  return typeof value === 'string' && /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(value);
}

export function isIsoDate(value) {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2}))?$/.test(value);
}

export function hasPlaceholder(value) {
  if (typeof value === 'string') return PLACEHOLDER_RE.test(value);
  if (Array.isArray(value)) return value.some(hasPlaceholder);
  if (isObject(value)) return Object.values(value).some(hasPlaceholder);
  return false;
}

export function sha256(content) {
  return createHash('sha256').update(content).digest('hex');
}

export function forbiddenPromptPathReason(path) {
  const normalized = String(path).replaceAll('\\', '/').toLowerCase();
  const parts = normalized.split('/').filter(Boolean);
  const base = parts.at(-1) ?? '';
  if (base === '.env' || base.startsWith('.env.')) return '.env files are excluded';
  if (/\.(?:db|sqlite|sqlite3|log)$/.test(base)) return 'state databases and logs are excluded';
  for (const part of parts) {
    const tokens = part.split(/[._-]+/).filter(Boolean);
    const forbidden = tokens.find((token) => FORBIDDEN_PROMPT_PATH_TOKENS.has(token));
    if (forbidden) return `path token "${forbidden}" is excluded`;
  }
  return null;
}

export function makeReport(mode, errors, warnings, summary = {}, data = {}) {
  return {
    schemaVersion: '1.0.0',
    mode,
    ok: errors.length === 0,
    errors,
    warnings,
    summary,
    data,
  };
}
