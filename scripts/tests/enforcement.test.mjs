import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const testDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(testDir, '../..');
const cli = resolve(repoRoot, 'scripts/lint.mjs');
const fixtures = resolve(repoRoot, 'scripts/fixtures/enforcement');

function run(flag, fixture) {
  return spawnSync(process.execPath, [cli, flag, resolve(fixtures, fixture)], {
    cwd: repoRoot,
    encoding: 'utf8',
  });
}

function assertPassFail(flag, passFixture, failFixture) {
  const pass = run(flag, passFixture);
  assert.equal(pass.status, 0, `${flag} passing fixture failed:\n${pass.stderr}\n${pass.stdout}`);

  const fail = run(flag, failFixture);
  assert.notEqual(fail.status, 0, `${flag} failing fixture unexpectedly passed`);
  assert.match(`${fail.stderr}\n${fail.stdout}`, /ERROR/);
}

test('instruction audit accepts declared precedence and rejects unresolved conflicts', () => {
  assertPassFail('--instructions', 'prompt-audit-pass.json', 'prompt-audit-fail.json');

  const sensitive = run('--instructions', 'prompt-audit-fail-sensitive-path.json');
  assert.notEqual(sensitive.status, 0);
  assert.match(`${sensitive.stderr}\n${sensitive.stdout}`, /excluded/);

  const escaping = run('--instructions', 'prompt-audit-fail-path-escape.json');
  assert.notEqual(escaping.status, 0);
  assert.match(`${escaping.stderr}\n${escaping.stdout}`, /escape/);
});

test('task-contract lint accepts bounded artifact work and rejects audit-only completion', () => {
  assertPassFail('--task-contract', 'task-contract-pass.json', 'task-contract-fail-audit-only.json');
});

test('task-contract lint rejects goal mode and overlong bounded runtime', () => {
  const result = run('--task-contract', 'task-contract-fail-unbounded-runtime.json');
  assert.notEqual(result.status, 0, 'open-ended bounded task unexpectedly passed');
  assert.match(`${result.stderr}\n${result.stdout}`, /goalMode|maxSeconds/);
});

test('task-contract lint rejects fields outside the canonical closed schema', () => {
  const result = run('--task-contract', 'task-contract-fail-extra-field.json');
  assert.notEqual(result.status, 0, 'contract with an undeclared nested field unexpectedly passed');
  assert.match(`${result.stderr}\n${result.stdout}`, /unexpected field/);
});

test('routing-failure lint accepts open metadata-only events and rejects unverified closure', () => {
  assertPassFail('--routing-failure', 'route-ledger-pass.json', 'route-ledger-fail.json');
});

test('prompt asset lifecycle is deterministic and rejects sensitive paths', () => {
  const first = run('--prompt-assets', 'prompt-manifest-pass.json');
  const second = run('--prompt-assets', 'prompt-manifest-pass.json');
  assert.equal(first.status, 0, first.stderr);
  assert.equal(second.status, 0, second.stderr);
  assert.equal(first.stdout, second.stdout);
  assert.doesNotMatch(first.stdout, /\/Volumes\/|\/Users\//);

  const sensitive = run('--prompt-assets', 'prompt-manifest-fail.json');
  assert.notEqual(sensitive.status, 0);
  assert.match(`${sensitive.stderr}\n${sensitive.stdout}`, /excluded/);

  const missingChangelog = run('--prompt-assets', 'prompt-manifest-fail-missing-changelog.json');
  assert.notEqual(missingChangelog.status, 0);
  assert.match(`${missingChangelog.stderr}\n${missingChangelog.stdout}`, /changelog/);
});

test('enforcement modes never mutate their inputs', () => {
  const fixture = resolve(fixtures, 'task-contract-pass.json');
  const before = readFileSync(fixture, 'utf8');
  const result = run('--task-contract', 'task-contract-pass.json');
  const after = readFileSync(fixture, 'utf8');
  assert.equal(result.status, 0);
  assert.equal(after, before);
});

test('unknown lint modes fail closed', () => {
  const result = spawnSync(process.execPath, [cli, '--not-a-real-mode'], {
    cwd: repoRoot,
    encoding: 'utf8',
  });
  assert.notEqual(result.status, 0);
});

test('task-contract schema is bounded and accepts portable owner identifiers', () => {
  const schema = JSON.parse(readFileSync(resolve(repoRoot, '99-system/task-contract.schema.json'), 'utf8'));
  const required = [
    'contractVersion', 'taskId', 'purpose', 'inputs', 'outputs', 'canonicalPath',
    'format', 'sources', 'owner', 'failureHandling', 'completion', 'verification',
    'runtime', 'nonGoals', 'securityExclusions', 'blockers',
  ];
  assert.deepEqual(schema.required, required);
  assert.equal(schema.properties.runtime.properties.maxSeconds.maximum, 5400);
  assert.equal(schema.properties.runtime.properties.goalMode.const, false);
  assert.equal(schema.properties.owner.properties.primary.type, 'string');
  assert.equal(schema.properties.owner.properties.primary.enum, undefined);
});

test('evidence schema preserves candidate, direct-read, and claim-support boundaries', () => {
  const schema = JSON.parse(readFileSync(resolve(repoRoot, '99-system/evidence-row.schema.json'), 'utf8'));
  assert.equal(schema.$schema, 'https://json-schema.org/draft/2020-12/schema');
  assert.ok(schema.$defs.EvidenceRow.required.includes('verification'));
  assert.ok(schema.$defs.EvidencePacket.required.includes('directReadQueue'));
  assert.ok(schema.$defs.EvidencePacket.required.includes('claims'));
  assert.ok(schema.$defs.Claim.required.includes('supportRowIds'));
  assert.ok(schema.$defs.Verification.properties.state.enum.includes('candidate'));
  assert.ok(schema.$defs.Verification.properties.state.enum.includes('direct-read'));
});

test('public evidence templates contain no live-instance owner or machine path', () => {
  const evidence = readFileSync(resolve(repoRoot, '99-system/EVIDENCE-SCHEMA.md'), 'utf8');
  const manifest = readFileSync(resolve(repoRoot, '99-system/templates/project-retrieval-manifest.yaml'), 'utf8');
  assert.doesNotMatch(`${evidence}\n${manifest}`, /\/Volumes\/|\/Users\/|Hermes Agent|owner: "pkm"|pkm-worker/);
  assert.match(manifest, /defaultDecision: "deny"/);
  assert.match(manifest, /schemaRef: "99-system\/EVIDENCE-SCHEMA.md"/);
});
