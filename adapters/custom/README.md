# Custom Adapter — any agent

Any agent that can read files can use AKM. Write your adapter in four steps.

## 1. Answer the four questions

Copy this table into your adapter and fill it in:

| # | Item | Value |
|---|---|---|
| ① | AKM root | (absolute path to your clone) |
| ② | Session start | All of `40-memory/` + `00-system/INDEX.md` |
| ③ | Routing | `00-system/ROUTER.md` classification tree before every save |
| ④ | Learn Back | `00-system/LOOP.md` mapping table on failures |

## 2. Put the snippet where your agent reads instructions

System prompt, instruction file, bootstrap note — wherever your agent loads its standing rules:

```markdown
## AKM Knowledge System

Knowledge system root: `/path/to/akm` (AKM)

- When you need knowledge, context, or procedures, first read AKM `00-system/INDEX.md` and all files in `40-memory/` (both are short)
- Lookup: INDEX → layer folder (`20-knowledge` knowledge, `30-context` context, `50-procedures` procedures)
- Before saving any knowledge, experience, or procedure, follow the classification tree in `00-system/ROUTER.md`. Never save to arbitrary locations
- On task failure or repeated mistakes, follow the Learn Back mapping table in `00-system/LOOP.md`: record under `70-evaluation/` and fix the designated layer
- Never modify originals in `10-sources/`. Update `00-system/INDEX.md` when adding or removing notes, and append one line to `00-system/LOG.md` for meaningful changes
```

## 3. If your agent has its own memory or brain

Divide, don't duplicate:

- **Agent's native memory**: pointers needed only by this agent + one pointer to the AKM root
- **AKM `40-memory/`**: rules every harness shares
- One body, everywhere else pointers. The dividing question: *"Would another harness need this?"* YES → AKM. NO → native memory
- If the native store has its own taxonomy (tiers, types), keep it — do not translate it into AKM's `trustLevel`. They are different axes (loading priority vs trust)

## 4. Don't bulk-migrate

If your agent already has a working memory system, leave it alone. Route **new** knowledge by the division rule above, and move old notes individually only when another harness actually needs them.

## Verify your adapter

Run a fresh session where the agent knows nothing except the snippet, then check:

1. Ask *"where do recurring mistakes get recorded?"* → it should answer `70-evaluation/failure-patterns/` (+ `40-memory/` pointer), citing LOOP/ROUTER
2. Tell it a user preference → it should store the body in `30-context/users/` and a one-line pointer in `40-memory/`
3. Tell it a repeatable procedure with failure points and a verification step → it should create a skill in `50-procedures/skills/` using the template
4. It should update `INDEX.md` and append to `LOG.md` without being asked
