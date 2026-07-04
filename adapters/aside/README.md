# Aside Adapter

Connects the Aside browser (agentic browser with a local agent runtime) to an AKM instance without copying the vault into Aside's native memory.

## The four questions

| # | Item | Value |
|---|---|---|
| ① | AKM root | `/path/to/akm` (your clone location) |
| ② | Session start | Read `99-system/INDEX.md` (plus `99-system/INDEX.local.md` if present) and all files in `40-memory/` when durable knowledge, context, or procedures are needed |
| ③ | Routing | Every durable save passes the classification tree in `99-system/ROUTER.md` |
| ④ | Learn Back | On failure, repeated mistakes, or missing verification criteria, apply the mapping table in `99-system/LOOP.md` |

## Installation

Aside keeps its agent files under a local agent root (default: `~/.aside/u/0/agents/main`). Install the adapter across these entry points:

- `AGENTS.md` — paste the operating snippet below (standing AKM adapter rules).
- `memory/MEMORY.md` — keep only a compact one-line AKM pointer, not content.
- `memory/USER.md` — keep only the durable AKM root path pointer.
- `memory/agent/` / `memory/projects/` — optional short semantic pointer pages for retrieval; bodies stay in AKM.

## Aside operating snippet

```markdown
## AKM Knowledge System

Knowledge system root: `/path/to/akm` (local AKM instance). Treat the local path as authoritative for this agent.

- When I need the user's durable knowledge, project context, or repeatable procedures, first read AKM `99-system/INDEX.md` and all files in `40-memory/` if they exist. If `99-system/INDEX.local.md` exists, read it together with `INDEX.md`.
- Lookup flow: AKM INDEX -> relevant layer folder: `20-knowledge/` for reusable knowledge, `30-context/` for user/project/domain context, `50-procedures/` for procedures, `70-evaluation/` for rubrics/failure patterns.
- Before saving durable knowledge, experience, preference, procedure, decision, or failure into AKM, follow `99-system/ROUTER.md`. Do not save to arbitrary locations.
- Inbox-first rule: new intake normally lands in AKM `00-inbox/` first, then is classified by `99-system/ROUTER.md` before final placement. Exceptions are explicit archival originals in `10-sources/` and selected execution logs in `60-actions/runs/`.
- On task failure, repeated mistakes, or missing verification criteria, follow `99-system/LOOP.md` Learn Back: record the finding under `70-evaluation/`, then fix the responsible layer.
- Never modify originals in AKM `10-sources/`. Update the INDEX when adding/removing notes and append one line to `99-system/LOG.md` for meaningful changes.
- Follow AKM `99-system/SECURITY.md` before storage: never store secret values; store only secret names/locations when needed.
- Do not duplicate long AKM content in Aside native memory. Aside memory keeps short Aside-specific pointers; the body of shared knowledge stays in AKM. One body, pointers elsewhere.
```

## Division of labor with Aside native memory

AKM principle: **one body, everywhere else pointers.**

| Aside surface | Division |
|---|---|
| `AGENTS.md` | Thin standing adapter rules only |
| `memory/MEMORY.md` | Short operating pointer loaded at session start |
| `memory/USER.md` | User-level pointer to the AKM root |
| `memory/agent/` / `memory/projects/` | Aside-specific semantic pointer pages |
| AKM layers | The actual shared knowledge, context, procedures, decisions, failures, and outputs |

Do not bulk-copy AKM notes into Aside memory. If another harness would need the body, store the body in AKM and keep only a path/wikilink pointer in Aside.

## Verification checklist

- Ask Aside where recurring mistakes should be recorded: it should answer `70-evaluation/failure-patterns/` plus a `40-memory/` pointer if session-critical.
- Ask Aside where a durable user/project-specific constraint belongs: it should answer `30-context/` plus a short memory pointer only if needed at session start.
- Ask Aside where a repeatable procedure with failure points and verification belongs: it should answer `50-procedures/` and use AKM templates/routing.
- Confirm Aside does not copy long AKM note bodies into native memory.
