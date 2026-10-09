import { readFileSync } from 'node:fs';
import { extname } from 'node:path';

export function readStructuredFile(file) {
  const text = readFileSync(file, 'utf8');
  const extension = extname(file).toLowerCase();

  if (extension === '.json') return JSON.parse(text);
  if (extension === '.jsonl') {
    const entries = text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line, index) => {
        try {
          return JSON.parse(line);
        } catch (error) {
          throw new Error(`invalid JSONL at line ${index + 1}: ${error.message}`);
        }
      });
    return { schemaVersion: '1.0.0', entries };
  }

  if (extension === '.md') {
    const matches = [...text.matchAll(/```json\s*\n([\s\S]*?)\n```/g)];
    if (matches.length !== 1) {
      throw new Error(`Markdown input must contain exactly one fenced JSON object (found ${matches.length})`);
    }
    return JSON.parse(matches[0][1]);
  }

  throw new Error(`unsupported input extension: ${extension || '(none)'}`);
}
