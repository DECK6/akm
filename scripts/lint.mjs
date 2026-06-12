#!/usr/bin/env node
// AKM lint — zero-dependency validator for an AKM instance.
// Usage: node scripts/lint.mjs [path-to-akm-root]   (bun also works)
//
// Errors (exit 1)
//   E1  frontmatter missing or unparsable
//   E2  required field missing (description, akmLayer, akmType, trustLevel, date created, date modified)
//   E3  akmLayer does not match the folder the note lives in
//   E4  akmType not valid for the layer
//   E5  enum field holds a disallowed value (trustLevel, akmRole, CMDS, sourceType, nextAction)
//   E6  date not in YYYY-MM-DD format
//   E7  source note without sourcePath
//   E8  note in 90-archive/ without trustLevel: deprecated
// Warnings (exit 0)
//   W1  unresolved wikilink (skipped in 10-sources/ snapshots and 00-system/templates/)
//   W2  layer note not listed in INDEX.md / INDEX.local.md
//   W3  text matching a common secret pattern (API key, token, private key)

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, dirname, relative } from 'node:path';

const ROOT = process.argv[2] ?? process.cwd();

const LAYER_BY_DIR = {
  '10-sources': 'source',
  '20-knowledge': 'knowledge',
  '30-context': 'context',
  '40-memory': 'operational-memory',
  '50-procedures': 'procedure',
  '60-actions': 'action',
  '70-evaluation': 'evaluation',
  '80-outputs': 'output',
};

const TYPES_BY_LAYER = {
  source: ['source'],
  knowledge: ['concept', 'entity', 'comparison', 'pattern', 'principle', 'tool', 'technique', 'map'],
  context: ['context'],
  'operational-memory': ['memory'],
  procedure: ['skill', 'workflow', 'checklist', 'playbook'],
  action: ['run', 'decision', 'handoff'],
  evaluation: ['failure-pattern', 'recovery-note', 'rubric', 'audit', 'verification'],
  output: ['output'],
};

const ENUMS = {
  trustLevel: ['raw', 'unverified', 'reviewed', 'canonical', 'deprecated'],
  akmRole: ['raw-source', 'learned-reference', 'reusable-knowledge', 'operating-context', 'executable-procedure', 'verification-rule', 'deliverable'],
  CMDS: ['Connect', 'Merge', 'Develop', 'Share'],
  sourceType: ['transcript', 'article', 'paper', 'book', 'meeting', 'tool-doc', 'code', 'agent-output', 'synthesis'],
  nextAction: ['triage', 'merge', 'contextualize', 'develop-into-skill', 'verify', 'publish', 'archive'],
};

const REQUIRED = ['description', 'akmLayer', 'akmType', 'trustLevel', 'date created', 'date modified'];
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

const SECRET_PATTERNS = [
  [/sk-[A-Za-z0-9_-]{20,}/, 'OpenAI-style API key'],
  [/ghp_[A-Za-z0-9]{30,}/, 'GitHub personal token'],
  [/github_pat_[A-Za-z0-9_]{30,}/, 'GitHub fine-grained token'],
  [/AKIA[0-9A-Z]{16}/, 'AWS access key'],
  [/xox[bporas]-[A-Za-z0-9-]{10,}/, 'Slack token'],
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----/, 'private key block'],
];

const errors = [];
const warnings = [];

function walk(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.git') || entry.name === 'node_modules') continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) walk(path, out);
    else out.push(path);
  }
  return out;
}

function parseFrontmatter(text) {
  if (!text.startsWith('---\n')) return null;
  const end = text.indexOf('\n---', 4);
  if (end === -1) return null;
  const fields = {};
  for (const line of text.slice(4, end).split('\n')) {
    if (!line.trim() || /^\s/.test(line) || line.startsWith('-')) continue;
    const i = line.indexOf(':');
    if (i === -1) continue;
    let value = line.slice(i + 1).trim();
    if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1);
    fields[line.slice(0, i).trim()] = value;
  }
  return fields;
}

const allFiles = walk(ROOT);
const allMd = allFiles.filter((f) => f.endsWith('.md'));
const mdBasenames = new Set(allMd.map((f) => f.split('/').pop().replace(/\.md$/, '')));

