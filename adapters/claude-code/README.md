# Claude Code Adapter

## The four questions

| # | Item | Value |
|---|---|---|
| ① | AKM root | `/path/to/akm` (your clone location) |
| ② | Session start | All of `40-memory/` + `00-system/INDEX.md` (instructed by the snippet) |
| ③ | Routing | Every save passes the classification tree in `00-system/ROUTER.md` |
| ④ | Learn Back | On failure or repeated mistakes, apply the mapping table in `00-system/LOOP.md` |

## Installation

Paste the snippet below into `~/.claude/CLAUDE.md` (global) or a project `CLAUDE.md`, replacing `/path/to/akm`.
(If you run Claude Code *inside* the cloned repo, the root `CLAUDE.md` already covers this — no installation needed.)

```markdown
## AKM Knowledge System

Knowledge system root: `/path/to/akm` (AKM)

- When you need knowledge, context, or procedures, first read AKM `00-system/INDEX.md` and all files in `40-memory/` (both are short)
- Lookup: INDEX → layer folder (`20-knowledge` knowledge, `30-context` context, `50-procedures` procedures)
- Before saving any knowledge, experience, or procedure, follow the classification tree in `00-system/ROUTER.md`. Never save to arbitrary locations
- On task failure or repeated mistakes, follow the Learn Back mapping table in `00-system/LOOP.md`: record under `70-evaluation/` and fix the designated layer
- Never modify originals in `10-sources/`. Update `00-system/INDEX.md` when adding or removing notes, and append one line to `00-system/LOG.md` for meaningful changes
```

## Division of labor with Claude Code native features

| Claude Code feature | Division |
|---|---|
| auto-memory (`~/.claude/projects/*/memory/`) | Session/project-scoped volatile pointers only. Knowledge or rules that other tools should share go to AKM; leave a one-line pointer to the AKM path in memory |
| `.claude/skills/` | Procedure bodies live in AKM `50-procedures/`. Write a Claude Code skill only as a trigger + "read and execute the corresponding AKM procedure" wrapper |
| `CLAUDE.md` | The snippet above + Claude-Code-specific tool settings only. No domain knowledge |
