# Claude Code Adapter

## Install the knowledge-management skills

From the repository root, with Python 3.10+:

```sh
python3 skill-suite/akm/scripts/install.py --host claude
```

This links all 15 roles into `CLAUDE_CONFIG_DIR/skills` when set, otherwise `~/.claude/skills`. Existing entries are preserved; re-running is idempotent for the same source. Keep the clone in place. For a project-local installation, add `--dest /path/to/project/.claude/skills`.

In Claude Code, start with:

```text
/akm 온톨로지 구축 시작해줘
/akm 이 자료를 기존 위키와 온톨로지에 반영해줘
/akm 빠진 연결을 보완하고 완결성을 검사해줘
```

Specialist commands such as `/akm-discover`, `/akm-grow`, and `/akm-maintain` are also available. Natural-language selection follows each skill's description. If a running session does not show the new skills, start a fresh session and check `/skills`. The interview, three initial notes, shared ontology/wiki and continuing operations use the same instructions as Codex.

Update from this clone's root with `git pull --ff-only`, then rerun the installer with `--host claude` to include new roles. This does not change Codex's installation or edit global instructions.

### Session-only plugin alternative

Instead of linking personal skills, load the complete package for one session:

```sh
claude --plugin-dir /absolute/path/to/akm/skill-suite/akm
```

Plugin commands are namespaced: `/akm:akm` is the entry point, with `/akm:akm-discover` and other roles underneath it. The manifest, skills, references, scripts and pinned assets travel together. No marketplace registration or global plugin setting is required. Use one installation mode for a given session to keep the command list clear.

These layouts follow the official [skill locations and invocation rules](https://code.claude.com/docs/en/skills) and [plugin manifest reference](https://code.claude.com/docs/en/plugins-reference). Configuration-directory overrides are documented in the [Claude directory guide](https://code.claude.com/docs/en/claude-directory). Installation and native manifest validation are distinct from verifying domain answers; see [validation](../../skill-suite/VALIDATION.md).

## Connect an existing Markdown core

The snippet below is for a knowledge workspace that already uses the full AKM core. It does not install the 15 skills. A workspace created through the interview uses its own selected layers and generated rules; do not replace them with a full-layer snippet.

### The four questions

| # | Item | Value |
|---|---|---|
| ① | AKM root | `/path/to/akm` (your clone location) |
| ② | Session start | All of `40-memory/` + `99-system/INDEX.md` (instructed by the snippet) |
| ③ | Routing | Every save passes the classification tree in `99-system/ROUTER.md` |
| ④ | Learn Back | On failure or repeated mistakes, apply the mapping table in `99-system/LOOP.md` |

### Core instruction snippet

Paste the snippet below into `~/.claude/CLAUDE.md` (global) or a project `CLAUDE.md`, replacing `/path/to/akm`.
(If you run Claude Code *inside* the cloned repo, the root `CLAUDE.md` already covers this — no installation needed.)

```markdown
## AKM Knowledge System

Knowledge system root: `/path/to/akm` (AKM)

- When you need knowledge, context, or procedures, first read AKM `99-system/INDEX.md` and all files in `40-memory/` (both are short)
- Lookup: INDEX → layer folder (`20-knowledge` knowledge, `30-context` context, `50-procedures` procedures)
- Before saving any knowledge, experience, or procedure, follow the classification tree in `99-system/ROUTER.md`. Never save to arbitrary locations
- Before marking durable, public, or high-stakes work complete, select and apply the Tier 0–3 checks in `99-system/VERIFICATION.md`
- On task failure or repeated mistakes, follow the Learn Back mapping table in `99-system/LOOP.md`: record under `70-evaluation/` and fix the designated layer
- Never modify originals in `10-sources/`. Update `99-system/INDEX.md` when adding or removing notes, and append one line to `99-system/LOG.md` for meaningful changes
```

## Division of labor with Claude Code native features

| Claude Code feature | Division |
|---|---|
| auto-memory (`~/.claude/projects/*/memory/`) | Session/project-scoped volatile pointers only. Knowledge or rules that other tools should share go to AKM; leave a one-line pointer to the AKM path in memory |
| `.claude/skills/` | The reusable AKM suite is installed here as links to its package. User-specific procedure bodies belong in the knowledge workspace’s selected procedure layer; use pointers for those rather than copying domain data into the package |
| `CLAUDE.md` | The snippet above + Claude-Code-specific tool settings only. No domain knowledge |
