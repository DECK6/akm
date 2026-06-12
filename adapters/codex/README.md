# Codex Adapter

## The four questions

| # | Item | Value |
|---|---|---|
| ① | AKM root | `/path/to/akm` (your clone location) |
| ② | Session start | All of `40-memory/` + `00-system/INDEX.md` (instructed by the snippet) |
| ③ | Routing | Every save passes the classification tree in `00-system/ROUTER.md` |
| ④ | Learn Back | On failure or repeated mistakes, apply the mapping table in `00-system/LOOP.md` |

## Installation

Paste the snippet below into `~/.codex/AGENTS.md` (global) or an `AGENTS.md` at your working repo root, replacing `/path/to/akm`.
(If you run Codex *inside* the cloned repo, the root `AGENTS.md` already covers this — no installation needed.)

```markdown
## AKM Knowledge System

Knowledge system root: `/path/to/akm` (AKM)

- When you need knowledge, context, or procedures, first read AKM `00-system/INDEX.md` and all files in `40-memory/` (both are short)
- Lookup: INDEX → layer folder (`20-knowledge` knowledge, `30-context` context, `50-procedures` procedures)
- Before saving any knowledge, experience, or procedure, follow the classification tree in `00-system/ROUTER.md`. Never save to arbitrary locations
- On task failure or repeated mistakes, follow the Learn Back mapping table in `00-system/LOOP.md`: record under `70-evaluation/` and fix the designated layer
- Never modify originals in `10-sources/`. Update `00-system/INDEX.md` when adding or removing notes, and append one line to `00-system/LOG.md` for meaningful changes
```

## Codex specifics

- Codex has no native long-term memory → **all persistent memory lives in AKM**. Whenever something must be remembered across sessions, route it through ROUTER into AKM
- When Codex is used as a subagent (outsourced worker), the caller must pass the AKM path and ROUTER rule explicitly in the prompt (for environments where `AGENTS.md` is not loaded)
