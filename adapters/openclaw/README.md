# OpenClaw Adapter

## The four questions

| # | Item | Value |
|---|---|---|
| ① | AKM root | `/path/to/akm` (your clone location) |
| ② | Session start | All of `40-memory/` + `00-system/INDEX.md` (instructed by the `AGENTS.md` snippet) |
| ③ | Routing | Every save passes the classification tree in `00-system/ROUTER.md` |
| ④ | Learn Back | On failure or repeated mistakes, apply the mapping table in `00-system/LOOP.md`. Daily-log promotions also pass through ROUTER |

## Installation

Paste the snippet below into your OpenClaw workspace `AGENTS.md` (loaded at every session start), replacing `/path/to/akm`.

```markdown
## AKM Knowledge System

Knowledge system root: `/path/to/akm` (AKM)

- When you need knowledge, context, or procedures, first read AKM `00-system/INDEX.md` and all files in `40-memory/` (both are short)
- Lookup: INDEX → layer folder (`20-knowledge` knowledge, `30-context` context, `50-procedures` procedures)
- Before saving any knowledge, experience, or procedure, follow the classification tree in `00-system/ROUTER.md`. Never save to arbitrary locations
- On task failure or repeated mistakes, follow the Learn Back mapping table in `00-system/LOOP.md`: record under `70-evaluation/` and fix the designated layer
- Never modify originals in `10-sources/`. Update `00-system/INDEX.md` when adding or removing notes, and append one line to `00-system/LOG.md` for meaningful changes
```

## Division of labor with OpenClaw workspace files

OpenClaw has two-layer memory: `MEMORY.md` (long-term, loaded every DM session) + `memory/YYYY-MM-DD.md` (daily logs; today's and yesterday's load automatically).

| OpenClaw file | Division |
|---|---|
| `AGENTS.md` | The snippet above + OpenClaw-specific behavior rules only |
| `MEMORY.md` | OpenClaw-only pointers (personal facts, preferences) + a pointer to the AKM root. Rules or knowledge that other harnesses should share go to AKM |
| `memory/YYYY-MM-DD.md` | Volatile work logs (outside AKM). However, **when promoting an item, do not send it straight to `MEMORY.md` — pass it through ROUTER**: reusable knowledge → `20-knowledge/`, repeated procedure → `50-procedures/`, failure → `70-evaluation/`, only short operating rules → `MEMORY.md` or `40-memory/` |
| `SOUL.md` / `IDENTITY.md` / `USER.md` | Not AKM's concern (persona, identity). Tool-agnostic user context from `USER.md` may live in `30-context/users/` with a pointer back |

References: [OpenClaw Agent workspace](https://docs.openclaw.ai/concepts/agent-workspace), [Memory overview](https://docs.openclaw.ai/concepts/memory)
