import { isIsoDate, isNonEmptyString, isObject, isSemver, makeReport } from './common.mjs';

const FAILURE_TYPES = new Set(['miss', 'false-positive', 'misroute']);
const STATUSES = new Set(['open', 'in_progress', 'closed', 'reopened']);
const FORBIDDEN_KEYS = /^(?:messageBody|prompt|rawContent|session|sessionBody|token|cookie|secret)$/i;

function findForbiddenKeys(value, path = '$', found = []) {
  if (Array.isArray(value)) {
    value.forEach((item, index) => findForbiddenKeys(item, `${path}[${index}]`, found));
  } else if (isObject(value)) {
    for (const [key, child] of Object.entries(value)) {
      if (FORBIDDEN_KEYS.test(key)) found.push(`${path}.${key}`);
      findForbiddenKeys(child, `${path}.${key}`, found);
    }
  }
  return found;
}

function requireString(value, path, errors) {
  if (!isNonEmptyString(value)) errors.push(`${path} must be a non-empty string`);
}

function validateCorrection(correction, path, errors) {
  if (!isObject(correction)) {
    errors.push(`${path} is required for a closed routing event`);
    return;
  }
  for (const key of ['targetPath', 'changeSummary', 'beforeHash', 'afterHash', 'verificationCommand']) {
    requireString(correction[key], `${path}.${key}`, errors);
  }
  if (!isIsoDate(correction.appliedAt)) errors.push(`${path}.appliedAt must be an ISO date or datetime`);
  if (!/^[a-f0-9]{64}$/i.test(correction.beforeHash ?? '')) errors.push(`${path}.beforeHash must be SHA-256`);
  if (!/^[a-f0-9]{64}$/i.test(correction.afterHash ?? '')) errors.push(`${path}.afterHash must be SHA-256`);
  if (correction.beforeHash === correction.afterHash) errors.push(`${path} beforeHash and afterHash must differ`);
  if (correction.verificationResult !== 'PASS') errors.push(`${path}.verificationResult must be PASS for closed status`);
}

export function validateRouteLedger(ledger) {
  const errors = [];
  const warnings = [];
  const entries = Array.isArray(ledger?.entries) ? ledger.entries : [];

  if (!isSemver(ledger?.schemaVersion)) errors.push('schemaVersion must be a semantic version');
  if (!Array.isArray(ledger?.entries)) errors.push('entries must be an array');
  if (entries.length === 0) warnings.push('route ledger has no observed failure events');

  const seen = new Set();
  const safeEvents = [];
  for (const [index, entry] of entries.entries()) {
    const path = `entries[${index}]`;
    if (!isObject(entry)) {
      errors.push(`${path} must be an object`);
      continue;
    }
    requireString(entry.eventId, `${path}.eventId`, errors);
    if (seen.has(entry.eventId)) errors.push(`${path}.eventId is duplicated: ${entry.eventId}`);
    seen.add(entry.eventId);
    if (!isIsoDate(entry.observedAt)) errors.push(`${path}.observedAt must be an ISO date or datetime`);
    requireString(entry.taskId, `${path}.taskId`, errors);
    requireString(entry.expectedRoute, `${path}.expectedRoute`, errors);
    if (!FAILURE_TYPES.has(entry.failureType)) errors.push(`${path}.failureType must be miss|false-positive|misroute`);
    if (!STATUSES.has(entry.status)) errors.push(`${path}.status must be open|in_progress|closed|reopened`);
    if (entry.privacy !== 'metadata-only') errors.push(`${path}.privacy must be metadata-only`);
    if (!Array.isArray(entry.evidence) || entry.evidence.length === 0 || entry.evidence.some((item) => !isNonEmptyString(item))) {
      errors.push(`${path}.evidence must contain non-empty metadata references`);
    }
    if (entry.failureType === 'miss') {
      if (isNonEmptyString(entry.actualRoute)) errors.push(`${path}.actualRoute must be empty for a miss`);
    } else {
      requireString(entry.actualRoute, `${path}.actualRoute`, errors);
      if (entry.actualRoute === entry.expectedRoute) errors.push(`${path}.actualRoute must differ from expectedRoute`);
    }
    if (entry.status === 'closed') validateCorrection(entry.correction, `${path}.correction`, errors);
    if (entry.status === 'reopened') requireString(entry.reopenReason, `${path}.reopenReason`, errors);

    safeEvents.push({
      eventId: entry.eventId ?? null,
      taskId: entry.taskId ?? null,
      failureType: entry.failureType ?? null,
      expectedRoute: entry.expectedRoute ?? null,
      actualRoute: entry.actualRoute ?? null,
      status: entry.status ?? null,
    });
  }

  for (const keyPath of findForbiddenKeys(ledger)) errors.push(`forbidden raw/sensitive field: ${keyPath}`);
  safeEvents.sort((left, right) => String(left.eventId).localeCompare(String(right.eventId)));

  const statusCounts = Object.fromEntries([...STATUSES].map((status) => [status, entries.filter((entry) => entry?.status === status).length]));
  const failureCounts = Object.fromEntries([...FAILURE_TYPES].map((type) => [type, entries.filter((entry) => entry?.failureType === type).length]));
  return makeReport('route-ledger', errors, warnings, {
    eventCount: entries.length,
    statusCounts,
    failureCounts,
    verifiedClosedCount: entries.filter((entry) => entry?.status === 'closed' && entry?.correction?.verificationResult === 'PASS').length,
  }, { events: safeEvents });
}
