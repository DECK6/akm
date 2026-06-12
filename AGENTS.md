# AKM — Agent Operating Instructions

This repository is an AKM (Agent Knowledge Management) instance, and you are at its root. All paths below are relative to this directory.

- When you need knowledge, context, or procedures, first read `00-system/INDEX.md` and all files in `40-memory/` (both are short)
- Lookup: INDEX → layer folder (`20-knowledge/` knowledge, `30-context/` context, `50-procedures/` procedures)
- Before saving any knowledge, experience, or procedure, follow the classification tree in `00-system/ROUTER.md`. Never save to arbitrary locations
- On task failure or repeated mistakes, follow the Learn Back mapping table in `00-system/LOOP.md`: record under `70-evaluation/` and fix the designated layer
- Never modify originals in `10-sources/`. Update `00-system/INDEX.md` when adding or removing notes, and append one line to `00-system/LOG.md` for meaningful changes
- New notes follow the frontmatter standard in `00-system/SCHEMA.md`; use the templates in `00-system/templates/`

To use AKM from outside this directory, install an adapter snippet: see `adapters/README.md`.
