import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import dictation
import installer

SPEC = importlib.util.spec_from_file_location('paste', installer.ROOT / 'voxtype-paste.py')
paste = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(paste)
CONFIG = '# keep comments\n[whisper]\nmodel="custom"\nlanguage="pt"\n[audio]\ndevice="mic"\n[output]\nmode="type"\n[text]\nsmart_auto_submit=false\n'


class DictationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.app = installer.Installer(self.root / 'app', True)
        self.app.state = self.root / 'state'
        self.enterContext(patch.dict(os.environ, XDG_CONFIG_HOME=str(self.root / 'config')))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(patch.object(installer.shutil, 'which', return_value='/usr/bin/tool'))
        self.config, self.helper = self.app.dictation_paths()
        self.config.parent.mkdir(parents=True)
        self.config.write_text(CONFIG)
        self.calls = []
        self.busy = False
        self.fail_restart = False
        self.app.command = self.command

    def command(self, args, **kwargs):
        self.calls.append(args)
        out = ''
        if args[:2] == ['hyprctl', 'version']:
            out = json.dumps({'version': '0.56.2'})
        elif args == ['voxtype', '--help']:
            out = '--post-output-command'
        elif args == ['voxtype', 'status']:
            out = 'recording' if self.busy else 'idle'
        elif args[:3] == ['voxtype', 'config', 'get']:
            out = 'clipboard'
        elif 'restart' in args and self.fail_restart:
            self.fail_restart = False
            raise installer.InstallError('restart failed')
        return subprocess.CompletedProcess(args, 0, out, '')

    def test_preserves_settings_backup_and_repeat(self):
        self.app.dictation()
        data = tomllib.loads(self.config.read_text())
        self.assertEqual(data['whisper'], {'model': 'custom', 'language': 'pt'})
        self.assertEqual(data['audio']['device'], 'mic')
        self.assertIn('# keep comments', self.config.read_text())
        self.assertEqual(data['output']['mode'], 'clipboard')
        self.assertFalse(data['output']['auto_submit'])
        self.assertEqual((self.app.run_dir / 'config.toml.before').read_text(), CONFIG)
        before = self.config.stat().st_mtime_ns
        self.calls.clear()
        self.app.dictation()
        self.assertEqual(before, self.config.stat().st_mtime_ns)
        self.assertFalse(any('restart' in c for c in self.calls))
        self.assertEqual(self.app.report['dictation']['visual_f9'], 'NOT_VERIFIED')

    def test_busy_service_is_not_interrupted(self):
        self.busy = True
        with self.assertRaisesRegex(installer.InstallError, 'ocupado'):
            self.app.dictation()
        self.assertEqual(self.config.read_text(), CONFIG)
        self.assertFalse(self.helper.exists())
        self.assertFalse(any('restart' in c for c in self.calls))

    def test_custom_hook_is_not_overwritten(self):
        custom = CONFIG.replace('mode="type"', 'mode="type"\npost_output_command="my-hook"')
        self.config.write_text(custom)
        with self.assertRaisesRegex(installer.InstallError, 'personalizado'):
            self.app.dictation()
        self.assertEqual(self.config.read_text(), custom)
        self.assertFalse(self.helper.exists())

    def test_restart_failure_rolls_back_both_files(self):
        self.helper.write_text('original helper')
        self.fail_restart = True
        with self.assertRaisesRegex(installer.InstallError, 'restart failed'):
            self.app.dictation()
        self.assertEqual(self.config.read_text(), CONFIG)
        self.assertEqual(self.helper.read_text(), 'original helper')

    def test_rollback_removes_only_new_helper(self):
        self.fail_restart = True
        with self.assertRaises(installer.InstallError):
            self.app.dictation()
        self.assertFalse(self.helper.exists())
        self.assertEqual(self.config.read_text(), CONFIG)

    def test_diagnosis_never_writes_or_restarts(self):
        with self.assertRaisesRegex(installer.InstallError, 'revisão'):
            self.app.verify_dictation()
        self.assertEqual(self.config.read_text(), CONFIG)
        self.assertFalse(self.app.state.exists())
        self.assertEqual(self.calls, [])

    def test_optional_without_voxtype(self):
        with patch.object(installer.shutil, 'which', return_value=None):
            self.assertIn('NÃO APLICÁVEL', self.app.verify_dictation())
        self.assertNotIn('dictation', installer.SEQUENCE)

    def test_quoted_paths_and_missing_newline(self):
        helper = Path('/tmp/a b/$HOME `cmd`/paste.py')
        candidate = dictation.configure('[output]\nmode="type"', helper)
        output = tomllib.loads(candidate)['output']
        import shlex
        self.assertEqual(shlex.split(output['post_output_command']), ['/usr/bin/python3', str(helper)])
        self.assertEqual(dictation.configure(candidate, helper), candidate)

    def test_inline_table_and_smart_submit_refused(self):
        for text in ('output={mode="type"}', CONFIG.replace('smart_auto_submit=false', 'smart_auto_submit=true')):
            with self.assertRaises(ValueError):
                dictation.configure(text, self.helper)

    def test_symlink_is_not_overwritten(self):
        self.helper.symlink_to(self.config)
        with self.assertRaisesRegex(installer.InstallError, 'symlink'):
            self.app.dictation()
        self.assertEqual(self.config.read_text(), CONFIG)


class PasteTests(unittest.TestCase):
    def test_gui_and_terminal_chords_keep_same_destination(self):
        for tags, mods, key in [([], 'CTRL', 'V'), (['terminal*'], 'SHIFT', 'Insert')]:
            with self.subTest(tags=tags), patch.object(paste, 'hyprctl', side_effect=[json.dumps({'address':'0x123', 'tags':tags}), 'ok', 'ok']) as call, patch.object(paste.time, 'sleep'):
                paste.main()
                commands = [c.args[1] for c in call.call_args_list[1:]]
                self.assertEqual(len(commands), 2)
                for cmd in commands:
                    self.assertIn(f'mods = "{mods}"', cmd)
                    self.assertIn(f'key = "{key}"', cmd)
                    self.assertIn('window = "address:0x123"', cmd)
                self.assertIn('state = "up"', commands[-1])

    def test_release_even_after_press_failure(self):
        with patch.object(paste, 'hyprctl', side_effect=[json.dumps({'address':'0x123'}), OSError('failed'), 'ok']) as call:
            with self.assertRaises(OSError):
                paste.main()
            self.assertIn('state = "up"', call.call_args_list[-1].args[1])

    def test_no_window_sends_no_keys(self):
        with patch.object(paste, 'hyprctl', return_value='{}') as call:
            with self.assertRaises(SystemExit):
                paste.main()
            self.assertEqual(call.call_count, 1)
