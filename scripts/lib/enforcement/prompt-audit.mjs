import { existsSync, readFileSync, realpathSync, statSync } from 'node:fs';
import { isAbsolute, relative, resolve, sep } from 'node:path';
import {
  forbiddenPromptPathReason,
  isNonEmptyString,
  isObject,
  isSemver,
  makeReport,
  sha256,
} from './common.mjs';

const TYPES = new Set(['AGENTS', 'CLAUDE', 'SOUL', 'skill', 'system', 'task']);
const SCOPE_KINDS = new Set(['global', 'profile', 'project', 'directory', 'skill', 'task']);
const EFFECTS = new Set(['allow', 'deny', 'require']);

function scopesOverlap(left, right) {
  if (left.kind === 'global' || right.kind === 'global') return true;
  if (left.kind !== right.kind) return false;
  return left.target === '*' || right.target === '*' || left.target === right.target;
}

function directiveSignature(asset) {
  return `${asset.directive.effect}:${asset.directive.value.trim().toLowerCase()}`;
}

function findCycles(graph) {
  const cycles = [];
  const visiting = new Set();
  const visited = new Set();
  const stack = [];

  function visit(node) {
    if (visiting.has(node)) {
      const start = stack.indexOf(node);
      cycles.push([...stack.slice(start), node]);
      return;
    }
    if (visited.has(node)) return;
    visiting.add(node);
    stack.push(node);
    for (const next of graph.get(node) ?? []) visit(next);
    stack.pop();
    visiting.delete(node);
    visited.add(node);
  }

  for (const node of graph.keys()) visit(node);
  return cycles;
}

function hasOverridePath(graph, from, to, seen = new Set()) {
  if (from === to) return true;
  if (seen.has(from)) return false;
  seen.add(from);
  for (const next of graph.get(from) ?? []) {
    if (next === to || hasOverridePath(graph, next, to, seen)) return true;
  }
  return false;
}

function resolveAssetPath(input, asset, baseDir, errors) {
  if (!isNonEmptyString(asset.path)) {
    errors.push(`${asset.id ?? '(unknown)'}: path is required`);
    return null;
  }
  const forbiddenReason = forbiddenPromptPathReason(asset.path);
  if (forbiddenReason) {
    errors.push(`${asset.id}: ${forbiddenReason}`);
    return null;
  }

  const hasRootAlias = asset.root !== undefined;
  if (hasRootAlias) {
    if (!isNonEmptyString(asset.root) || !isObject(input.roots) || !isNonEmptyString(input.roots[asset.root])) {
      errors.push(`${asset.id}: root alias "${asset.root}" is not defined`);
      return null;
    }
  }

  if (isAbsolute(asset.path) || asset.path.split(/[\\/]+/).includes('..')) {
    errors.push(`${asset.id}: asset path must be relative and cannot escape its ${hasRootAlias ? 'root' : 'manifest directory'}`);
    return null;
  }

  const displayPath = hasRootAlias
    ? `${asset.root}:${asset.path.replaceAll('\\', '/')}`
    : asset.path.replaceAll('\\', '/');
  let rootPath;
  try {
    rootPath = realpathSync(hasRootAlias ? resolve(baseDir, input.roots[asset.root]) : baseDir);
    if (!statSync(rootPath).isDirectory()) {
      errors.push(`${asset.id}: ${hasRootAlias ? `root alias "${asset.root}"` : 'manifest directory'} is not a directory`);
      return null;
    }
  } catch {
    errors.push(`${asset.id}: ${hasRootAlias ? `root alias "${asset.root}"` : 'manifest directory'} does not exist`);
    return null;
  }

  const candidate = resolve(rootPath, asset.path);
  let filePath;
  try {
    filePath = realpathSync(candidate);
  } catch {
    errors.push(`${asset.id}: instruction asset does not exist at ${displayPath}`);
    return null;
  }
  const rel = relative(rootPath, filePath);
  if (rel.startsWith(`..${sep}`) || rel === '..') {
    errors.push(`${asset.id}: resolved path escapes ${hasRootAlias ? `root alias "${asset.root}"` : 'the manifest directory'}`);
    return null;
  }
  return { filePath, displayPath };
}

