# AKM-SECURITY

Security and privacy rules for every AKM instance. These apply **before** ROUTER classification — an input that violates them is not stored, regardless of which layer it would belong to.

## 1. Never store secret values

API keys, tokens, passwords, OAuth refresh tokens, cookies, private keys, payment data — never, in any layer.
Store **secret names and locations** instead:

- Bad: `OPENAI_API_KEY=sk-abc123...`
- Good: `OpenAI key lives in ~/.zshrc as OPENAI_API_KEY`

`scripts/lint.mjs` scans for common secret patterns (W3), but the scan is a backstop, not permission to be careless.

## 2. Personal data in sources

Before ingesting material containing personal data (names, contacts, conversations, third-party content):

- Ingest only if the work actually needs it; prefer storing a `sourcePath` reference over copying content
- Third-party private conversations and unpublished work: reference, don't snapshot
- If ingested, it stays in the gitignored layers — see rule 3

## 3. The layers never leave the machine

Everything under `10-sources/` … `90-archive/` is your private instance, protected by `.gitignore`.

- **Never `git add -f`** (force-add) a layer file. If a file genuinely belongs in the public system, move it into `00-system/` or `adapters/` deliberately and review it first
- Before any commit: `git diff --cached --name-only` and confirm only system files are staged
- `sourcePath` values may reveal your private directory structure — fine locally, one more reason instance notes are never committed

## 4. Outputs are the leak surface

`80-outputs/` content is *meant* to leave the machine. Before sharing any output externally:

- Re-read it for secrets, personal data, private paths, internal project names
- Check what its wikilinks and quoted material expose
- When an agent produces an output for publication, this review is part of Verify (step 6), not optional polish

## 5. Agents follow these rules too

Adapter snippets point agents at ROUTER for storage; ROUTER's pre-check points here. An agent that is asked to store a secret should refuse and store the secret's *location* instead — that is correct AKM behavior, not disobedience.
