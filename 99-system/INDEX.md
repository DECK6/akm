# AKM-INDEX

Full note list with one-line summaries. Update this file whenever notes are added or removed.

> Keeping a private instance in a public clone? List your instance notes in `INDEX.local.md` (gitignored) instead of here, and this file stays conflict-free when pulling system updates. If `INDEX.local.md` exists, read it together with this file.

## 99-system

- [[SCHEMA]] — frontmatter standard, enum values, layer↔folder mapping
- [[ROUTER]] — security pre-check + classification decision tree + four storage judgment rules
- [[LOOP]] — seven-step operating loop + Learn Back mapping table
- [[VERIFICATION]] — DEER-informed risk tiers, seven-dimension rubric, claim checks, verdicts, and Learn Back routing
- [[SECURITY]] — no secret values, private layers, output review rules
- [[EXTERNAL-ASSETS]] — keep large binaries outside the text vault while preserving relative-path traceability
- [[MIGRATION]] — phased consolidation guide for adopting an existing Markdown or Obsidian vault
- [[OKF-COMPAT]] — OKF-compatible export/import boundary, field mapping, indexes, and lint expectations
- [[MANIFEST]] — AKM and OKF compatibility version declarations
- [[GLOSSARY]] — terminology
- [[INDEX]] — this file
- [[LOG]] — change history
- `templates/` — 12 note templates: concept, entity, comparison, skill, failure-pattern, decision, audit, rubric, verification, claim-ledger, run, handoff
- `../scripts/lint.mjs` — zero-dependency validator (AKM strict mode, OKF export mode, links, secrets)
- `../scripts/export-okf.mjs` — exports selected AKM layers as an OKF-compatible bundle
- `../scripts/index.mjs` — generates directory-level `INDEX.local.md` or OKF `index.md` files

## 10-sources

(empty)

## 20-knowledge

(empty)

## 30-context

(empty)

## 40-memory

(empty)

## 50-procedures

(empty)

## 60-actions

(empty)

## 70-evaluation

(empty)

## 80-outputs

(empty)

## adapters

- [README](../adapters/README.md) — adapter specification (four questions, native-memory division principle)
- [claude-code](../adapters/claude-code/README.md) — CLAUDE.md snippet + auto-memory/skills division
- [codex](../adapters/codex/README.md) — AGENTS.md snippet, subagent rule passing
- [openclaw](../adapters/openclaw/README.md) — AGENTS.md snippet + MEMORY.md/daily-log division
- [custom](../adapters/custom/README.md) — write an adapter for any agent
- [aside](../adapters/aside/README.md) — Aside instructions + native-memory pointer division
- [hermes](../adapters/hermes/README.md) — multi-profile session instructions + shared AKM pointer division

## examples

- [minimal-akm](../examples/minimal-akm/) — small public AKM fixture showing ingest, compile, contextualize, execute, verify, learn back
- [okf-export](../examples/okf-export/) — OKF-compatible export generated from the minimal fixture
