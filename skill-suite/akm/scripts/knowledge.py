#!/usr/bin/env python3
"""Read-only integrity, coverage, frontier and change-impact reports for AKM.

Consumes a hashed projection of an existing ontology/wiki. It neither infers
facts nor edits knowledge. See skills/akm/references/audit-map.md.
"""
import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

TABLES = ('types', 'concepts', 'relations', 'claims', 'notes', 'sources', 'questions')
LISTS = {'concepts': ('type_ids',), 'relations': ('domain_types', 'range_types'),
         'notes': ('question_ids', 'concept_ids', 'claim_ids', 'source_ids', 'links')}
TEXT = {'concepts': ('definition',), 'relations': ('definition',),
        'claims': ('subject', 'predicate', 'object', 'conditions', 'basis', 'status'),
        'notes': ('path', 'status'), 'questions': ('text', 'status')}
CASES = {'normal', 'counterexample', 'unknown'}


def validate(data):
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('Invalid map: version must be 1')
    if not isinstance(data.get('domain_id'), str) or not data['domain_id'].strip():
        raise ValueError('Invalid map: domain_id is required')
    if type(data.get('revision')) is not int or data['revision'] < 1:
        raise ValueError('Invalid map: revision must be a positive integer')
    if not isinstance(data.get('model_path'), str) or not data['model_path']:
        raise ValueError('Invalid map: model_path is required')
    artifacts = data.get('artifacts')
    if not isinstance(artifacts, dict) or any(not isinstance(p, str) or not isinstance(h, str)
            or not re.fullmatch('[0-9a-f]{64}', h) for p, h in artifacts.items()):
        raise ValueError('Invalid map: artifacts must map relative paths to SHA-256 values')
    for table in TABLES:
        rows = data.get(table)
        if not isinstance(rows, list):
            raise ValueError(f'Invalid map: {table} must be an array')
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
                raise ValueError(f'Invalid map: {table} entries need a string id')
            for field in TEXT.get(table, ()):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    raise ValueError(f'Invalid map: {row["id"]}.{field} must be nonempty text')
            for field in LISTS.get(table, ()):
                if not isinstance(row.get(field), list) or any(not isinstance(x, str) or not x for x in row[field]):
                    raise ValueError(f'Invalid map: {row["id"]}.{field} must be a string array')
            if table == 'claims':
                if row['status'] not in {'current', 'proposed', 'disputed', 'deprecated', 'needs-review'}:
                    raise ValueError('Invalid map: unsupported claim status')
                if row['basis'] not in {'source-supported', 'user-stated', 'llm-proposed'}:
                    raise ValueError('Invalid map: unsupported claim basis')
                if not isinstance(row.get('evidence'), list) or any(not isinstance(e, dict)
                        or not isinstance(e.get('source_id'), str) or not isinstance(e.get('locator'), str)
                        for e in row['evidence']):
                    raise ValueError(f'Invalid map: {row["id"]}.evidence needs source_id and locator')
            if table == 'sources':
                if type(row.get('read')) is not bool or not any(isinstance(row.get(k), str) and row[k] for k in ('path', 'url')):
                    raise ValueError('Invalid map: source needs read boolean and path or url')
            if table == 'questions' and row['status'] not in {'open', 'answered', 'deferred'}:
                raise ValueError('Invalid map: unsupported question status')
            if table == 'notes' and row['status'] not in {'current', 'draft', 'needs-review', 'deprecated'}:
                raise ValueError('Invalid map: unsupported note status')
    if not isinstance(data.get('checks'), list):
        raise ValueError('Invalid map: checks must be an array')
    for row in data['checks']:
        if not isinstance(row, dict) or not isinstance(row.get('question_id'), str) or row.get('case') not in CASES or row.get('result') not in {'pass', 'fail', 'unknown'} or type(row.get('revision')) is not int or not isinstance(row.get('path'), str):
            raise ValueError('Invalid map: check needs question_id, case, result, revision and path')


