#!/usr/bin/env node
// AKM lint — zero-dependency validators for AKM roots and OKF export bundles.
//
// Usage:
//   node scripts/lint.mjs
//   node scripts/lint.mjs --akm [path-to-akm-root]
//   node scripts/lint.mjs --okf-export <path-to-okf-bundle>
//   node scripts/lint.mjs --links [path]
//   node scripts/lint.mjs --secrets [path]

import { existsSync, readFileSync } from 'node:fs';
import { basename, dirname, join } from 'node:path';
import {
  DATE_RE,
  ENUMS,
  LAYER_BY_DIR,
  LIST_FIELDS,
  REQUIRED,
  SECRET_PATTERNS,
  TYPES_BY_LAYER,
  buildMarkdownIndex,
  findMarkdownLinks,
  layerNotes,
  parseFrontmatter,
  posixRel,
  readMarkdown,
  resolveMarkdownHref,
  resolveWikiTarget,
  stripCode,
  walk,
} from './lib/akm.mjs';

const { mode, root } = parseArgs(process.argv.slice(2));
const errors = [];
const warnings = [];

if (mode === 'help') {
  printHelp();
  process.exit(0);
} else if (mode === 'akm') lintAkmRoot(root);
else if (mode === 'okf-export') lintOkfExport(root);
else if (mode === 'links') lintLinks(root);
else if (mode === 'secrets') lintSecrets(root);
else {
  printHelp();
  process.exitCode = 1;
}

for (const e of errors) console.error(`ERROR   ${e}`);
for (const w of warnings) console.warn(`warning ${w}`);

const label = mode === 'okf-export' ? 'okf export lint' : `${mode} lint`;
console.log(`\n${label}: ${errors.length} error(s), ${warnings.length} warning(s)`);
if (errors.length > 0) process.exitCode = 1;

function parseArgs(args) {
  if (args.includes('--help') || args.includes('-h')) return { mode: 'help', root: process.cwd() };
  if (args.length === 0) return { mode: 'akm', root: process.cwd() };

  const first = args[0];
  if (!first.startsWith('--')) return { mode: 'akm', root: first };

  const modeByFlag = {
    '--akm': 'akm',
    '--okf-export': 'okf-export',
    '--links': 'links',
    '--secrets': 'secrets',
  };
  const parsedMode = modeByFlag[first];
  if (!parsedMode) return { mode: 'help', root: process.cwd() };
  return { mode: parsedMode, root: args[1] && !args[1].startsWith('--') ? args[1] : process.cwd() };
}

function printHelp() {
  console.log(`AKM lint

Usage:
  node scripts/lint.mjs
  node scripts/lint.mjs --akm [path-to-akm-root]
  node scripts/lint.mjs --okf-export <path-to-okf-bundle>
  node scripts/lint.mjs --links [path]
  node scripts/lint.mjs --secrets [path]`);
}

function lintAkmRoot(akmRoot) {
  const notes = layerNotes(akmRoot);
  const allMd = walk(akmRoot).filter((file) => file.endsWith('.md'));

  lintAkmSchema(akmRoot, notes);
  lintWikilinks(akmRoot, allMd);
  lintIndexCoverage(akmRoot, notes);
  lintDuplicateLayerBasenames(akmRoot, notes);
  lintSecretsInFiles(akmRoot, allMd);

  const sampleRoot = join(akmRoot, 'examples/minimal-akm');
  if (existsSync(sampleRoot)) {
    const sampleNotes = layerNotes(sampleRoot);
    lintAkmSchema(sampleRoot, sampleNotes, 'sample ');
    lintWikilinks(sampleRoot, walk(sampleRoot).filter((file) => file.endsWith('.md')), 'sample ');
    lintIndexCoverage(sampleRoot, sampleNotes, 'sample ');
  }

  console.log(`akm lint: ${notes.length} root note(s) checked`);
}

function lintAkmSchema(akmRoot, notes, prefix = '') {
  for (const file of notes) {
    const r = posixRel(akmRoot, file);
    const top = r.split('/')[0];
    const { text, frontmatter } = readMarkdown(file);
    if (!frontmatter) {
      errors.push(`${prefix}E1 ${r}: frontmatter missing or unparsable`);
      continue;
    }

    for (const warning of frontmatter.warnings) warnings.push(`${prefix}W0 ${r}: ${warning}`);
    const fm = frontmatter.fields;

    for (const key of REQUIRED) {
      if (!fm[key]) errors.push(`${prefix}E2 ${r}: missing required field "${key}"`);
    }

    const layer = fm.akmLayer;
    if (layer && top !== '90-archive' && LAYER_BY_DIR[top] !== layer) {
      errors.push(`${prefix}E3 ${r}: akmLayer "${layer}" does not match folder "${top}" (expected "${LAYER_BY_DIR[top]}")`);
    }

    if (layer && fm.akmType && TYPES_BY_LAYER[layer] && !TYPES_BY_LAYER[layer].includes(fm.akmType)) {
      errors.push(`${prefix}E4 ${r}: akmType "${fm.akmType}" not valid for layer "${layer}" (allowed: ${TYPES_BY_LAYER[layer].join(', ')})`);
    }

    for (const [key, allowed] of Object.entries(ENUMS)) {
      if (fm[key] && !allowed.includes(fm[key])) {
        errors.push(`${prefix}E5 ${r}: ${key} "${fm[key]}" not in [${allowed.join(', ')}]`);
      }
    }

    for (const key of ['date created', 'date modified']) {
      if (fm[key] && !DATE_RE.test(String(fm[key]))) errors.push(`${prefix}E6 ${r}: ${key} "${fm[key]}" is not YYYY-MM-DD`);
    }

    if (layer === 'source' && !fm.sourcePath) errors.push(`${prefix}E7 ${r}: source note without sourcePath`);

    if (top === '90-archive' && fm.trustLevel !== 'deprecated') {
      errors.push(`${prefix}E8 ${r}: archived note must have trustLevel: deprecated (got "${fm.trustLevel}")`);
    }

    for (const key of LIST_FIELDS) {
      if (fm[key] !== undefined && !Array.isArray(fm[key])) {
        errors.push(`${prefix}E9 ${r}: ${key} must be a YAML list`);
      }
    }

    if (!text.endsWith('\n')) warnings.push(`${prefix}W8 ${r}: file should end with a newline`);
  }
}

