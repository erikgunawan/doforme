"""Exercise real Git staging, hooks and content-bound documentation checks."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import update_docs as DOCS
import install_doc_hooks as HOOKS


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'plugin'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        for directory in ('.claude-plugin', 'commands', 'docs', 'scripts', '.githooks'):
            (self.repo / directory).mkdir()
        (self.repo / '.claude-plugin/plugin.json').write_text(json.dumps({'name': 'doforme', 'version': '0.1.0'}))
        (self.repo / 'commands/analyze.md').write_text(
            '---\ndescription: Read-only analysis\nagent: doforme:investigator\nargument-hint: issue file\n---\n')
        for name in ('docs/INSTALLATION.md', 'docs/USAGE.md', 'CONTRIBUTING.md'):
            (self.repo / name).write_text('Synthetic guide\n')
        (self.repo / 'source.py').write_text('original\n')
        for name in ('update_docs.py', 'repo_policy.py', 'check_plugin.py', 'install_doc_hooks.py'):
            shutil.copy2(ROOT / 'scripts' / name, self.repo / 'scripts' / name)
        shutil.copy2(ROOT / '.githooks/pre-commit', self.repo / '.githooks/pre-commit')
        self.git('add', '.')
        self.git('commit', '-qm', 'synthetic baseline')
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, text=True)

    def sync(self, **kwargs):
        return DOCS.sync(self.repo, import_history=not (self.repo / DOCS.MANAGED[0]).exists(), **kwargs)

    def change(self, text='changed\n'):
        (self.repo / 'source.py').write_text(text)
        self.git('add', 'source.py')

    def establish_history(self):
        self.sync()
        self.git('commit', '-qm', 'bootstrap history')
        return self.git('rev-parse', 'HEAD').strip()

    def test_bootstrap_imports_git_subject_and_current_reference(self):
        data = self.sync()
        self.assertEqual(data['entries'][0]['summary'], 'synthetic baseline')
        self.assertEqual(data['entries'][0]['version'], '0.1.0')
        DOCS.check(self.repo)
        self.assertIn('/doforme:analyze', (self.repo / 'docs/REFERENCE.md').read_text())

    def test_english_history_rendering_preserves_canonical_committed_records(self):
        self.establish_history()
        original = json.loads((self.repo / 'docs/changes.json').read_text())
        old_id = original['entries'][0]['id']
        translations = self.repo / 'docs/history-translations.json'
        translations.write_text(json.dumps({old_id: 'English display summary'}))
        self.git('add', 'docs/history-translations.json')
        updated = self.sync(summary='Add English presentation')
        self.assertEqual(updated['entries'][:len(original['entries'])], original['entries'])
        self.assertIn('English display summary', (self.repo / 'CHANGELOG.md').read_text())
        self.assertIn('# doforme command reference', (self.repo / 'docs/REFERENCE.md').read_text())
        DOCS.check(self.repo)

    def test_history_translation_uses_staged_content_and_detects_unstaged_changes(self):
        data = self.sync()
        identity = data['entries'][0]['id']
        path = self.repo / 'docs/history-translations.json'
        path.write_text(json.dumps({identity: 'Reviewed English translation'}))
        self.git('add', 'docs/history-translations.json')
        path.write_text(json.dumps({identity: 'Unstaged owner draft'}))
        self.sync()
        self.assertIn('Reviewed English translation', (self.repo / 'CHANGELOG.md').read_text())
        self.assertNotIn('Unstaged owner draft', (self.repo / 'CHANGELOG.md').read_text())
        with self.assertRaisesRegex(ValueError, 'stale'):
            DOCS.check(self.repo)

    def test_invalid_history_translation_mapping_is_rejected(self):
        self.sync()
        path = self.repo / 'docs/history-translations.json'
        path.write_text(json.dumps({'invalid-change-id': 'Display text'}))
        self.git('add', 'docs/history-translations.json')
        with self.assertRaisesRegex(ValueError, 'History translations'):
            self.sync()

    def test_changes_are_recorded_from_index_without_staging_unrelated_source(self):
        self.change('staged\n')
        (self.repo / 'source.py').write_text('unstaged owner edits\n')
        data = self.sync(summary='Scoped fixture change')
        self.assertEqual((self.repo / 'source.py').read_text(), 'unstaged owner edits\n')
        self.assertEqual(self.git('show', ':source.py'), 'staged\n')
        self.assertEqual(data['entries'][-1]['summary'], 'Scoped fixture change')
        self.assertEqual(set(data['entries'][-1]['changes']), {'source.py'})

    def test_repeated_sync_is_idempotent_and_preserves_explicit_summary(self):
        self.change()
        first = self.sync(summary='Owner reviewed summary')
        before = {name: (self.repo / name).read_bytes() for name in DOCS.MANAGED}
        second = self.sync()
        self.assertEqual(first, second)
        self.assertEqual(before, {name: (self.repo / name).read_bytes() for name in DOCS.MANAGED})
        self.change('different staged bytes\n')
        third = self.sync()
        self.assertEqual(len(third['entries']), len(first['entries']))
        self.assertEqual(third['entries'][-1]['summary'], 'Owner reviewed summary')
        self.assertNotEqual(third['entries'][-1]['id'], first['entries'][-1]['id'])

    def test_reference_uses_staged_manifest_and_command_metadata(self):
        self.sync()
        manifest = self.repo / '.claude-plugin/plugin.json'
        manifest.write_text('{"name":"doforme","version":"0.2.0"}')
        self.git('add', '.claude-plugin/plugin.json')
        manifest.write_text('{"name":"doforme","version":"0.3.0"}')
        self.sync()
        self.assertIn('**0.2.0**', (self.repo / 'docs/REFERENCE.md').read_text())
        with self.assertRaisesRegex(ValueError, 'stale'):
            DOCS.check(self.repo)

    def test_unstaged_managed_edits_are_preserved(self):
        self.sync()
        path = self.repo / 'CHANGELOG.md'
        path.write_text('owner draft\n')
        self.change()
        with self.assertRaisesRegex(ValueError, 'Review/stage'):
            self.sync()
        self.assertEqual(path.read_text(), 'owner draft\n')

    def test_symlink_managed_path_cannot_overwrite_owner_file(self):
        outside = self.repo.parent / 'outside'
        outside.write_text('owner\n')
        (self.repo / 'CHANGELOG.md').symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            self.sync()
        self.assertEqual(outside.read_text(), 'owner\n')

    def test_history_coverage_passes_and_detects_unrecorded_content_change(self):
        self.establish_history()
        base = self.git('rev-parse', 'HEAD').strip()
        self.change()
        self.sync()
        self.git('commit', '-qm', 'recorded change')
        DOCS.verify_range(self.repo, base)
        self.change('unrecorded new content\n')
        self.git('commit', '-qm', 'simulate commit made without hook')
        with self.assertRaisesRegex(ValueError, 'missing current history content'):
            DOCS.verify_range(self.repo, base)

    def test_delete_and_rename_are_content_bound(self):
        base = self.establish_history()
        self.git('mv', 'source.py', 'renamed.py')
        data = self.sync()
        self.assertIsNone(data['entries'][-1]['changes']['source.py'])
        self.assertIsNotNone(data['entries'][-1]['changes']['renamed.py'])
        self.git('commit', '-qm', 'rename')
        DOCS.verify_range(self.repo, base)

    def test_multi_commit_history_survives_squash_with_final_content_coverage(self):
        base = self.establish_history()
        for content in ('first change\n', 'second change\n'):
            self.change(content)
            self.sync()
            self.git('commit', '-qm', 'recorded intermediate change')
        # Simulate a hosting-platform squash only in this disposable fixture.
        self.git('reset', '--soft', base)
        self.git('commit', '-qm', 'squashed change')
        DOCS.verify_range(self.repo, base)
        DOCS.check(self.repo)

    def test_old_history_cannot_be_rewritten(self):
        base = self.establish_history()
        path = self.repo / 'docs/changes.json'
        data = json.loads(path.read_text())
        data['entries'][0]['summary'] = 'rewritten historical claim'
        path.write_text(json.dumps(data))
        self.git('add', 'docs/changes.json')
        with self.assertRaisesRegex(ValueError, 'remain unchanged'):
            self.sync()
        self.git('commit', '-qm', 'simulate history tamper without hook')
        with self.assertRaisesRegex(ValueError, 'rewritten'):
            DOCS.verify_range(self.repo, base)

    def test_missing_history_and_stale_generated_docs_fail(self):
        with self.assertRaisesRegex(ValueError, 'Missing history'):
            DOCS.sync(self.repo)
        self.sync()
        (self.repo / 'docs/REFERENCE.md').write_text('out of date\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            DOCS.check(self.repo)

    def test_real_git_precommit_updates_and_commits_history_automatically(self):
        base = self.establish_history()
        HOOKS.install(self.repo)
        self.change('automatically recorded\n')
        self.git('commit', '-qm', 'ordinary commit with hook')
        committed = json.loads(self.git('show', 'HEAD:docs/changes.json'))
        self.assertEqual(committed['entries'][-1]['base_commit'], base)
        self.assertIn('source.py', committed['entries'][-1]['changes'])
        self.assertEqual(self.git('status', '--porcelain').strip(), '')
        DOCS.check(self.repo)
        DOCS.verify_range(self.repo, base)

    def test_existing_default_hook_is_not_replaced(self):
        hook = self.repo / '.git/hooks/pre-commit'
        hook.write_text('owner hook\n')
        with self.assertRaisesRegex(ValueError, 'Existing pre-commit'):
            HOOKS.install(self.repo)
        self.assertEqual(hook.read_text(), 'owner hook\n')

    def test_existing_hooks_path_is_preserved(self):
        self.git('config', 'core.hooksPath', 'owner-hooks')
        with self.assertRaisesRegex(ValueError, 'Existing hooksPath'):
            HOOKS.install(self.repo)
        self.assertEqual(self.git('config', 'core.hooksPath').strip(), 'owner-hooks')

    def test_global_hooks_path_is_respected(self):
        from unittest.mock import patch
        config = self.repo.parent / 'gitconfig'
        config.write_text('[core]\n hooksPath = global-owner-hooks\n')
        original = HOOKS.subprocess.run
        def configured(*args, **kwargs):
            # Simulate a global user config after installer strips inherited Git overrides.
            kwargs['env'] = {**kwargs['env'], 'GIT_CONFIG_GLOBAL': str(config)}
            return original(*args, **kwargs)
        with patch.object(HOOKS.subprocess, 'run', side_effect=configured):
            with self.assertRaisesRegex(ValueError, 'Existing hooksPath'):
                HOOKS.install(self.repo)


if __name__ == '__main__':
    unittest.main()
