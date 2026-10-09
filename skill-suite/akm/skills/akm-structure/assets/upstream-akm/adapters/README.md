# AKM Adapter Specification

An adapter is the **thin entry point** that makes a harness (agent runtime) read and write the AKM core.
Adapters never duplicate core rules — they only point at them. The rules themselves always live in `99-system/`.

## The four questions every adapter must answer

| # | Item | Meaning |
|---|---|---|
| ① | AKM root path | The absolute path where the harness finds the core |
| ② | Files to read at session start | Minimum: everything in `40-memory/` + `99-system/INDEX.md` |
| ③ | Where the routing rules live | Every save must pass the classification tree in `99-system/ROUTER.md` |
| ④ | Learn Back trigger | On failure or repeated mistakes, apply the mapping table in `99-system/LOOP.md` |

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

## Compliance checklist (after install)

Run a fresh session and verify the agent actually follows the system — installation is not compliance:

- [ ] Reads `40-memory/` and `99-system/INDEX.md` before using knowledge
- [ ] Consults `99-system/ROUTER.md` before storing anything (ask it to store a preference and a procedure; check where they land)
- [ ] Selects the applicable Tier 0–3 checks in `99-system/VERIFICATION.md` before declaring durable, public, or high-stakes work complete
- [ ] Consults `99-system/LOOP.md` on failure and records under `70-evaluation/`
- [ ] Updates `INDEX.md` and appends to `LOG.md` when creating notes — without being asked
- [ ] Does not duplicate content between its native memory and AKM (one body, pointers elsewhere)
- [ ] Refuses to store secret values, per `99-system/SECURITY.md`

A worked test script for this checklist is in [custom/README.md](custom/README.md) ("Verify your adapter").

## Adapters

- [claude-code](claude-code/README.md) — `CLAUDE.md` snippet + auto-memory / skills division
- [codex](codex/README.md) — `AGENTS.md` snippet (no native memory)
- [openclaw](openclaw/README.md) — `AGENTS.md` snippet + `MEMORY.md` / daily-log division
- [custom](custom/README.md) — write your own adapter for any agent in four steps
- [aside](aside/README.md) — Aside `AGENTS.md` + native memory pointers to the local AKM instance
- [hermes](hermes/README.md) — multi-profile agent: native memory/brain as pointers, one shared AKM instance
