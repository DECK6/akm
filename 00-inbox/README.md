# 00-inbox — Intake staging

AKM is ROUTER-first, but to prevent material from scattering across layers before it is classified, **every new intake lands here first**. An item may stay in the inbox **up to 7 days**, then it must be classified into its final layer via the decision tree in `99-system/ROUTER.md`.

## The 7-day rule

- **First landing**: new material, job outputs, and collected items go to `00-inbox/` first (use a topic subfolder `00-inbox/<topic>/` when it helps).
- **Stay limit**: at most **7 days**, counted from the file's `date created` frontmatter (fall back to mtime).
- **Classification**: apply the `99-system/ROUTER.md` tree from the top; the first match is the destination layer (`10-sources/`, `20-knowledge/`, `30-context/`, `50-procedures/`, `60-actions/`, `70-evaluation/`, `80-outputs/`, …).
- **Who moves it**: a weekly triage job (or you, at any time) sweeps items past 7 days through the ROUTER. Emptying the inbox early is always fine — 7 days is a ceiling, not a target.
- **Never a store**: the inbox is a landing zone. Nothing lives here permanently.
- **Record moves**: append one line to `99-system/LOG.md` for meaningful moves, and update the INDEX when notes are added or relocated.

## Exceptions (may skip the inbox)

- Explicitly archival originals written straight to `10-sources/`.
- Execution logs written straight to `60-actions/runs/`.

Everything in this folder except this README is gitignored — inbox contents are instance data and never leave the machine.
