# AKM External Assets

AKM is a text-first vault. Large binary originals and deliverables should live outside the AKM root so Git, sync tools, search indexes, and agents do not repeatedly process files they cannot use as Markdown.

## Storage convention

Choose an external asset root outside the vault, for example:

```text
<akm-root>-external-assets/
```

Mirror the AKM-relative path under that root:

```text
AKM note:       <akm-root>/80-outputs/project/final-delivery.md
External asset: <akm-root>-external-assets/80-outputs/project/final-delivery.mp4
```

This keeps the relationship obvious without storing the binary in the knowledge vault. Record the external path, provenance, checksum when useful, and verification status in the companion AKM note.

## Operating rules

- Keep Markdown, transcripts, manifests, checksums, and compact metadata in AKM.
- Put large audio, video, PDF, slide, and other binary files in the external asset root.
- Preserve the AKM-relative directory structure when externalizing a file.
- Verify the external copy before moving the in-vault copy to Trash; never destroy the only copy.
- Do not use `git add -f` to bypass the binary safety patterns in `.gitignore`.
- Treat external assets as instance data: back them up separately and do not assume Git protects them.

The default `.gitignore` blocks common large binary extensions and local generated state. Extend it for additional binary formats used by your instance.
