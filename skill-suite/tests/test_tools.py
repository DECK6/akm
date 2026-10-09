import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'akm'
ARTIFACTS = ROOT / '.test-artifacts'
ARTIFACTS.mkdir(exist_ok=True)


def scratch():
    # Keep fixtures recoverable; no permanent deletion during the test run.
    return Path(tempfile.mkdtemp(prefix='case-', dir=ARTIFACTS))


class InstallationTests(unittest.TestCase):
    def command(self, dest, env=None):
        return subprocess.run([sys.executable, str(PACKAGE/'scripts/install.py'),
                               '--dest', str(dest)], capture_output=True, text=True, env=env)

    def test_unicode_destination_under_ascii_locale(self):
        dest = scratch()/'설치'
        env = dict(os.environ, LC_ALL='C', PYTHONUTF8='0', PYTHONCOERCECLOCALE='0')
        result = self.command(dest, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(os.fsencode(json.loads(result.stdout)['destination']), os.fsencode(str(dest)))
        self.assertTrue((dest/'akm/SKILL.md').is_file())

    def test_complete_install_and_idempotent_rerun(self):
        dest = scratch()/'skills'
        first = self.command(dest)
        self.assertEqual(first.returncode, 0, first.stderr)
        expected = sorted(p.name for p in (PACKAGE/'skills').iterdir() if (p/'SKILL.md').is_file())
        self.assertGreaterEqual(len(expected), 11)
        self.assertEqual(sorted(p.name for p in dest.iterdir()), expected)
        for name in expected:
            self.assertEqual((dest/name).resolve(), (PACKAGE/'skills'/name).resolve())
        self.assertEqual(self.command(dest).returncode, 0)

    def test_collision_preserves_existing_and_does_not_partially_install(self):
        dest = scratch()/'skills'
        occupied = dest/'akm-wiki'
        occupied.mkdir(parents=True)
        (occupied/'user-note.txt').write_text('user-owned')
        result = self.command(dest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Installation conflict', result.stderr)
        self.assertEqual((occupied/'user-note.txt').read_text(), 'user-owned')
        self.assertEqual([p.name for p in dest.iterdir()], ['akm-wiki'])

    def test_dangling_symlink_is_not_overwritten(self):
        dest = scratch()/'skills'
        dest.mkdir()
        (dest/'akm').symlink_to(dest/'missing')
        result = self.command(dest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Installation conflict', result.stderr)
        self.assertTrue((dest/'akm').is_symlink())
        self.assertEqual(len(list(dest.iterdir())), 1)


class WorkspaceTests(unittest.TestCase):
    def run_profile(self, profile, root, mode='init', env=None):
        config = scratch()/'profile.json'
        config.write_text(json.dumps(profile, ensure_ascii=False))
        return subprocess.run([sys.executable, str(PACKAGE/'scripts/workspace.py'), mode,
                               '--profile', str(config), '--root', str(root)],
                              capture_output=True, text=True, env=env)

    def test_utf8_profile_and_unicode_root_under_ascii_locale(self):
        root = scratch()/'지식공간'
        env = dict(os.environ, LC_ALL='C', PYTHONUTF8='0', PYTHONCOERCECLOCALE='0')
        plan = self.run_profile(self.profile(), root, mode='plan', env=env)
        self.assertEqual(plan.returncode, 0, plan.stderr)
        # ASCII filesystem locales may represent argv with surrogateescape.
        self.assertEqual(os.fsencode(json.loads(plan.stdout)['root']), os.fsencode(str(root)))
        self.assertFalse(root.exists())
        result = self.run_profile(self.profile(), root, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(os.fsencode(json.loads(result.stdout)['created']), os.fsencode(str(root)))
        saved = json.loads((root/'99-system/PROFILE.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['domain'], self.profile()['domain'])
        self.assertIn('맞춤 AKM', (root/'99-system/SCHEMA.md').read_text(encoding='utf-8'))

    def profile(self, **updates):
        result = {'version': 1, 'domain_id': 'literature', 'domain': '문학 비교',
                  'purpose': '작품의 장치를 비교한다', 'inbox': False,
                  'layers': ['knowledge'], 'knowledge_depth': 'linked',
                  'operating_depth': 'none',
                  'decisions': [{'component': 'inbox', 'choice': False,
                                 'reason': '읽고 바로 분류하는 개인 작업', 'basis': 'user-stated'}],
                  'pending_questions': []}
        result.update(updates)
        return result

    def test_knowledge_only_without_inbox_or_operating_folders(self):
        root = scratch()/'workspace'
        result = self.run_profile(self.profile(), root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(p.name for p in root.iterdir()), ['20-knowledge', '99-system'])
        profile = json.loads((root/'99-system/PROFILE.json').read_text())
        self.assertFalse(profile['inbox'])
        state = json.loads((root/'99-system/domains/literature/akm-state.json').read_text())
        self.assertEqual(state['initial_note_ids'], [])
        self.assertTrue((root/state['paths']['brief']).is_file())

    def test_operating_profile_with_inbox_uses_exact_selected_layers(self):
        root = scratch()/'workspace'
        profile = self.profile(inbox=True, layers=['sources','knowledge','context','procedures','evaluation'],
                               operating_depth='execute', knowledge_depth='synthesis')
        result = self.run_profile(profile, root)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = ['00-inbox','10-sources','20-knowledge','30-context','50-procedures','70-evaluation','99-system']
        self.assertEqual(sorted(p.name for p in root.iterdir()), expected)
        self.assertFalse((root/'40-memory').exists())

    def test_existing_workspace_is_not_overwritten(self):
        root = scratch()/'workspace'
        root.mkdir()
        (root/'user.md').write_text('keep')
        result = self.run_profile(self.profile(), root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Existing workspace preserved', result.stderr)
        self.assertEqual((root/'user.md').read_text(), 'keep')
        self.assertEqual(len(list(root.iterdir())), 1)

    def test_context_brief_meets_its_generated_schema(self):
        root = scratch()/'workspace'
        result = self.run_profile(self.profile(layers=['knowledge','context']), root)
        self.assertEqual(result.returncode, 0, result.stderr)
        brief = (root/'30-context/domains/literature/domain-brief.md').read_text()
        self.assertTrue(brief.startswith('---\n'), 'context brief must be a schema-valid note')
        header = brief.split('---', 2)[1]
        for key in ['description', 'akmLayer', 'akmType', 'trustLevel', 'date created', 'date modified']:
            self.assertRegex(header, rf'(?m)^{re.escape(key)}: .+')
        self.assertIn('akmLayer: context', header)
        self.assertIn('akmType: context', header)
        self.assertIn('trustLevel: draft', header)

    def test_invalid_path_id_and_unknown_layers_have_no_side_effects(self):
        for changes in [{'domain_id': '../../escape'}, {'layers': ['knowledge','unknown']},
                        {'inbox': 'false'}, {'knowledge_depth':'synthesis','layers':['actions']}]:
            with self.subTest(changes=changes):
                root = scratch()/'workspace'
                result = self.run_profile(self.profile(**changes), root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Invalid profile', result.stderr)
                self.assertFalse(root.exists())

    def test_plan_is_read_only_and_matches_created_folders(self):
        root = scratch()/'workspace'
        result = self.run_profile(self.profile(), root, 'plan')
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertFalse(root.exists())
        self.assertEqual(plan['folders'], ['20-knowledge','99-system'])


class PackageTests(unittest.TestCase):
    def test_public_core_snapshot_matches_pinned_hashes(self):
        assets=PACKAGE/'skills/akm-structure/assets'
        manifest=json.loads((assets/'upstream-manifest.json').read_text())
        self.assertEqual(manifest['repository'], 'https://github.com/DECK6/akm')
        self.assertRegex(manifest['commit'], r'^[a-f0-9]{40}$')
        self.assertTrue((assets/'upstream-akm/LICENSE').is_file())
        for row in manifest['files']:
            path=assets/'upstream-akm'/row['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['sha256'], row['path'])

    def test_skill_and_reference_links_resolve(self):
        broken=[]
        for path in (PACKAGE/'skills').rglob('*.md'):
            if 'assets' in path.parts:
                continue
            content=path.read_text()
            for target in re.findall(r'\]\(([^)]+)\)', content):
                if '://' in target or target.startswith('#'):
                    continue
                target=target.split('#')[0]
                if target and not (path.parent/target).exists():
                    broken.append(f'{path.relative_to(PACKAGE)} -> {target}')
        self.assertEqual(broken, [])

    def test_manifest_skill_directory_exists(self):
        manifest=json.loads((PACKAGE/'.codex-plugin/plugin.json').read_text())
        self.assertEqual(manifest['name'], PACKAGE.name)
        self.assertTrue((PACKAGE/manifest['skills']).is_dir())


if __name__ == '__main__':
    unittest.main()
