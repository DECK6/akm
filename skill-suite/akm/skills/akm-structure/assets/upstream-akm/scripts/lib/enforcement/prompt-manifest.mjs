import { realpathSync, readFileSync, statSync } from 'node:fs';
import { extname, isAbsolute, relative, resolve, sep } from 'node:path';
import { SECRET_PATTERNS } from '../akm.mjs';
import {
  forbiddenPromptPathReason,
  isIsoDate,
  isNonEmptyString,
  isObject,
  isSemver,
  makeReport,
  sha256,
} from './common.mjs';

const KINDS = new Set(['AGENTS', 'CLAUDE', 'SOUL', 'skill', 'system', 'task']);
const STATES = new Set(['active', 'experimental', 'deprecated']);
const ALLOWED_EXTENSIONS = new Set(['.md', '.txt', '.json', '.yaml', '.yml']);
const MAX_ASSET_BYTES = 1024 * 1024;

function withinRoot(root, file) {
  const rel = relative(root, file);
  return rel !== '..' && !rel.startsWith(`..${sep}`) && !isAbsolute(rel);
}

function validateMetadata(asset, label, errors) {
  if (!isNonEmptyString(asset.assetId)) errors.push(`${label}: assetId is required`);
  if (!KINDS.has(asset.kind)) errors.push(`${label}: kind must be one of ${[...KINDS].join(', ')}`);
  for (const key of ['owner', 'scope', 'canonicalSource', 'version']) {
    if (!isNonEmptyString(asset[key])) errors.push(`${label}: ${key} is required`);
  }
  if (!STATES.has(asset.state)) errors.push(`${label}: state must be active|experimental|deprecated`);
  if (!isIsoDate(asset.lastReviewedAt)) errors.push(`${label}: lastReviewedAt must be an ISO date or datetime`);
  if (!isObject(asset.lifecycle)) errors.push(`${label}: lifecycle is required`);
  else {
    for (const key of ['vcs', 'changelog', 'restoreMethod', 'restoreEvidence']) {
      if (!isNonEmptyString(asset.lifecycle[key]) || /^none$/i.test(asset.lifecycle[key])) {
        errors.push(`${label}: lifecycle.${key} must identify real version/restore evidence`);
      }
    }
  }
}

export function buildPromptManifest(input, { baseDir }) {
  const errors = [];
  const warnings = [];
  const roots = isObject(input?.roots) ? input.roots : {};
  const assets = Array.isArray(input?.assets) ? input.assets : [];

  if (!isSemver(input?.schemaVersion)) errors.push('schemaVersion must be a semantic version');
  if (Object.keys(roots).length === 0) errors.push('roots must define at least one allowlisted root alias');
  if (assets.length === 0) errors.push('assets must contain at least one prompt asset');

  const resolvedRoots = new Map();
  for (const [alias, rootValue] of Object.entries(roots)) {
    if (!/^[a-z][a-z0-9-]*$/.test(alias)) {
      errors.push(`invalid root alias: ${alias}`);
      continue;
    }
    if (!isNonEmptyString(rootValue)) {
      errors.push(`root alias ${alias} must map to a path`);
      continue;
    }
    try {
      const rootPath = realpathSync(resolve(baseDir, rootValue));
      if (!statSync(rootPath).isDirectory()) errors.push(`root alias ${alias} is not a directory`);
      else resolvedRoots.set(alias, rootPath);
    } catch {
      errors.push(`root alias ${alias} does not exist`);
    }
  }

  const seen = new Set();
  const snapshots = [];
  for (const [index, asset] of assets.entries()) {
    const label = isNonEmptyString(asset?.assetId) ? asset.assetId : `assets[${index}]`;
    if (!isObject(asset)) {
      errors.push(`${label}: asset must be an object`);
      continue;
    }
    validateMetadata(asset, label, errors);
    if (seen.has(asset.assetId)) errors.push(`${label}: duplicate assetId`);
    seen.add(asset.assetId);
    if (!isNonEmptyString(asset.root) || !resolvedRoots.has(asset.root)) {
      errors.push(`${label}: root must reference a valid allowlisted alias`);
      continue;
    }
    if (!isNonEmptyString(asset.path) || isAbsolute(asset.path) || asset.path.split(/[\\/]+/).includes('..')) {
      errors.push(`${label}: path must be a non-escaping relative path`);
      continue;
    }
    const reason = forbiddenPromptPathReason(asset.path);
    if (reason) {
      errors.push(`${label}: ${reason}`);
      continue;
    }

    const rootPath = resolvedRoots.get(asset.root);
    const candidate = resolve(rootPath, asset.path);
    let filePath;
    try {
      filePath = realpathSync(candidate);
    } catch {
      errors.push(`${label}: allowlisted file does not exist at ${asset.root}:${asset.path}`);
      continue;
    }
    if (!withinRoot(rootPath, filePath)) {
      errors.push(`${label}: resolved path escapes allowlisted root`);
      continue;
    }
    const stat = statSync(filePath);
    if (!stat.isFile()) {
      errors.push(`${label}: asset is not a regular file`);
      continue;
    }
    if (!ALLOWED_EXTENSIONS.has(extname(filePath).toLowerCase())) {
      errors.push(`${label}: unsupported prompt asset extension`);
      continue;
    }
    if (stat.size > MAX_ASSET_BYTES) {
      errors.push(`${label}: prompt asset exceeds ${MAX_ASSET_BYTES} bytes`);
      continue;
    }

    const content = readFileSync(filePath);
    const text = content.toString('utf8');
    for (const [pattern, secretLabel] of SECRET_PATTERNS) {
      pattern.lastIndex = 0;
      if (pattern.test(text)) errors.push(`${label}: content matches excluded ${secretLabel}`);
    }
    snapshots.push({
      assetId: asset.assetId,
      path: `${asset.root}:${asset.path.replaceAll('\\', '/')}`,
      kind: asset.kind,
      owner: asset.owner,
      scope: asset.scope,
      canonicalSource: asset.canonicalSource,
      version: asset.version,
      state: asset.state,
      lastReviewedAt: asset.lastReviewedAt,
      lifecycle: asset.lifecycle,
      bytes: stat.size,
      sha256: sha256(content),
    });
  }

  snapshots.sort((left, right) => left.assetId.localeCompare(right.assetId));
  return makeReport('prompt-manifest', errors, warnings, {
    declaredAssetCount: assets.length,
    snapshotAssetCount: snapshots.length,
    activeCount: snapshots.filter((asset) => asset.state === 'active').length,
    excludedCount: assets.length - snapshots.length,
  }, { assets: snapshots });
}
