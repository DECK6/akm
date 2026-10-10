#!/usr/bin/env python3
"""Link all AKM skills into Codex or Claude Code without replacing existing entries."""
import argparse
import json
import os
from pathlib import Path
import sys


def install(destination):
    source = Path(__file__).resolve().parents[1] / 'skills'
    skills = sorted(p for p in source.iterdir() if (p/'SKILL.md').is_file())
    pending, present, conflicts = [], [], []
    for skill in skills:
        target = destination / skill.name
        if target.is_symlink() and target.resolve() == skill.resolve():
            present.append(skill.name)
        elif target.exists() or target.is_symlink():
            conflicts.append(str(target))
        else:
            pending.append((skill, target))
    if conflicts:
        raise ValueError('Installation conflict; existing entries preserved: ' + ', '.join(conflicts))
    destination.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for skill, target in pending:
            target.symlink_to(skill.resolve(), target_is_directory=True)
            created.append(skill.name)
    except OSError as error:
        raise OSError(f'Installation stopped; created links retained: {created}; {error}') from error
    return {'destination': str(destination), 'created': created, 'already_present': present}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('codex', 'claude'), default='codex',
                        help='target host (default: codex); claude uses CLAUDE_CONFIG_DIR or ~/.claude')
    parser.add_argument('--dest', type=Path,
                        help='explicit skills directory; overrides the selected host default')
    args = parser.parse_args()
    variable, fallback = ('CLAUDE_CONFIG_DIR', '.claude') if args.host == 'claude' else ('CODEX_HOME', '.codex')
    destination = args.dest if args.dest is not None else Path(os.environ.get(variable) or Path.home()/fallback)/'skills'
    try:
        result = install(destination.expanduser().absolute())
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    result['host'] = args.host
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
