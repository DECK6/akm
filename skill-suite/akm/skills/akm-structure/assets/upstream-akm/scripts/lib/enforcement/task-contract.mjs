import { hasPlaceholder, isNonEmptyString, isObject, isSemver, makeReport } from './common.mjs';

const INPUT_VERIFY = new Set(['exists', 'http', 'readback']);
const SOURCE_ROLES = new Set(['source-of-truth', 'support', 'authorial-synthesis']);
const OWNER_RE = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const REQUIRED_SECURITY = ['auth', 'token', 'cookie', 'session-db', 'secret'];
const INTERNAL_BLOCKER_RE = /(?:PATCH_NEEDED|\binternal\b|\blint(?:ing)?\b|\b(?:unit|integration|regression) test\b|\bcode review\b|\bverification (?:gate|failure|pending)\b)/i;
const ROOT_FIELDS = new Set([
  'contractVersion', 'taskId', 'purpose', 'inputs', 'outputs', 'canonicalPath',
  'format', 'sources', 'owner', 'failureHandling', 'completion', 'verification',
  'runtime', 'nonGoals', 'securityExclusions', 'blockers',
]);

function rejectUnexpectedFields(value, allowed, path, errors) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) errors.push(`${path}.${key} is an unexpected field`);
  }
}

function requireString(value, path, errors) {
  if (!isNonEmptyString(value)) errors.push(`${path} must be a non-empty string`);
}

function requireArray(value, path, errors, { min = 0 } = {}) {
  if (!Array.isArray(value)) {
    errors.push(`${path} must be an array`);
    return false;
  }
  if (value.length < min) errors.push(`${path} must contain at least ${min} item(s)`);
  return true;
}

function requireStringArray(value, path, errors, { min = 0 } = {}) {
  if (!requireArray(value, path, errors, { min })) return;
  value.forEach((item, index) => requireString(item, `${path}[${index}]`, errors));
}