const rel = (f) => relative(ROOT, f);
const layerNotes = allMd.filter((f) => {
  const top = rel(f).split('/')[0];
  return top in LAYER_BY_DIR || top === '90-archive';
});

// E1–E8: frontmatter and schema
for (const file of layerNotes) {
  const r = rel(file);
  const top = r.split('/')[0];
  const text = readFileSync(file, 'utf8');
  const fm = parseFrontmatter(text);

  if (!fm) { errors.push(`E1 ${r}: frontmatter missing or unparsable`); continue; }

  for (const key of REQUIRED) {
    if (!fm[key]) errors.push(`E2 ${r}: missing required field "${key}"`);
  }

  const layer = fm.akmLayer;
  if (layer && top !== '90-archive' && LAYER_BY_DIR[top] !== layer) {
    errors.push(`E3 ${r}: akmLayer "${layer}" does not match folder "${top}" (expected "${LAYER_BY_DIR[top]}")`);
  }

  if (layer && fm.akmType && TYPES_BY_LAYER[layer] && !TYPES_BY_LAYER[layer].includes(fm.akmType)) {
    errors.push(`E4 ${r}: akmType "${fm.akmType}" not valid for layer "${layer}" (allowed: ${TYPES_BY_LAYER[layer].join(', ')})`);
  }

  for (const [key, allowed] of Object.entries(ENUMS)) {
    if (fm[key] && !allowed.includes(fm[key])) {
      errors.push(`E5 ${r}: ${key} "${fm[key]}" not in [${allowed.join(', ')}]`);
    }
  }

  for (const key of ['date created', 'date modified']) {
    if (fm[key] && !DATE_RE.test(fm[key])) errors.push(`E6 ${r}: ${key} "${fm[key]}" is not YYYY-MM-DD`);
  }

  if (layer === 'source' && !fm.sourcePath) errors.push(`E7 ${r}: source note without sourcePath`);

  if (top === '90-archive' && fm.trustLevel !== 'deprecated') {
    errors.push(`E8 ${r}: archived note must have trustLevel: deprecated (got "${fm.trustLevel}")`);
  }
}

// W1: wikilink resolution (skip immutable source snapshots and placeholder templates)
const linkCheckFiles = allMd.filter((f) => {
  const r = rel(f);
  return !r.startsWith('10-sources/') && !r.startsWith('00-system/templates/');
});
for (const file of linkCheckFiles) {
  // ignore syntax examples inside fenced blocks and inline code spans
  const text = readFileSync(file, 'utf8')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`\n]*`/g, '');
  for (const match of text.matchAll(/\[\[([^\]\n]+)\]\]/g)) {
    const target = match[1].split('|')[0].split('#')[0].trim();
    if (!target) continue;
    const base = target.split('/').pop();
    const candidates = [
      join(ROOT, target), join(ROOT, `${target}.md`),
      join(dirname(file), target), join(dirname(file), `${target}.md`),
    ];
    if (!mdBasenames.has(base) && !candidates.some(existsSync)) {
      warnings.push(`W1 ${rel(file)}: unresolved wikilink [[${match[1]}]]`);
    }
  }
}

// W2: every layer note listed in INDEX.md / INDEX.local.md
let indexText = '';
for (const f of ['00-system/INDEX.md', '00-system/INDEX.local.md']) {
  const p = join(ROOT, f);
  if (existsSync(p)) indexText += readFileSync(p, 'utf8');
}
for (const file of layerNotes) {
  const base = file.split('/').pop().replace(/\.md$/, '');
  if (!indexText.includes(base)) warnings.push(`W2 ${rel(file)}: not listed in INDEX.md / INDEX.local.md`);
}

// W3: secret patterns
for (const file of allMd) {
  const text = readFileSync(file, 'utf8');
  for (const [pattern, label] of SECRET_PATTERNS) {
    if (pattern.test(text)) warnings.push(`W3 ${rel(file)}: contains text matching ${label}`);
  }
}

for (const e of errors) console.error(`ERROR   ${e}`);
for (const w of warnings) console.warn(`warning ${w}`);
console.log(`\nakm lint: ${layerNotes.length} notes checked — ${errors.length} error(s), ${warnings.length} warning(s)`);
if (errors.length > 0) process.exitCode = 1;
