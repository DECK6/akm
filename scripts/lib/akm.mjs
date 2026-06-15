import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { basename, dirname, join, relative } from 'node:path';

export const LAYER_BY_DIR = {
  '10-sources': 'source',
  '20-knowledge': 'knowledge',
  '30-context': 'context',
  '40-memory': 'operational-memory',
  '50-procedures': 'procedure',
  '60-actions': 'action',
  '70-evaluation': 'evaluation',
  '80-outputs': 'output',
};

export const DEFAULT_EXPORT_DIRS = ['20-knowledge', '30-context', '50-procedures', '70-evaluation'];

export const TYPES_BY_LAYER = {
  source: ['source'],
  knowledge: ['concept', 'entity', 'comparison', 'pattern', 'principle', 'tool', 'technique', 'map'],
  context: ['context'],
  'operational-memory': ['memory'],
  procedure: ['skill', 'workflow', 'checklist', 'playbook'],
  action: ['run', 'decision', 'handoff'],
  evaluation: ['failure-pattern', 'recovery-note', 'rubric', 'audit', 'verification'],
  output: ['output'],
};

export const ENUMS = {
  trustLevel: ['raw', 'unverified', 'reviewed', 'canonical', 'deprecated'],
  akmRole: ['raw-source', 'learned-reference', 'reusable-knowledge', 'operating-context', 'executable-procedure', 'verification-rule', 'deliverable'],
  CMDS: ['Connect', 'Merge', 'Develop', 'Share'],
  sourceType: ['transcript', 'article', 'paper', 'book', 'meeting', 'tool-doc', 'code', 'agent-output', 'synthesis'],
  nextAction: ['triage', 'classify', 'merge', 'contextualize', 'develop-into-skill', 'verify', 'publish', 'archive'],
};

export const REQUIRED = ['description', 'akmLayer', 'akmType', 'trustLevel', 'date created', 'date modified'];
export const LIST_FIELDS = new Set(['aliases', 'tags', 'usedBy']);
export const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export const SECRET_PATTERNS = [
  [/sk-[A-Za-z0-9_-]{20,}/, 'OpenAI-style API key'],
  [/ghp_[A-Za-z0-9]{30,}/, 'GitHub personal token'],
  [/github_pat_[A-Za-z0-9_]{30,}/, 'GitHub fine-grained token'],
  [/AKIA[0-9A-Z]{16}/, 'AWS access key'],
  [/AIza[0-9A-Za-z_-]{20,}/, 'Google API key'],
  [/xox[bporas]-[A-Za-z0-9-]{10,}/, 'Slack token'],
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----/, 'private key block'],
  [/-----BEGIN OPENSSH PRIVATE KEY-----/, 'OpenSSH private key block'],
  [/\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b/, 'JWT-like token'],
];

const SKIP_DIRS = new Set(['.git', 'node_modules']);

export function walk(dir, out = []) {
  if (!existsSync(dir) || !statSync(dir).isDirectory()) return out;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (SKIP_DIRS.has(entry.name)) continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) walk(path, out);
    else out.push(path);
  }
  return out.sort();
}

export function posixRel(root, file) {
  return relative(root, file).split('\\').join('/');
}

export function stripCode(text) {
  return text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`\n]*`/g, '');
}

function splitInlineList(value) {
  const inner = value.slice(1, -1).trim();
  if (!inner) return [];
  const items = [];
  let current = '';
  let quote = null;
  for (let i = 0; i < inner.length; i += 1) {
    const ch = inner[i];
    if ((ch === '"' || ch === "'") && inner[i - 1] !== '\\') {
      quote = quote === ch ? null : quote ?? ch;
      current += ch;
      continue;
    }
    if (ch === ',' && !quote) {
      items.push(parseScalar(current.trim()));
      current = '';
      continue;
    }
    current += ch;
  }
  if (current.trim()) items.push(parseScalar(current.trim()));
  return items;
}

export function parseScalar(raw) {
  let value = raw.trim();
  if (value === '[]') return [];
  if (value.startsWith('[') && value.endsWith(']')) return splitInlineList(value);
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    value = value.slice(1, -1);
  }
  return value;
}

