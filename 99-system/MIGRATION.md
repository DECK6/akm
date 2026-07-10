# Migrating an Existing Vault into AKM

AKM can run beside an existing knowledge vault or become the primary Markdown/Obsidian vault. Consolidation is safer when treated as a sequence of verified moves, not a bulk folder rename.

## 1. Freeze the migration contract

Before moving files:

1. Make a restorable backup outside both the source and target vaults.
2. Inventory source folders, file counts, large binaries, automations, retrieval indexes, and agent entry points.
3. Map every source folder to exactly one AKM layer using `99-system/ROUTER.md`. Mark anything intentionally out of scope instead of forcing a fit.
4. Decide the frontmatter reconciliation rule. Preserve legacy fields under a clear namespace; do not overload AKM enum fields with source-system values.
5. Identify secrets, private conversations, credentials, and binary assets before copying. Apply `99-system/SECURITY.md` and `99-system/EXTERNAL-ASSETS.md` first.

## 2. Run a representative pilot

Choose a bounded slice that exercises the main risks: nested folders, wikilinks, aliases, frontmatter, source lineage, and at least one automation or retrieval path.

For the pilot:

1. Route each item through the classification tree.
2. Move managed notes into their target layers and add valid AKM metadata.
3. Keep unmodified Markdown originals in `10-sources/` opaque when editing them would violate source preservation; store metadata in a companion note or index.
4. Repair internal links and any paths referenced by procedures, jobs, or agents.
5. Run lint, link checks, and retrieval reindexing.
6. Smoke-test one real read path and one real write path.

Proceed only when the pilot has no blocking schema, link, secret, retrieval, or automation failures.

## 3. Expand one domain at a time

Repeat the pilot method for coherent domains rather than arbitrary file-count batches. A typical order is:

1. official or archival sources → `10-sources/`
2. reusable notes and guides → `20-knowledge/`
3. user, organization, project, and domain context → `30-context/`
4. repeatable procedures → `50-procedures/`
5. selected decisions, handoffs, and reproducible run records → `60-actions/`
6. failure patterns, rubrics, audits, and verification records → `70-evaluation/`
7. publishable deliverables → `80-outputs/`

After every domain, record counts and verification results in `60-actions/runs/`, update the local INDEX, and stop on a failed gate.

## 4. Cut over integrations

Once content is stable:

- Point agent adapters at the AKM root and keep native agent memories as short pointers.
- Repoint scheduled jobs, scripts, and output paths from the old vault to AKM.
- Rebuild text search, embeddings, or document graphs from the new root.
- Open the AKM folder directly in Obsidian if desired; keep `.obsidian/` local state untracked.
- Verify several real sessions before retiring the old source vault.

## 5. Retire without losing rollback

One body, pointers elsewhere: after cutover, do not keep two writable authoritative copies. Preserve the old vault as a read-only backup or move it to Trash only after the new vault has passed real-session checks. Permanently delete nothing during migration unless the owner explicitly requests it and a verified backup exists.

The migration is complete when agents, scheduled jobs, retrieval tools, and human vault use all resolve to the AKM root, and the old vault is no longer receiving writes.