export function validateTaskContract(contract) {
  const errors = [];
  const warnings = [];

  if (!isObject(contract)) return makeReport('contract-lint', ['contract must be a JSON object'], [], {}, {});
  rejectUnexpectedFields(contract, ROOT_FIELDS, '$', errors);
  if (!isSemver(contract.contractVersion)) errors.push('contractVersion must be a semantic version');
  requireString(contract.taskId, 'taskId', errors);
  requireString(contract.purpose, 'purpose', errors);

  if (requireArray(contract.inputs, 'inputs', errors, { min: 1 })) {
    contract.inputs.forEach((input, index) => {
      if (!isObject(input)) {
        errors.push(`inputs[${index}] must be an object`);
        return;
      }
      rejectUnexpectedFields(input, new Set(['path', 'required', 'verify']), `inputs[${index}]`, errors);
      requireString(input.path, `inputs[${index}].path`, errors);
      if (typeof input.required !== 'boolean') errors.push(`inputs[${index}].required must be boolean`);
      if (!INPUT_VERIFY.has(input.verify)) errors.push(`inputs[${index}].verify must be exists|http|readback`);
    });
  }

  if (requireArray(contract.outputs, 'outputs', errors, { min: 1 })) {
    contract.outputs.forEach((output, index) => {
      if (!isObject(output)) {
        errors.push(`outputs[${index}] must be an object`);
        return;
      }
      rejectUnexpectedFields(output, new Set(['path', 'kind', 'required']), `outputs[${index}]`, errors);
      requireString(output.path, `outputs[${index}].path`, errors);
      requireString(output.kind, `outputs[${index}].kind`, errors);
      if (typeof output.required !== 'boolean') errors.push(`outputs[${index}].required must be boolean`);
    });
  }

  requireString(contract.canonicalPath, 'canonicalPath', errors);
  if (isNonEmptyString(contract.canonicalPath) && Array.isArray(contract.outputs)) {
    const canonicalMatches = contract.outputs.filter((output) => output?.path === contract.canonicalPath);
    if (canonicalMatches.length !== 1) {
      errors.push('canonicalPath must match exactly one declared output path');
    } else if (canonicalMatches[0].required !== true) {
      errors.push('canonicalPath output must be required');
    }
  }

  requireStringArray(contract.format, 'format', errors, { min: 1 });

  if (requireArray(contract.sources, 'sources', errors, { min: 1 })) {
    contract.sources.forEach((source, index) => {
      if (!isObject(source)) {
        errors.push(`sources[${index}] must be an object`);
        return;
      }
      rejectUnexpectedFields(source, new Set(['ref', 'role']), `sources[${index}]`, errors);
      requireString(source.ref, `sources[${index}].ref`, errors);
      if (!SOURCE_ROLES.has(source.role)) {
        errors.push(`sources[${index}].role must be source-of-truth|support|authorial-synthesis`);
      }
    });
  }

  if (!isObject(contract.owner)) errors.push('owner must be an object');
  else {
    rejectUnexpectedFields(contract.owner, new Set(['primary', 'handoff']), 'owner', errors);
    if (!isNonEmptyString(contract.owner.primary) || !OWNER_RE.test(contract.owner.primary)) {
      errors.push('owner.primary must be a portable identifier using letters, numbers, dot, underscore, colon, or hyphen');
    }
    requireString(contract.owner.handoff, 'owner.handoff', errors);
  }

  if (!isObject(contract.failureHandling)) errors.push('failureHandling must be an object');
  else {
    rejectUnexpectedFields(
      contract.failureHandling,
      new Set(['blockedWhen', 'holdWhen', 'preserve']),
      'failureHandling',
      errors,
    );
    requireStringArray(contract.failureHandling.blockedWhen, 'failureHandling.blockedWhen', errors);
    requireStringArray(contract.failureHandling.holdWhen, 'failureHandling.holdWhen', errors);
    requireStringArray(contract.failureHandling.preserve, 'failureHandling.preserve', errors, { min: 1 });
    for (const blocker of contract.failureHandling.blockedWhen ?? []) {
      if (INTERNAL_BLOCKER_RE.test(blocker)) {
        errors.push(`failureHandling.blockedWhen contains an internal gate: ${blocker}`);
      }
    }
  }

  if (!isObject(contract.completion)) errors.push('completion must be an object');
  else {
    rejectUnexpectedFields(contract.completion, new Set(['required', 'optional']), 'completion', errors);
    requireStringArray(contract.completion.required, 'completion.required', errors, { min: 1 });
    requireStringArray(contract.completion.optional, 'completion.optional', errors);
  }

  if (requireArray(contract.verification, 'verification', errors, { min: 1 })) {
    contract.verification.forEach((verification, index) => {
      if (!isObject(verification)) {
        errors.push(`verification[${index}] must be an object`);
        return;
      }
      rejectUnexpectedFields(
        verification,
        new Set(['command', 'expectedExit', 'readback']),
        `verification[${index}]`,
        errors,
      );
      requireString(verification.command, `verification[${index}].command`, errors);
      if (!Number.isInteger(verification.expectedExit)) {
        errors.push(`verification[${index}].expectedExit must be an integer`);
      }
      requireString(verification.readback, `verification[${index}].readback`, errors);
    });
  }

  if (Array.isArray(contract.outputs) && Array.isArray(contract.verification)) {
    for (const output of contract.outputs.filter((item) => item?.required === true && isNonEmptyString(item.path))) {
      if (!contract.verification.some((item) => item?.readback === output.path)) {
        errors.push(`required output lacks exact verification readback: ${output.path}`);
      }
    }
  }

  if (!isObject(contract.runtime)) errors.push('runtime must be an object');
  else {
    rejectUnexpectedFields(contract.runtime, new Set(['maxSeconds', 'goalMode']), 'runtime', errors);
    if (!Number.isInteger(contract.runtime.maxSeconds) || contract.runtime.maxSeconds < 1 || contract.runtime.maxSeconds > 5400) {
      errors.push('runtime.maxSeconds must be an integer from 1 to 5400 for bounded work');
    }
    if (contract.runtime.goalMode !== false) errors.push('runtime.goalMode must be false for bounded work');
  }

  requireStringArray(contract.nonGoals, 'nonGoals', errors, { min: 1 });
  requireStringArray(contract.securityExclusions, 'securityExclusions', errors, { min: REQUIRED_SECURITY.length });
  if (Array.isArray(contract.securityExclusions)) {
    const normalized = new Set(contract.securityExclusions.map((item) => String(item).trim().toLowerCase()));
    for (const required of REQUIRED_SECURITY) {
      if (!normalized.has(required)) errors.push(`securityExclusions must include "${required}"`);
    }
  }

  requireStringArray(contract.blockers, 'blockers', errors);
  for (const blocker of contract.blockers ?? []) {
    if (INTERNAL_BLOCKER_RE.test(blocker)) errors.push(`blockers contains an internal gate: ${blocker}`);
  }

  if (hasPlaceholder(contract)) errors.push('contract contains placeholder text (for example <...>, TODO, TBD, or FIXME)');

  return makeReport('contract-lint', errors, warnings, {
    taskId: isNonEmptyString(contract.taskId) ? contract.taskId : null,
    inputCount: Array.isArray(contract.inputs) ? contract.inputs.length : 0,
    outputCount: Array.isArray(contract.outputs) ? contract.outputs.length : 0,
    verificationCount: Array.isArray(contract.verification) ? contract.verification.length : 0,
    runtimeMaxSeconds: Number.isInteger(contract.runtime?.maxSeconds) ? contract.runtime.maxSeconds : null,
  }, {
    canonicalPath: isNonEmptyString(contract.canonicalPath) ? contract.canonicalPath : null,
    owner: contract.owner?.primary ?? null,
  });
}