export function parseFrontmatter(text) {
  if (!text.startsWith('---\n')) return null;
  const end = text.indexOf('\n---', 4);
  if (end === -1) return null;

  const raw = text.slice(4, end);
  const bodyStart = text.indexOf('\n', end + 4) + 1;
  const body = bodyStart > 0 ? text.slice(bodyStart) : '';
  const lines = raw.split('\n');
  const fields = {};
  const warnings = [];

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    if (!line.trim() || /^\s/.test(line) || line.trim().startsWith('-')) continue;
    const splitAt = line.indexOf(':');
    if (splitAt === -1) {
      warnings.push(`frontmatter line ${i + 1} is not key: value`);
      continue;
    }

    const key = line.slice(0, splitAt).trim();
    const rest = line.slice(splitAt + 1).trim();
    if (rest) {
      fields[key] = parseScalar(rest);
      continue;
    }

    const block = [];
    let j = i + 1;
    while (j < lines.length && (/^\s+/.test(lines[j]) || lines[j].trim().startsWith('-'))) {
      if (lines[j].trim()) block.push(lines[j]);
      j += 1;
    }

    if (block.length === 0) {
      fields[key] = '';
    } else if (block.every((item) => item.trim().startsWith('- '))) {
      fields[key] = block.map((item) => parseScalar(item.trim().slice(2).trim()));
    } else {
      const object = {};
      let objectLike = true;
      for (const item of block) {
        const trimmed = item.trim();
        const objectSplitAt = trimmed.indexOf(':');
        if (objectSplitAt === -1) {
          objectLike = false;
          break;
        }
        object[trimmed.slice(0, objectSplitAt).trim()] = parseScalar(trimmed.slice(objectSplitAt + 1).trim());
      }
      fields[key] = objectLike ? object : block.join('\n');
      warnings.push(`frontmatter key "${key}" uses nested object syntax; AKM lint preserves it but does not validate nested keys`);
    }
    i = j - 1;
  }

  return { fields, body, raw, warnings };
}

export function readMarkdown(file) {
  const text = readFileSync(file, 'utf8');
  return { text, frontmatter: parseFrontmatter(text) };
}

