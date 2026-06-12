# AKM-SCHEMA

The frontmatter standard and storage rules every Markdown note in the AKM core follows.
This file is the single source of truth. Harness-specific extra fields are defined in each adapter and must not conflict with the fields defined here.

## Layer ↔ folder mapping

| akmLayer | Folder | Role |
|---|---|---|
| `source` | `10-sources/` | Original preservation (never modified) |
| `knowledge` | `20-knowledge/` | Compiled reusable knowledge |
| `context` | `30-context/` | User / org / project / domain context |
| `operational-memory` | `40-memory/` | Short, stable operating pointers |
| `procedure` | `50-procedures/` | Repeatable execution procedures |
| `action` | `60-actions/` | Selected execution records, decisions, handoffs |
| `evaluation` | `70-evaluation/` | Verification, failure patterns, quality criteria |
| `output` | `80-outputs/` | Deliverables for external use |
| (none) | `90-archive/` | End-of-life notes — keep original frontmatter, set `trustLevel: deprecated` |

## Frontmatter standard

### Required fields

| Field | Format | Description |
|---|---|---|
| `description` | string (English) | Retrieval hint for LLMs. One English sentence |
| `akmLayer` | enum | See allowed values below |
| `akmType` | enum | See allowed values below |
| `trustLevel` | enum | See allowed values below |
| `date created` | YYYY-MM-DD | Creation date |
| `date modified` | YYYY-MM-DD | Last modification date |

### Optional fields

| Field | Format | Description |
|---|---|---|
| `akmRole` | enum | The role this note plays in the system |
| `CMDS` | enum | Current stage in the knowledge lifecycle |
| `sourceType` | enum | Type of origin for the source/knowledge |
| `sourcePath` | string | External path of the original (required when ingesting into sources) |
| `usedBy` | list | Agents / skills / workflows / projects that reference this knowledge |
| `nextAction` | enum | What to do next |
| `aliases` | list | Alternative names |
| `tags` | list | Tags |

## Allowed values (enums)

### akmLayer

`source` | `knowledge` | `context` | `operational-memory` | `procedure` | `action` | `evaluation` | `output`

### akmRole

`raw-source` | `learned-reference` | `reusable-knowledge` | `operating-context` | `executable-procedure` | `verification-rule` | `deliverable`

### akmType

Allowed types per layer:

| akmLayer | Allowed akmType |
|---|---|
| source | `source` |
| knowledge | `concept`, `entity`, `comparison`, `pattern`, `principle`, `tool`, `technique`, `map` |
| context | `context` |
| operational-memory | `memory` |
| procedure | `skill`, `workflow`, `checklist`, `playbook` |
| action | `run`, `decision`, `handoff` |
| evaluation | `failure-pattern`, `recovery-note`, `rubric`, `audit`, `verification` |
| output | `output` |

### CMDS

`Connect` | `Merge` | `Develop` | `Share`

- Connect: intake of new material, interests, questions, tools, concepts
- Merge: combining sources into reusable synthesized knowledge
- Develop: evolving synthesized knowledge into procedures, skills, system designs, project applications
- Share: turning results into external documents, reports, products, publications

### sourceType

`transcript` | `article` | `paper` | `book` | `meeting` | `tool-doc` | `code` | `agent-output` | `synthesis`

### trustLevel

`raw` | `unverified` | `reviewed` | `canonical` | `deprecated`

- raw: original as-is, no interpretation
- unverified: synthesized but not yet verified
- reviewed: passed human or procedural verification
- canonical: the reference note for its topic
- deprecated: end of life (candidate for `90-archive/`)

### nextAction

`triage` | `merge` | `contextualize` | `develop-into-skill` | `verify` | `publish` | `archive`

## Example frontmatter

### knowledge note (concept)

```yaml
---
description: "Explains the seven-layer AKM architecture and why memory, knowledge, and procedures must be stored separately."
akmLayer: knowledge
akmRole: reusable-knowledge
akmType: concept
trustLevel: reviewed
CMDS: Merge
sourceType: synthesis
usedBy: []
nextAction: contextualize
date created: 2026-06-12
date modified: 2026-06-12
tags: [akm, architecture]
---
```

### source note (ingested original)

```yaml
---
description: "Raw snapshot of an external article about agent memory design."
akmLayer: source
akmRole: raw-source
akmType: source
trustLevel: raw
CMDS: Connect
sourceType: article
sourcePath: "https://example.com/agent-memory-design"
nextAction: merge
date created: 2026-06-12
date modified: 2026-06-12
---
```

### failure-pattern note

```yaml
---
description: "Recurring failure: long domain knowledge stored in operational memory pollutes the agent brain."
akmLayer: evaluation
akmRole: verification-rule
akmType: failure-pattern
trustLevel: reviewed
nextAction: verify
date created: 2026-06-12
date modified: 2026-06-12
---
```

## File rules

- Filenames: kebab-case English. Example: `akm-seven-layer-architecture.md`
- Originals (`10-sources/`) use `YYYY-MM-DD-<original-name>.md` and are never modified after ingest. Interpretation and summary happen in `20-knowledge/`
- `40-memory/` uses **cumulative files per topic** (e.g. `user-preferences.md`). 1–3 lines per item plus a wikilink to the full note. The whole folder is loaded every session, so do not fragment it into many small files. Memory notes omit `akmRole`
- `30-context/users/` filenames are the user's handle or account name in kebab-case (e.g. `alice.md`)
- One file = one topic. Split files that mix topics
- Reference other notes with `[[wikilinks]]` (no file extension)
- The AKM core uses only `akm*`-prefixed custom fields to avoid colliding with fields from other systems (e.g. an Obsidian vault's `type`). When syncing a note into another system, the adapter adds that system's fields
