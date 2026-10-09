#!/usr/bin/env node
// Export selected AKM layers as an OKF-compatible Markdown bundle.
//
// Usage:
//   node scripts/export-okf.mjs [akm-root] [out-dir]
//   node scripts/export-okf.mjs --root . --out dist/okf --layers 20-knowledge,50-procedures
//   node scripts/export-okf.mjs --dry-run

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import {
  DEFAULT_EXPORT_DIRS,
  buildMarkdownIndex,
  convertWikilinksToMarkdown,
  extractUrls,
  firstHeading,
  formatYaml,
  normalizeTimestamp,
  okfTypeFromAkmType,
  posixRel,
  readMarkdown,
  titleFromPath,
  walk,
} from './lib/akm.mjs';

const options = parseArgs(process.argv.slice(2));
const sourceRoot = options.root;
const outRoot = options.out;
const generatedAt = options.generatedAt ?? new Date().toISOString();
const sourceRootLabel = options.sourceRootLabel ?? displayRoot(sourceRoot);
const index = buildMarkdownIndex(sourceRoot);

const files = walk(sourceRoot).filter((file) => {
  if (!file.endsWith('.md')) return false;
  const rel = posixRel(sourceRoot, file);
  if (rel.includes('/INDEX.local.md') || rel.endsWith('/index.md')) return false;
  return options.layers.some((layer) => rel === `${layer}.md` || rel.startsWith(`${layer}/`));
});

const outputs = new Map();
const exportedEntries = [];

for (const file of files) {
  const rel = posixRel(sourceRoot, file);
  const { text, frontmatter } = readMarkdown(file);
  if (!frontmatter) {
    console.warn(`skip ${rel}: frontmatter missing or unparsable`);
    continue;
  }

  const fm = frontmatter.fields;
  const body = convertWikilinksToMarkdown(frontmatter.body, sourceRoot, file, index);
  const title = firstHeading(frontmatter.body) ?? titleFromPath(file);
  const resource = fm.sourcePath || extractUrls(frontmatter.body)[0];
  const okfFields = {
    type: okfTypeFromAkmType(fm.akmType) ?? 'Concept',
    title,
    description: fm.description,
    resource,
    tags: Array.isArray(fm.tags) ? fm.tags : undefined,
    timestamp: normalizeTimestamp(fm['date modified']),
  };

  outputs.set(rel, `${formatYaml(okfFields)}${body.trimEnd()}\n`);
  exportedEntries.push({ rel, title, description: fm.description, type: okfFields.type });

  if (text.includes('[[') && !body.includes('[[')) {
    // Useful in dry-run output without being noisy during normal export.
    exportedEntries[exportedEntries.length - 1].convertedWikilinks = true;
  }
}

addRootIndex(outputs, exportedEntries, generatedAt, sourceRootLabel, options.layers);
addDirectoryIndexes(outputs, exportedEntries);
addLog(outputs, generatedAt, sourceRootLabel, options.layers);

if (options.dryRun) {
  console.log(`OKF export dry run: ${outputs.size} file(s) would be written to ${outRoot}`);
  for (const rel of [...outputs.keys()].sort()) {
    const entry = exportedEntries.find((item) => item.rel === rel);
    console.log(`- ${rel}${entry?.convertedWikilinks ? ' (wikilinks converted)' : ''}`);
  }
} else {
  for (const [rel, content] of outputs.entries()) {
    const dest = join(outRoot, rel);
    mkdirSync(dirname(dest), { recursive: true });
    writeFileSync(dest, content, 'utf8');
  }
  console.log(`OKF export: wrote ${outputs.size} file(s) to ${outRoot}`);
}

function parseArgs(args) {
  const parsed = {
    root: process.cwd(),
    out: join(process.cwd(), 'dist/okf'),
    layers: DEFAULT_EXPORT_DIRS,
    dryRun: false,
    generatedAt: null,
    sourceRootLabel: null,
  };
  const positionals = [];

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === '--dry-run') {
      parsed.dryRun = true;
    } else if (arg === '--root') {
      parsed.root = args[++i];
    } else if (arg === '--out') {
      parsed.out = args[++i];
    } else if (arg === '--layers') {
      parsed.layers = args[++i].split(',').map((item) => item.trim()).filter(Boolean);
    } else if (arg === '--generated-at') {
      parsed.generatedAt = args[++i];
    } else if (arg === '--source-root-label') {
      parsed.sourceRootLabel = args[++i];
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    } else {
      positionals.push(arg);
    }
  }

  if (positionals[0]) parsed.root = positionals[0];
  if (positionals[1]) parsed.out = positionals[1];
  return parsed;
}

function displayRoot(root) {
  const rel = relative(process.cwd(), root).split('\\').join('/');
  if (rel === '') return '.';
  return rel && !rel.startsWith('..') ? rel : root;
}

function printHelp() {
  console.log(`Export AKM notes as an OKF-compatible bundle.

Usage:
  node scripts/export-okf.mjs [akm-root] [out-dir]
  node scripts/export-okf.mjs --root . --out dist/okf --layers 20-knowledge,50-procedures
  node scripts/export-okf.mjs --dry-run`);
}

function addRootIndex(outputs, entries, generatedAt, sourceRoot, layers) {
  const frontmatter = formatYaml({
    okf_version: '0.1',
    title: 'AKM OKF Export',
    generated_at: generatedAt,
    source_root: sourceRoot,
  });
  const lines = [
    '# AKM OKF Export',
    '',
    'This bundle is generated from AKM notes. AKM keeps its internal schema and wikilinks; this export maps selected notes to OKF-compatible Markdown.',
    '',
    '## Exported layers',
    '',
    ...layers.map((layer) => `- ${layer}`),
    '',
    '## Contents',
    '',
  ];
  for (const entry of entries.sort((a, b) => a.rel.localeCompare(b.rel))) {
    lines.push(`- [${entry.title}](/${entry.rel}) - ${entry.type}${entry.description ? `; ${entry.description}` : ''}`);
  }
  outputs.set('index.md', `${frontmatter}\n${lines.join('\n')}\n`);
}

function addDirectoryIndexes(outputs, entries) {
  const byDir = new Map();
  for (const entry of entries) {
    const dir = entry.rel.split('/').slice(0, -1).join('/');
    if (!dir) continue;
    if (!byDir.has(dir)) byDir.set(dir, []);
    byDir.get(dir).push(entry);
  }

  for (const [dir, dirEntries] of byDir.entries()) {
    const title = dir.split('/').pop();
    const lines = [`# ${title} index`, '', 'Directory-level entry point for OKF consumers.', ''];
    for (const entry of dirEntries.sort((a, b) => a.rel.localeCompare(b.rel))) {
      lines.push(`- [${entry.title}](/${entry.rel}) - ${entry.type}${entry.description ? `; ${entry.description}` : ''}`);
    }
    outputs.set(`${dir}/index.md`, `${lines.join('\n')}\n`);
  }
}

function addLog(outputs, generatedAt, sourceRoot, layers) {
  const lines = [
    '# OKF Bundle Log',
    '',
    'Chronological bundle-level changes only. Execution details, failure analyses, and session logs stay in AKM action/evaluation layers.',
    '',
    `- ${generatedAt} | export | Generated OKF-compatible bundle from ${sourceRoot} (${layers.join(', ')})`,
  ];
  outputs.set('log.md', `${lines.join('\n')}\n`);
}
