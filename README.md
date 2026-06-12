# AKM — Agent Knowledge Management

A universal, tool-agnostic knowledge system for AI agents. Plain Markdown, no database, no code to run. Works with **Claude Code**, **Codex**, **OpenClaw**, and any agent that can read files.

> An LLM wiki gives an agent a *map* of knowledge. AKM gives it an *operating system* for knowledge: what to learn, where to store it, how to act on it, how to verify results, and where failures go so the next run is better.

## Why

Agents forget. Plain RAG re-interprets the same documents every session, good syntheses evaporate when the session ends, and the same mistakes repeat. Compiled Markdown wikis (e.g. Karpathy's LLM Wiki pattern) fix the *knowledge* half — but knowing is not operating. AKM keeps the wiki pattern as its knowledge layer and adds operational memory, context, procedures, selective action logging, and an evaluation loop, so agents don't just know more — they work better over time.

The core idea is **separation of stores**. Long external knowledge, short operating rules, repeatable procedures, execution records, and verification criteria each fail differently when mixed. AKM stores them apart and reconnects them with wikilinks and frontmatter.

## The seven layers

| # | Layer | Folder | One-line rule |
|---|-------|--------|---------------|
| 1 | Source | `10-sources/` | Originals, never modified. Provenance tracked |
| 2 | Knowledge | `20-knowledge/` | Compiled, reusable knowledge — true for anyone |
| 3 | Context | `30-context/` | True only for this user / org / project / domain |
| 4 | Operational Memory | `40-memory/` | Short, stable pointers the agent must know every session |
| 5 | Procedural | `50-procedures/` | How to execute — skills, workflows, checklists |
| 6 | Action | `60-actions/` | Selected execution records — only what's needed for reproduction, verification, handoff |
| 7 | Evaluation | `70-evaluation/` | Failure patterns, rubrics, audits — where failures become learning |

Plus two auxiliary layers: `80-outputs/` (deliverables) and `90-archive/` (deprecated notes).

## Three stores: memory, brain, vault

The seven layers group into three stores — the agent's mental model for *when* things get read:

```text
┌─ MEMORY  what loads every session ········ 40-memory
├─ BRAIN   how the agent works ············· 50-procedures · 60-actions · 70-evaluation
└─ VAULT   what the agent knows ············ 10-sources · 20-knowledge · 30-context · 80-outputs
```

- **Memory** is read first, always. Pointers only.
- **Brain** is read when acting: the procedure to follow, past decisions, failure patterns to avoid.
- **Vault** is read when knowledge is needed: sources, compiled knowledge, context, deliverables.

The layers define *storage semantics* (what goes where); the stores define *loading behavior* (when it gets read). If your agent already has its own brain or memory system, see [`adapters/custom/`](adapters/custom/README.md) — keep it native, connect by pointers.

## The loop

```text
1. Ingest → 2. Classify → 3. Compile → 4. Contextualize → 5. Execute → 6. Verify → 7. Learn Back
                                                                                        │
                                                  ┌─────────────────────────────────────┘
                                                  ▼
                                   (the layer that gets fixed improves the next run)
```

Accumulating knowledge without steps 5–7 is just a wiki. Executing without 6–7 is just automation. **Learn Back** — routing every failure to the layer that must change — is what makes it AKM. See [`00-system/LOOP.md`](00-system/LOOP.md).

## Quick start

```bash
git clone https://github.com/<you>/akm.git
```

**Zero setup**: run your agent *inside* the cloned folder — root [`CLAUDE.md`](CLAUDE.md) and [`AGENTS.md`](AGENTS.md) are included, so Claude Code, Codex, and OpenClaw pick up the operating rules automatically.

To use AKM from anywhere:

1. **Pick your adapter** in [`adapters/`](adapters/):
   - [Claude Code](adapters/claude-code/README.md) → paste the snippet into `~/.claude/CLAUDE.md` or a project `CLAUDE.md`
   - [Codex](adapters/codex/README.md) → paste into `~/.codex/AGENTS.md` or a repo `AGENTS.md`
   - [OpenClaw](adapters/openclaw/README.md) → paste into your workspace `AGENTS.md`
   - [Any other agent](adapters/custom/README.md) → four questions every adapter must answer
2. **Replace `/path/to/akm`** in the snippet with your clone location.
3. **Use it.** Ask your agent to store or find anything. The snippet points it to the routing rules (`00-system/ROUTER.md`) and the loop (`00-system/LOOP.md`); everything else follows.

Your notes can be in any language — only the system files are English.

## Storage rules in 30 seconds

- **Memory (40)** only if *all* hold: short, stable, needed repeatedly, must be known before acting, a pointer suffices. Never put long knowledge here.
- **Knowledge (20)** if it's worth re-reading, reusable across projects, or domain knowledge itself.
- **Procedure (50)** only if *all* hold: repeated, has steps, has known failure points, has a verification method.
- **Evaluation (70)** if a failure may repeat, or a quality bar / verification method is needed.
- **Action (60)**: store only what reproduction, verification, or handoff requires. Everything else, drop.

Full decision tree: [`00-system/ROUTER.md`](00-system/ROUTER.md).

## Linting

Validate your instance — frontmatter schema, enum values, layer placement, broken wikilinks, INDEX consistency, and common secret patterns:

```bash
node scripts/lint.mjs    # or: bun scripts/lint.mjs
```

Schema violations are errors (exit 1); link/index/secret findings are warnings. Security and privacy rules — never store secret values, layers never leave the machine, review outputs before sharing — live in [`00-system/SECURITY.md`](00-system/SECURITY.md).

## Repository structure

```text
akm/
├── README.md
├── 00-system/          # SCHEMA (frontmatter standard), ROUTER (classification),
│   │                   # LOOP (operating loop), SECURITY, GLOSSARY, INDEX, LOG
│   └── templates/      # 11 note templates: concept, entity, comparison, skill,
│                       # failure-pattern, decision, audit, rubric, verification,
│                       # run, handoff
├── 10-sources/         ┐
├── 20-knowledge/       │
├── 30-context/         │
├── 40-memory/          │  your knowledge lives here —
├── 50-procedures/      │  local instance data, not tracked by git
├── 60-actions/         │
├── 70-evaluation/      │
├── 80-outputs/         │
├── 90-archive/         ┘
├── adapters/           # thin entry points per harness
└── scripts/            # lint.mjs — zero-dependency instance validator
```

The repo distributes the *system* (`00-system/`, `adapters/`, templates). What you store in the layers is *your instance* and is gitignored — clone once, use privately, pull system updates without conflicts.

## Design principles

1. **Core–adapter separation.** The core assumes no specific agent. Each harness connects through one thin entry-point snippet that points at the core — it never duplicates rules.
2. **Separated stores, reconnected by links.** Memory holds pointers, not knowledge. Skills hold procedures, not domain knowledge. Actions are stored selectively.
3. **Evaluation is not optional.** A failure is not an error to delete; it's a signal that must be routed back to the layer that caused it.
4. **One body, everywhere else pointers.** Native agent memories (Claude Code auto-memory, OpenClaw `MEMORY.md`, a custom agent's brain) keep harness-specific pointers; shared rules live in AKM. Never duplicate content across stores.
5. **No over-engineering.** Markdown + folders + frontmatter. Add code or databases only when file counts demand it.
6. **Generic structure, domain-specific taxonomy.** The layers never change per domain; domains extend inside the Knowledge and Context layers.

## Lineage

AKM is influenced by two prior patterns, and reduces to neither:

- **[Karpathy's LLM Wiki](https://karpathy.bearblog.dev/)** — compile sources into an LLM-readable Markdown knowledge base (`raw/`, `entities/`, `concepts/`, `SCHEMA/index/log`). AKM adopts this as its Knowledge Layer pattern.
- **CMDS (Connect → Merge → Develop → Share)** — a process grammar for how knowledge moves through its lifecycle. AKM uses it as routing metadata (`CMDS:` frontmatter), not as folders.

## License

[MIT](LICENSE)
