#!/usr/bin/env python3
"""Add the complete sibling skill set without replacing existing entries."""
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
    default = Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex'))) / 'skills'
    parser.add_argument('--dest', type=Path, default=default)
    args = parser.parse_args()
    try:
        result = install(args.dest.expanduser().absolute())
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