function lintWikilinks(root, allMd, prefix = '') {
  const index = buildMarkdownIndex(root);
  for (const file of allMd) {
    const r = posixRel(root, file);
    if (r.startsWith('10-sources/') || r.startsWith('99-system/templates/')) continue;
    const text = stripCode(readFileSync(file, 'utf8'));
    for (const match of text.matchAll(/\[\[([^\]\n]+)\]\]/g)) {
      const target = match[1].split('|')[0].trim();
      if (!target) continue;
      if (!resolveWikiTarget(root, file, target, index)) {
        warnings.push(`${prefix}W1 ${r}: unresolved wikilink [[${match[1]}]]`);
      }
    }
  }
}

function lintIndexCoverage(root, notes, prefix = '') {
  let indexText = '';
  for (const f of ['99-system/INDEX.md', '99-system/INDEX.local.md']) {
    const p = join(root, f);
    if (existsSync(p)) indexText += readFileSync(p, 'utf8');
  }
  if (!indexText) return;
  for (const file of notes) {
    const base = basename(file, '.md');
    if (!indexText.includes(base)) warnings.push(`${prefix}W2 ${posixRel(root, file)}: not listed in INDEX.md / INDEX.local.md`);
  }
}

function lintDuplicateLayerBasenames(root, notes) {
  const byBase = new Map();
  for (const file of notes) {
    const base = basename(file, '.md');
    if (!byBase.has(base)) byBase.set(base, []);
    byBase.get(base).push(posixRel(root, file));
  }
  for (const [base, files] of byBase.entries()) {
    if (files.length > 1) warnings.push(`W4 duplicate layer basename "${base}": ${files.join(', ')}`);
  }
}

function lintSecrets(rootPath) {
  lintSecretsInFiles(rootPath, walk(rootPath).filter((file) => file.endsWith('.md')));
}

function lintSecretsInFiles(rootPath, files) {
  for (const file of files) {
    const text = readFileSync(file, 'utf8');
    for (const [pattern, label] of SECRET_PATTERNS) {
      if (pattern.test(text)) warnings.push(`W3 ${posixRel(rootPath, file)}: contains text matching ${label}`);
    }
  }
}

function lintLinks(rootPath) {
  const allMd = walk(rootPath).filter((file) => file.endsWith('.md'));
  lintWikilinks(rootPath, allMd);
  lintMarkdownLinks(rootPath, allMd);
}

function lintMarkdownLinks(rootPath, files, prefix = '') {
  for (const file of files) {
    const text = readFileSync(file, 'utf8');
    for (const link of findMarkdownLinks(text)) {
      if (!resolveMarkdownHref(rootPath, file, link.href)) {
        warnings.push(`${prefix}W5 ${posixRel(rootPath, file)}: broken Markdown link [${link.label}](${link.href})`);
      }
    }
  }
}

function lintOkfExport(bundleRoot) {
  const rootIndex = join(bundleRoot, 'index.md');
  const allMd = walk(bundleRoot).filter((file) => file.endsWith('.md'));
  if (!existsSync(rootIndex)) {
    errors.push('O1 index.md: missing bundle root index.md');
  } else {
    const rootFm = parseFrontmatter(readFileSync(rootIndex, 'utf8'));
    if (!rootFm?.fields.okf_version) errors.push('O2 index.md: missing okf_version frontmatter');
  }

  const conceptFiles = allMd.filter((file) => {
    const name = basename(file);
    return name !== 'index.md' && name !== 'log.md';
  });

  for (const file of conceptFiles) {
    const r = posixRel(bundleRoot, file);
    const fm = parseFrontmatter(readFileSync(file, 'utf8'));
    if (!fm) {
      errors.push(`O3 ${r}: frontmatter missing or unparsable`);
      continue;
    }
    if (!fm.fields.type) errors.push(`O4 ${r}: missing required OKF field "type"`);
    if (!fm.fields.title) warnings.push(`O5 ${r}: optional field "title" missing`);
    if (!fm.fields.description) warnings.push(`O6 ${r}: optional field "description" missing`);
    if (fm.fields.tags !== undefined && !Array.isArray(fm.fields.tags)) {
      warnings.push(`O7 ${r}: tags should be a YAML list`);
    }
  }

  lintMarkdownLinks(bundleRoot, allMd, 'OKF ');
  lintMissingDirectoryIndexes(bundleRoot, conceptFiles);
}

function lintMissingDirectoryIndexes(bundleRoot, conceptFiles) {
  const dirs = new Set(conceptFiles.map((file) => dirname(file)));
  for (const dir of dirs) {
    if (dir === bundleRoot) continue;
    if (!existsSync(join(dir, 'index.md'))) {
      warnings.push(`OKF O8 ${posixRel(bundleRoot, dir)}/: directory has concepts but no index.md`);
    }
  }
}