export function firstHeading(body) {
  const match = body.match(/^#{1,6}\s+(.+?)\s*#*\s*$/m);
  return match ? stripMarkdownInline(match[1].trim()) : null;
}

export function titleFromPath(file) {
  const stem = basename(file, '.md');
  return stem
    .split(/[-_]+/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function stripMarkdownInline(text) {
  return text
    .replace(/\[\[([^|\]]+)\|([^\]]+)\]\]/g, '$2')
    .replace(/\[\[([^\]]+)\]\]/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[*_`~]/g, '')
    .trim();
}

function normalizeAlias(value) {
  return String(value).replace(/\.md$/, '').trim();
}

export function buildMarkdownIndex(root) {
  const files = walk(root).filter((file) => file.endsWith('.md'));
  const targets = new Map();
  const duplicates = new Map();

  function add(key, file) {
    const normalized = normalizeAlias(key);
    if (!normalized) return;
    if (targets.has(normalized) && targets.get(normalized) !== file) {
      duplicates.set(normalized, [targets.get(normalized), file]);
      return;
    }
    targets.set(normalized, file);
  }

  for (const file of files) {
    const rel = posixRel(root, file);
    const noExt = rel.replace(/\.md$/, '');
    const base = basename(file, '.md');
    add(noExt, file);
    add(base, file);

    const { frontmatter } = readMarkdown(file);
    if (frontmatter?.fields.aliases && Array.isArray(frontmatter.fields.aliases)) {
      for (const alias of frontmatter.fields.aliases) add(alias, file);
    }
    const heading = frontmatter ? firstHeading(frontmatter.body) : null;
    if (heading) add(heading, file);
  }

  return { files, targets, duplicates };
}

export function resolveWikiTarget(root, fromFile, target, index = buildMarkdownIndex(root)) {
  const [pathPart, headingPart] = target.split('#');
  const cleanTarget = pathPart.trim().replace(/\.md$/, '');
  const candidates = [
    join(root, cleanTarget),
    join(root, `${cleanTarget}.md`),
    join(dirname(fromFile), cleanTarget),
    join(dirname(fromFile), `${cleanTarget}.md`),
  ];

  for (const candidate of candidates) {
    if (!existsSync(candidate)) continue;
    const stat = statSync(candidate);
    if (stat.isFile()) return { file: candidate, heading: headingPart };
    if (stat.isDirectory()) return { dir: candidate, heading: headingPart };
  }
  const indexed = index.targets.get(cleanTarget) ?? index.targets.get(basename(cleanTarget));
  return indexed ? { file: indexed, heading: headingPart } : null;
}

export function markdownAnchor(text) {
  return String(text)
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .replace(/\s+/g, '-');
}

export function convertWikilinksToMarkdown(text, root, fromFile, index = buildMarkdownIndex(root)) {
  return text.replace(/\[\[([^\]\n]+)\]\]/g, (full, inner) => {
    const [rawTarget, rawLabel] = inner.split('|');
    const label = rawLabel?.trim() || rawTarget.split('#')[0].trim();
    const resolved = resolveWikiTarget(root, fromFile, rawTarget, index);
    if (!resolved) {
      const fallback = rawTarget.split('#')[0].trim().replace(/\.md$/, '');
      const fallbackHref = `/${fallback.split('/').map((part) => slugPathPart(part)).join('/')}.md`;
      return `[${label}](${fallbackHref})`;
    }
    const targetPath = resolved.file ?? resolved.dir;
    const suffix = resolved.dir ? '/' : '';
    const href = `/${posixRel(root, targetPath)}${suffix}${resolved.heading ? `#${markdownAnchor(resolved.heading)}` : ''}`;
    return `[${label}](${href})`;
  });
}

function slugPathPart(part) {
  return String(part)
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/^-+|-+$/g, '');
}

export function extractUrls(text) {
  const urls = [];
  for (const match of text.matchAll(/\[[^\]]+\]\((https?:\/\/[^)\s]+)\)/g)) urls.push(match[1]);
  for (const match of text.matchAll(/(?<!\()https?:\/\/[^\s)]+/g)) urls.push(match[0]);
  return [...new Set(urls)];
}

export function normalizeTimestamp(value) {
  if (!value) return null;
  const text = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return `${text}T00:00:00Z`;
  const date = new Date(text);
  if (Number.isNaN(date.valueOf())) return text;
  return date.toISOString();
}

function quoteYaml(value) {
  return JSON.stringify(String(value));
}

export function formatYaml(fields) {
  const lines = ['---'];
  for (const [key, value] of Object.entries(fields)) {
    if (value === undefined || value === null || value === '') continue;
    if (Array.isArray(value)) {
      lines.push(`${key}:`);
      for (const item of value) lines.push(`  - ${quoteYaml(item)}`);
      continue;
    }
    lines.push(`${key}: ${quoteYaml(value)}`);
  }
  lines.push('---');
  return `${lines.join('\n')}\n`;
}

export function okfTypeFromAkmType(akmType) {
  if (!akmType) return null;
  return String(akmType)
    .split('-')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function isExternalHref(href) {
  return /^(https?:|mailto:|tel:)/.test(href) || href.startsWith('#');
}

export function findMarkdownLinks(text) {
  const links = [];
  const clean = stripCode(text);
  for (const match of clean.matchAll(/!?\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g)) {
    if (match[0].startsWith('!')) continue;
    links.push({ label: match[1], href: match[2] });
  }
  return links;
}

export function resolveMarkdownHref(root, fromFile, href) {
  const cleanHref = href.split('#')[0];
  if (!cleanHref || isExternalHref(href)) return true;
  const resolved = cleanHref.startsWith('/')
    ? join(root, cleanHref.slice(1))
    : join(dirname(fromFile), cleanHref);
  return existsSync(resolved);
}

export function layerNotes(root) {
  return walk(root).filter((file) => {
    if (!file.endsWith('.md')) return false;
    const top = posixRel(root, file).split('/')[0];
    return top in LAYER_BY_DIR || top === '90-archive';
  });
}
