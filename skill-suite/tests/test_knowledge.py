"""Behavioral checks for the linked knowledge audit, using actual local files."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from test_tools import PACKAGE, scratch


def fixture():
    root = scratch()
    files = {'model.md': '# Model\nC1 is a Tool; C2 is Training. R1 means requires.\n',
             'raw.md': '# Workshop rule\nUsing the cutter requires induction.\n',
             'wiki/a.md': '# Cutter\nThe cutter requires induction. [Training](b.md).\n',
             'wiki/b.md': '# Induction\nInduction is required for the cutter. [Cutter](a.md).\n',
             'checks.md': '# Checks\nNormal: trained user may use it. Counterexample: untrained user may not. Unknown: another tool is not covered.\n'}
    for path, content in files.items():
        target = root/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    data = {
        'version': 1, 'domain_id': 'workshop', 'revision': 1, 'model_path': 'model.md',
        'artifacts': {path: hashlib.sha256((root/path).read_bytes()).hexdigest() for path in files},
        'types': [{'id': 'T1'}, {'id': 'T2'}],
        'concepts': [{'id': 'C1', 'definition': 'Cutter', 'type_ids': ['T1']},
                     {'id': 'C2', 'definition': 'Induction', 'type_ids': ['T2']}],
        'relations': [{'id': 'R1', 'definition': 'requires prior completion', 'domain_types': ['T1'], 'range_types': ['T2']}],
        'sources': [{'id': 'S1', 'path': 'raw.md', 'read': True}],
        'claims': [{'id': 'A1', 'subject': 'C1', 'predicate': 'R1', 'object': 'C2',
                    'conditions': 'Workshop cutter use', 'status': 'current', 'basis': 'source-supported',
                    'evidence': [{'source_id': 'S1', 'locator': 'Workshop rule, sentence 1'}]}],
        'notes': [{'id': 'N1', 'path': 'wiki/a.md', 'status': 'current', 'question_ids': ['Q1'],
                   'concept_ids': ['C1'], 'claim_ids': ['A1'], 'source_ids': ['S1'], 'links': ['N2']},
                  {'id': 'N2', 'path': 'wiki/b.md', 'status': 'current', 'question_ids': ['Q1'],
                   'concept_ids': ['C2'], 'claim_ids': ['A1'], 'source_ids': ['S1'], 'links': ['N1']}],
        'questions': [{'id': 'Q1', 'text': 'When may someone use the cutter?', 'status': 'answered'}],
        'checks': [{'question_id': 'Q1', 'case': case, 'result': 'pass', 'revision': 1, 'path': 'checks.md'}
                   for case in ['normal', 'counterexample', 'unknown']]}
    return root, data


class KnowledgeTests(unittest.TestCase):
    def run_tool(self, root, data, command='lint', extra=()):
        path = root/'map.json'
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        return subprocess.run([sys.executable, str(PACKAGE/'scripts/knowledge.py'), command,
                               '--root', str(root), '--map', str(path), *extra],
                              capture_output=True, text=True)

    def report(self, root, data, command='lint', extra=()):
        result = self.run_tool(root, data, command, extra)
        self.assertIn(result.returncode, [0, 1], result.stderr)
        return json.loads(result.stdout)

    def test_valid_linked_scope_and_read_only(self):
        root, data = fixture()
        before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
        result = self.report(root, data, 'coverage')
        self.assertTrue(result['coverage']['complete_for_declared_scope'])
        self.assertEqual(result['coverage']['verified_question_ids'], ['Q1'])
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)

    def test_empty_system_is_not_complete(self):
        root, data = fixture()
        for table in ['questions', 'notes', 'claims', 'concepts', 'relations', 'types', 'sources', 'checks']:
            data[table] = []
        report = self.report(root, data, 'coverage')
        self.assertFalse(report['coverage']['complete_for_declared_scope'])

    def test_boolean_version_is_not_schema_version_one(self):
        for version in [True, 1.0]:
            root, data = fixture()
            data['version'] = version
            result = self.run_tool(root, data)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Invalid input:', result.stderr)

    def test_example_link_syntax_inside_code_is_not_a_broken_link(self):
        root, data = fixture()
        note = root/'wiki/a.md'
        note.write_text(note.read_text()+'\nLiteral: `[example](missing-inline.md)`\n\n~~~md\n[example](missing-fenced.md)\n~~~\n', encoding='utf-8')
        data['artifacts']['wiki/a.md'] = hashlib.sha256(note.read_bytes()).hexdigest()
        report = self.report(root, data)
        self.assertEqual(report['findings'], [])

    def test_unmapped_answer_claims_are_a_review_gap(self):
        root, data = fixture()
        data['notes'][0]['claim_ids'] = []
        report = self.report(root, data)
        self.assertFalse(report['coverage']['complete_for_declared_scope'])
        self.assertIn('missing-claim-mapping', {x['code'] for x in report['findings']})

    def test_empty_registered_files_cannot_satisfy_coverage(self):
        for path in ['wiki/a.md', 'model.md', 'checks.md', 'raw.md']:
            with self.subTest(path=path):
                root, data = fixture()
                (root/path).write_text('  \n', encoding='utf-8')
                data['artifacts'][path] = hashlib.sha256((root/path).read_bytes()).hexdigest()
                report = self.report(root, data, 'coverage')
                self.assertFalse(report['coverage']['complete_for_declared_scope'])
                self.assertIn('empty-artifact', {x['code'] for x in report['findings']})

    def test_invalid_references_types_and_duplicate_ids_fail_lint(self):
        root, data = fixture()
        data['concepts'].append(copy.deepcopy(data['concepts'][0]))
        data['claims'][0]['object'] = 'C1'
        data['notes'][0]['source_ids'] = ['S-missing']
        result = self.run_tool(root, data)
        self.assertEqual(result.returncode, 1)
        codes = {x['code'] for x in json.loads(result.stdout)['findings']}
        self.assertTrue({'duplicate-id', 'relation-range', 'missing-reference'} <= codes)

    def test_unread_or_unlocated_evidence_cannot_pass(self):
        root, data = fixture()
        data['sources'][0]['read'] = False
        data['claims'][0]['evidence'][0]['locator'] = ''
        report = self.report(root, data)
        self.assertFalse(report['coverage']['complete_for_declared_scope'])
        self.assertTrue({'unread-evidence', 'unlocated-evidence'} <= {x['code'] for x in report['findings']})

    def test_stale_content_and_old_checks_block_completeness(self):
        root, data = fixture()
        (root/'raw.md').write_text('Rule changed', encoding='utf-8')
        data['revision'] = 2
        report = self.report(root, data, 'coverage')
        codes = {x['code'] for x in report['findings']}
        self.assertIn('stale-projection', codes)
        self.assertFalse(report['coverage']['complete_for_declared_scope'])
        self.assertEqual(report['coverage']['verified_question_ids'], [])

    def test_gap_frontier_separates_connection_and_exploration(self):
        root, data = fixture()
        data['notes'][0]['links'] = []
        data['notes'][1]['links'] = []
        data['questions'].append({'id': 'Q2', 'text': 'What about the lathe?', 'status': 'open'})
        report = self.report(root, data, 'frontier')
        roles = {x['role'] for x in report['tasks']}
        self.assertTrue({'akm-connect', 'akm-explore'} <= roles)
        self.assertEqual(len({x['id'] for x in report['tasks']}), len(report['tasks']))

    def test_source_impact_reaches_claim_notes_and_question(self):
        root, data = fixture()
        report = self.report(root, data, 'impact', ['--id', 'S1'])
        self.assertTrue({'S1', 'A1', 'N1', 'N2', 'Q1'} <= set(report['affected_ids']))

    def test_external_and_symlink_paths_are_rejected_without_read(self):
        for symbolic in [False, True]:
            root, data = fixture()
            outside = scratch()/'private.md'
            outside.write_text('DO_NOT_READ_ME', encoding='utf-8')
            if symbolic:
                (root/'escape.md').symlink_to(outside)
                path = 'escape.md'
            else:
                path = str(outside)
            data['notes'][0]['path'] = path
            report = self.report(root, data)
            self.assertIn('unsafe-path', {x['code'] for x in report['findings']})
            self.assertNotIn('DO_NOT_READ_ME', json.dumps(report))

    def test_malformed_table_returns_clean_input_error(self):
        root, data = fixture()
        data['notes'] = ['bad']
        result = self.run_tool(root, data)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Invalid input:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_broken_real_link_and_quarantined_claim_are_visible(self):
        root, data = fixture()
        (root/'wiki/a.md').write_text('# Text\n[Missing](absent.md)', encoding='utf-8')
        data['claims'][0]['status'] = 'disputed'
        report = self.report(root, data)
        codes = {x['code'] for x in report['findings']}
        self.assertTrue({'broken-link', 'unresolved-claim'} <= codes)
        self.assertFalse(report['coverage']['complete_for_declared_scope'])


if __name__ == '__main__':
    unittest.main()