export function auditInstructionPrecedence(input, { baseDir }) {
  const errors = [];
  const warnings = [];
  const assets = Array.isArray(input?.assets) ? input.assets : [];

  if (!isSemver(input?.schemaVersion)) errors.push('schemaVersion must be a semantic version');
  if (assets.length === 0) errors.push('assets must contain at least one instruction asset');

  const byId = new Map();
  const inspected = [];
  for (const asset of assets) {
    const label = isNonEmptyString(asset?.id) ? asset.id : '(unknown)';
    if (!isObject(asset)) {
      errors.push('each asset must be an object');
      continue;
    }
    if (!isNonEmptyString(asset.id)) errors.push('asset id is required');
    else if (byId.has(asset.id)) errors.push(`${asset.id}: duplicate asset id`);
    else byId.set(asset.id, asset);
    if (!TYPES.has(asset.type)) errors.push(`${label}: type must be one of ${[...TYPES].join(', ')}`);
    if (!isNonEmptyString(asset.owner)) errors.push(`${label}: owner is required`);
    if (!isObject(asset.scope) || !SCOPE_KINDS.has(asset.scope.kind) || !isNonEmptyString(asset.scope.target)) {
      errors.push(`${label}: scope requires a supported kind and non-empty target`);
    }
    if (!isNonEmptyString(asset.appliesWhen)) errors.push(`${label}: appliesWhen is required`);
    if (!Number.isInteger(asset.precedenceRank) || asset.precedenceRank < 0) {
      errors.push(`${label}: precedenceRank must be a non-negative integer`);
    }
    if (!Array.isArray(asset.overrides)) errors.push(`${label}: overrides must be an array`);
    if (!Array.isArray(asset.mustNotOverride)) errors.push(`${label}: mustNotOverride must be an array`);
    if (!isNonEmptyString(asset.conflictKey)) errors.push(`${label}: conflictKey is required`);
    if (!isObject(asset.directive) || !EFFECTS.has(asset.directive.effect) || !isNonEmptyString(asset.directive.value)) {
      errors.push(`${label}: directive requires effect allow|deny|require and a non-empty value`);
    }

    const resolved = resolveAssetPath(input, asset, baseDir, errors);
    if (resolved && !existsSync(resolved.filePath)) {
      errors.push(`${label}: instruction asset does not exist at ${resolved.displayPath}`);
    } else if (resolved && !statSync(resolved.filePath).isFile()) {
      errors.push(`${label}: instruction asset is not a regular file at ${resolved.displayPath}`);
    } else if (resolved) {
      inspected.push({
        id: asset.id,
        path: resolved.displayPath,
        type: asset.type,
        owner: asset.owner,
        scope: asset.scope,
        precedenceRank: asset.precedenceRank,
        conflictKey: asset.conflictKey,
        sha256: sha256(readFileSync(resolved.filePath)),
      });
    }
  }

  const graph = new Map([...byId.keys()].map((id) => [id, new Set()]));
  for (const asset of assets.filter((item) => isObject(item) && isNonEmptyString(item.id))) {
    for (const target of Array.isArray(asset.overrides) ? asset.overrides : []) {
      if (!byId.has(target)) {
        errors.push(`${asset.id}: overrides unknown asset "${target}"`);
        continue;
      }
      graph.get(asset.id)?.add(target);
      const targetAsset = byId.get(target);
      if (Number.isInteger(asset.precedenceRank) && Number.isInteger(targetAsset.precedenceRank)
          && asset.precedenceRank >= targetAsset.precedenceRank) {
        errors.push(`${asset.id}: override of ${target} requires a lower precedenceRank than ${targetAsset.precedenceRank}`);
      }
      const protectedFrom = Array.isArray(targetAsset.mustNotOverride) ? targetAsset.mustNotOverride : [];
      if (protectedFrom.includes('*') || protectedFrom.includes(asset.id) || protectedFrom.includes(asset.type)) {
        errors.push(`${asset.id}: override of protected asset ${target} violates mustNotOverride`);
      }
    }
  }

  for (const cycle of findCycles(graph)) errors.push(`override cycle: ${cycle.join(' -> ')}`);

  let conflictPairs = 0;
  for (let i = 0; i < assets.length; i += 1) {
    const left = assets[i];
    if (!isObject(left.scope) || !isObject(left.directive)) continue;
    for (let j = i + 1; j < assets.length; j += 1) {
      const right = assets[j];
      if (!isObject(right.scope) || !isObject(right.directive)) continue;
      if (left.conflictKey !== right.conflictKey || !scopesOverlap(left.scope, right.scope)) continue;
      if (directiveSignature(left) === directiveSignature(right)) continue;
      conflictPairs += 1;
      const resolved = hasOverridePath(graph, left.id, right.id) || hasOverridePath(graph, right.id, left.id);
      if (!resolved) {
        errors.push(`${left.conflictKey}: unresolved conflict between ${left.id} and ${right.id}`);
      }
    }
  }

  inspected.sort((left, right) => left.id.localeCompare(right.id));
  return makeReport('prompt-audit', errors, warnings, {
    assetCount: assets.length,
    inspectedCount: inspected.length,
    conflictPairs,
    overrideEdges: [...graph.values()].reduce((sum, targets) => sum + targets.size, 0),
  }, { assets: inspected });
}
