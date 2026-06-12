# AKM Adapter Specification

An adapter is the **thin entry point** that makes a harness (agent runtime) read and write the AKM core.
Adapters never duplicate core rules — they only point at them. The rules themselves always live in `00-system/`.

## The four questions every adapter must answer

| # | Item | Meaning |
|---|---|---|
| ① | AKM root path | The absolute path where the harness finds the core |
| ② | Files to read at session start | Minimum: everything in `40-memory/` + `00-system/INDEX.md` |
| ③ | Where the routing rules live | Every save must pass the classification tree in `00-system/ROUTER.md` |
| ④ | Learn Back trigger | On failure or repeated mistakes, apply the mapping table in `00-system/LOOP.md` |

Each adapter README fills in this table. If any cell is empty, it is not an adapter.

## Division of labor with native memory (shared principle)

When a harness has its own memory (Claude Code auto-memory, OpenClaw `MEMORY.md`, a custom agent's brain):

- **Native memory**: operating pointers needed only by that harness + a pointer to the AKM root
- **AKM `40-memory/`**: operating rules every harness must share
- Never write the same content in both places. One body; everywhere else, pointers

## Installation (shared)

1. Paste the adapter's snippet into the harness entry file (`CLAUDE.md` / `AGENTS.md` / your agent's system prompt) and replace `/path/to/akm` with your clone location
2. Zero-setup alternative: run your agent **inside the cloned repo** — the root `CLAUDE.md` and `AGENTS.md` already contain the rules with relative paths
3. Verify in a fresh session: ask the agent to find and to store something, and check it follows ROUTER

## Adapters

- [claude-code](claude-code/README.md) — `CLAUDE.md` snippet + auto-memory / skills division
- [codex](codex/README.md) — `AGENTS.md` snippet (no native memory)
- [openclaw](openclaw/README.md) — `AGENTS.md` snippet + `MEMORY.md` / daily-log division
- [custom](custom/README.md) — write your own adapter for any agent in four steps
