#!/usr/bin/env node
// Generate directory-level AKM indexes for progressive disclosure.
//
// Usage:
//   node scripts/index.mjs --write
//   node scripts/index.mjs --stdout --layers 20-knowledge,70-evaluation
//   node scripts/index.mjs --write --okf ./examples/okf-export

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import {
  DEFAULT_EXPORT_DIRS,
  firstHeading,
  posixRel,
  readMarkdown,
  walk,
} from './lib/akm.mjs';

const options = parseArgs(process.argv.slice(2));
const indexes = generateIndexes(options.root, options.layers, options.okf);

if (options.stdout || !options.write) {
  for (const [rel, content] of indexes.entries()) {
    console.log(`--- ${rel} ---`);
    console.log(content.trimEnd());
  }
}

if (options.write) {
  for (const [rel, content] of indexes.entries()) {
    const dest = join(options.root, rel);
    mkdirSync(dirname(dest), { recursive: true });
    writeFileSync(dest, content, 'utf8');
  }
  console.log(`index: wrote ${indexes.size} index file(s) under ${options.root}`);
}

function parseArgs(args) {
  const parsed = {
    root: process.cwd(),
    layers: DEFAULT_EXPORT_DIRS,
    write: false,
    stdout: false,
    okf: false,
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === '--write') parsed.write = true;
    else if (arg === '--stdout') parsed.stdout = true;
    else if (arg === '--okf') parsed.okf = true;
    else if (arg === '--layers') parsed.layers = args[++i].split(',').map((item) => item.trim()).filter(Boolean);
    else if (arg === '--root') parsed.root = args[++i];
    else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    } else {
      parsed.root = arg;
    }
  }
  return parsed;
}

function printHelp() {
  console.log(`Generate directory-level indexes.

Usage:
  node scripts/index.mjs --write
  node scripts/index.mjs --stdout --layers 20-knowledge,70-evaluation
  node scripts/index.mjs --write --okf ./examples/okf-export`);
}

function generateIndexes(root, layers, okfMode) {
  const outputs = new Map();
  for (const layer of layers) {
    const files = walk(join(root, layer)).filter((file) => {
      if (!file.endsWith('.md')) return false;
      const name = file.split('/').pop();
      return name !== 'INDEX.local.md' && name !== 'index.md';
    });
    outputs.set(`${layer}/${okfMode ? 'index.md' : 'INDEX.local.md'}`, renderIndex(root, layer, files, okfMode));
  }
  return outputs;
}

function renderIndex(root, layer, files, okfMode) {
  const title = layerTitle(layer);
  const lines = [
    `# ${title} Index`,
    '',
    okfMode
      ? 'Directory-level entry point for OKF consumers.'
      : 'Directory-level local entry point for AKM agents. Generated files can stay untracked as INDEX.local.md.',
    '',
  ];

  if (files.length === 0) {
    lines.push('(empty)');
    return `${lines.join('\n')}\n`;
  }

  const byDir = new Map();
  for (const file of files) {
    const rel = posixRel(root, file);
    const subdir = rel.split('/').slice(1, -1).join('/') || '(root)';
    if (!byDir.has(subdir)) byDir.set(subdir, []);
    byDir.get(subdir).push(file);
  }

  for (const [subdir, subdirFiles] of [...byDir.entries()].sort()) {
    lines.push(`## ${subdir}`);
    lines.push('');
    for (const file of subdirFiles.sort()) {
      const rel = posixRel(root, file);
      const { frontmatter } = readMarkdown(file);
      const title = frontmatter ? firstHeading(frontmatter.body) ?? file.split('/').pop().replace(/\.md$/, '') : file.split('/').pop().replace(/\.md$/, '');
      const description = frontmatter?.fields.description;
      const link = okfMode ? `[${title}](/${rel})` : `[[${file.split('/').pop().replace(/\.md$/, '')}]]`;
      lines.push(`- ${link}${description ? ` - ${description}` : ''}`);
    }
    lines.push('');
  }

  return `${lines.join('\n').trimEnd()}\n`;
}

function layerTitle(layer) {
  return layer.replace(/^\d+-/, '').replace(/-/g, ' ');
}
