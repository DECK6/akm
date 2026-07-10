import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const lint = join(here, '..', 'lint.mjs');
const fixtures = join(here, 'fixtures');

function runFixture(name) {
  const result = spawnSync(process.execPath, [lint, '--akm', join(fixtures, name)], {
    encoding: 'utf8',
  });
  return {
    ...result,
    output: `${result.stdout ?? ''}${result.stderr ?? ''}`,
  };
}

function runLinks(root) {
  const result = spawnSync(process.execPath, [lint, '--links', root], {
    encoding: 'utf8',
  });
  return {
    ...result,
    output: `${result.stdout ?? ''}${result.stderr ?? ''}`,
  };
}

test('opaque source and output Markdown may omit AKM frontmatter', () => {
  const result = runFixture('opaque-source-output');
  assert.equal(result.status, 0, result.output);
  assert.match(result.output, /0 error\(s\)/);
});

test('managed notes still require complete frontmatter', () => {
  const result = runFixture('managed-missing-frontmatter');
  assert.equal(result.status, 1, result.output);
  assert.match(result.output, /E1 20-knowledge\/missing\.md/);
});

test('source and output notes opting into AKM fields require the full schema', () => {
  const result = runFixture('partial-source-schema');
  assert.equal(result.status, 1, result.output);
  assert.match(result.output, /E2 10-sources\/partial\.md/);
});

test('production enum additions are accepted', () => {
  const result = runFixture('production-enums');
  assert.equal(result.status, 0, result.output);
  assert.doesNotMatch(result.output, /E5/);
});

test('an indexed directory covers notes below it', () => {
  const result = runFixture('directory-index-coverage');
  assert.equal(result.status, 0, result.output);
  assert.doesNotMatch(result.output, /W2/);
});

test('nested _archive snapshots do not create duplicate-basename warnings', () => {
  const result = runFixture('nested-archive');
  assert.equal(result.status, 0, result.output);
  assert.doesNotMatch(result.output, /W4/);
});

test('root link lint defers nested OKF bundles to their own root', () => {
  const fixtureRoot = join(fixtures, 'nested-okf-bundle');
  const rootResult = runLinks(fixtureRoot);
  assert.equal(rootResult.status, 0, rootResult.output);
  assert.doesNotMatch(rootResult.output, /W5/);

  const bundleResult = runLinks(join(fixtureRoot, 'examples', 'okf-export'));
  assert.equal(bundleResult.status, 0, bundleResult.output);
  assert.doesNotMatch(bundleResult.output, /W5/);
});