def contained(root, value):
    path = Path(value)
    if path.is_absolute() or not value or '\\' in value:
        raise ValueError('Expected root-relative path')
    resolved = (root/path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError('Path escapes knowledge root')
    return resolved


def prose_only(content):
    """Exclude fenced and inline code before inspecting ordinary Markdown links."""
    lines, fence = [], None
    for line in content.splitlines(keepends=True):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
        else:
            lines.append(line)
    return re.sub(r'(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)', '', ''.join(lines), flags=re.S)


def audit(root, data):
    validate(data)
    findings, ids, by = [], {}, {}
    dependencies = defaultdict(set)

    def add(code, target, message, severity='error', role='akm-lint'):
        item = {'code': code, 'target': target, 'message': message, 'severity': severity, 'role': role}
        if item not in findings:
            findings.append(item)

    for table in TABLES:
        by[table] = {}
        for row in data[table]:
            key = row['id']
            if key in ids:
                add('duplicate-id', key, 'ID occurs more than once')
            ids[key] = table
            by[table][key] = row

    def ref(value, table, owner):
        if value not in by[table]:
            add('missing-reference', owner, f'{value} is not in {table}')
            return None
        dependencies[value].add(owner)
        return by[table][value]

    inspected = {}

    def file(value, owner, hashed=True):
        try:
            path = contained(root, value)
        except (ValueError, OSError, RuntimeError):
            add('unsafe-path', owner, f'Unsafe path: {value}')
            return None
        if not path.is_file():
            add('missing-file', owner, f'Missing file: {value}')
            return None
        if hashed:
            expected = data['artifacts'].get(value)
            content = path.read_bytes()
            actual = hashlib.sha256(content).hexdigest()
            inspected[value] = actual
            if not content.strip():
                add('empty-artifact', owner, f'Registered knowledge/evidence file is empty: {value}', role='akm-review')
            if expected is None:
                add('unhashed-artifact', owner, f'Projection has no fingerprint: {value}')
            elif expected != actual:
                add('stale-projection', owner, f'Read and refresh projection after change: {value}', role='akm-review')
        return path

    file(data['model_path'], data['domain_id'])
    for value in data['artifacts']:
        file(value, value)
    for concept in data['concepts']:
        for type_id in concept['type_ids']:
            ref(type_id, 'types', concept['id'])
        if not concept['type_ids']:
            add('untyped-concept', concept['id'], 'No type assigned', 'warning', 'akm-ontology')
    for relation in data['relations']:
        for type_id in relation['domain_types'] + relation['range_types']:
            ref(type_id, 'types', relation['id'])
    for source in data['sources']:
        if source.get('path'):
            file(source['path'], source['id'])
        elif not source.get('url', '').startswith(('https://', 'http://')):
            add('invalid-source-url', source['id'], 'Source URL must be HTTP(S)')
    for claim in data['claims']:
        cid = claim['id']
        subject = ref(claim['subject'], 'concepts', cid)
        predicate = ref(claim['predicate'], 'relations', cid)
        obj = ref(claim['object'], 'concepts', cid)
        if predicate:
            for end, value, field in [('domain', subject, 'domain_types'), ('range', obj, 'range_types')]:
                if value and predicate[field] and not set(value['type_ids']).intersection(predicate[field]):
                    add('relation-' + end, cid, f'{value["id"]} violates {predicate["id"]} {end} types', role='akm-ontology')
        if claim['status'] != 'deprecated':
            if claim['status'] != 'current' or claim['basis'] == 'llm-proposed':
                add('unresolved-claim', cid, 'Claim is not currently evidence-supported', 'warning', 'akm-review')
            if not claim['evidence'] and claim['basis'] != 'llm-proposed':
                add('missing-evidence', cid, 'Supported claim has no evidence', role='akm-explore')
        for evidence in claim['evidence']:
            source = ref(evidence['source_id'], 'sources', cid)
            if not evidence['locator'].strip():
                add('unlocated-evidence', cid, 'Claim needs a source passage locator', role='akm-ingest')
            if source and not source['read']:
                add('unread-evidence', cid, f'{source["id"]} has not been read', role='akm-explore')

    active_notes = [n for n in data['notes'] if n['status'] != 'deprecated']
    for note in data['notes']:
        nid = note['id']
        path = file(note['path'], nid)
        for field, table in [('question_ids', 'questions'), ('concept_ids', 'concepts'), ('claim_ids', 'claims'), ('source_ids', 'sources'), ('links', 'notes')]:
            for value in note[field]:
                row = ref(value, table, nid)
                if row and row.get('status') == 'deprecated' and note['status'] != 'deprecated':
                    add('deprecated-reference', nid, f'Active note uses retired {value}', role='akm-review')
        for qid in note['question_ids']:
            dependencies[nid].add(qid)
        for claim_id in note['claim_ids']:
            claim = by['claims'].get(claim_id)
            if claim:
                missing = {e['source_id'] for e in claim['evidence']} - set(note['source_ids'])
                if missing:
                    add('note-evidence-gap', nid, f'Claim sources missing from note: {sorted(missing)}', role='akm-wiki')
        if note['status'] != 'deprecated':
            if note['status'] != 'current':
                add('note-needs-review', nid, 'Note is not current', 'warning', 'akm-review')
            if not note['concept_ids']:
                add('missing-model-connection', nid, 'Note has no concept mapping', 'warning', 'akm-connect')
            if not note['claim_ids']:
                add('missing-claim-mapping', nid, 'Read the explanation and map its claims before declaring completeness', 'warning', 'akm-review')
            if len(active_notes) > 1 and not any(nid in n['links'] for n in active_notes if n['id'] != nid):
                add('orphan-note', nid, 'No incoming note link; inspect whether one is useful', 'info', 'akm-connect')
        if path:
            content = path.read_text(encoding='utf-8')
            # Common inline Markdown links only; complex syntax/anchors need host lint.
            content = prose_only(content)
            for raw in re.findall(r'\]\(([^\s)]+)\)', content):
                link = urlsplit(raw)
                if link.scheme or link.netloc or not link.path:
                    continue
                target = unquote(link.path).strip('<>')
                if target.startswith('/'):
                    add('unsafe-path', nid, f'Absolute local link: {target}')
                    continue
                relative = str(Path(note['path']).parent/target)
                file(relative, nid, hashed=False) if (root/relative).exists() else add('broken-link', nid, f'Unresolved inline link: {raw}', role='akm-connect')

    for check in data['checks']:
        ref(check['question_id'], 'questions', check['question_id'])
        file(check['path'], check['question_id'])
    verified, open_ids = [], []
    for question in data['questions']:
        qid = question['id']
        if question['status'] == 'deferred':
            continue
        answers = [n for n in active_notes if qid in n['question_ids'] and n['status'] == 'current']
        if question['status'] != 'answered' or not answers:
            open_ids.append(qid)
            add('question-gap', qid, question['text'], 'warning', 'akm-explore')
        checks = [c for c in data['checks'] if c['question_id'] == qid and c['revision'] == data['revision']]
        passed = {c['case'] for c in checks if c['result'] == 'pass'}
        if passed != CASES or any(c['result'] != 'pass' for c in checks):
            add('question-unverified', qid, 'Needs current normal/counterexample/unknown checks', 'warning', 'akm-review')
        elif question['status'] == 'answered' and answers:
            verified.append(qid)
    required = [q for q in data['questions'] if q['status'] != 'deferred']
    blockers = [f for f in findings if f['severity'] in {'error', 'warning'}]
    coverage = {'declared_questions': len(data['questions']), 'required_questions': len(required),
                'open_question_ids': open_ids, 'verified_question_ids': sorted(verified),
                'complete_for_declared_scope': bool(required) and len(verified) == len(required) and not blockers,
                'meaning': 'Recorded checks for this declared scope and revision; not proof of factual truth or field-wide completeness.'}
    return {'domain_id': data['domain_id'], 'revision': data['revision'], 'findings': findings,
            'coverage': coverage, 'inspected_sha256': inspected}, dependencies, ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['lint', 'coverage', 'frontier', 'impact'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--map', type=Path, required=True)
    parser.add_argument('--id', action='append', default=[])
    args = parser.parse_args()
    try:
        root = args.root.expanduser().resolve(strict=True)
        path = args.map.expanduser().resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError('Projection must be inside the selected knowledge root')
        data = json.loads(path.read_text(encoding='utf-8'))
        report, dependencies, ids = audit(root, data)
        if args.command == 'frontier':
            report['tasks'] = [{'id': 'task-' + hashlib.sha256((f['code'] + ':' + f['target']).encode()).hexdigest()[:12],
                               'role': f['role'], 'target': f['target'], 'reason': f['message'], 'status': 'pending',
                               'priority': {'error': 0, 'warning': 1, 'info': 2}[f['severity']]}
                              for f in report['findings']]
            # One task can cover several findings of the same kind on one target.
            report['tasks'] = list({t['id']: t for t in report['tasks']}.values())
            report['tasks'].sort(key=lambda t: (t['priority'], t['id']))
        if args.command == 'impact':
            if not args.id or any(key not in ids for key in args.id):
                raise ValueError('Impact requires existing --id values')
            queue, seen = deque(args.id), set(args.id)
            while queue:
                for child in dependencies[queue.popleft()] - seen:
                    seen.add(child)
                    queue.append(child)
            report['affected_ids'] = sorted(seen)
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 1 if any(f['severity'] == 'error' for f in report['findings']) else 0
    except (ValueError, OSError, TypeError, KeyError, RuntimeError) as error:
        parser.exit(2, 'Invalid input: ' + str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
