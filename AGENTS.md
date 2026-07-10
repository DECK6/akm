# AKM — Agent Operating Instructions

This repository is an AKM (Agent Knowledge Management) instance, and you are at its root. All paths below are relative to this directory.

- When you need knowledge, context, or procedures, first read `99-system/INDEX.md` and all files in `40-memory/` (both are short)
- Lookup: INDEX → layer folder (`20-knowledge/` knowledge, `30-context/` context, `50-procedures/` procedures)
- Before saving any knowledge, experience, or procedure, follow the classification tree in `99-system/ROUTER.md`. Never save to arbitrary locations
- **Inbox-first**: every new note/intake (notes, cron outputs, collected material) lands in `00-inbox/` first and stays up to 7 days. Do NOT write straight into a final layer. A weekly inbox triage job sweeps items past 7 days into the correct layer via `99-system/ROUTER.md`. Exception: `10-sources/` originals that are explicitly archival, and `60-actions/runs/` execution logs, may be written directly.
- Before marking durable, public, or high-stakes work complete, select and apply the Tier 0–3 checks in `99-system/VERIFICATION.md`
- On task failure or repeated mistakes, follow the Learn Back mapping table in `99-system/LOOP.md`: record under `70-evaluation/` and fix the designated layer
- Never modify originals in `10-sources/`. Update `99-system/INDEX.md` when adding or removing notes, and append one line to `99-system/LOG.md` for meaningful changes
- New notes follow the frontmatter standard in `99-system/SCHEMA.md`; use the templates in `99-system/templates/`

To use AKM from outside this directory, install an adapter snippet: see `adapters/README.md`.
