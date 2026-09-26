import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'installer.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def result(code=0, out=''):
    return subprocess.CompletedProcess([], code, out, '')


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = mod.Installer(self.root / 'app', True)
        self.app.state = self.root / 'state'
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_omarchy_identity_and_architecture(self):
        self.assertTrue(mod.supported({'ID':'omarchy','ID_LIKE':'arch'}, 'x86_64'))
        self.assertFalse(mod.supported({'ID':'arch'}, 'x86_64'))
        self.assertFalse(mod.supported({'ID':'omarchy'}, 'aarch64'))

    def test_refuses_root_execution(self):
        with patch.object(mod.os, 'geteuid', return_value=0):
            with self.assertRaisesRegex(mod.InstallError, 'usuário comum'):
                self.app.environment()

    def test_unsafe_target_and_symlink(self):
        for value in ('/', '/data', str(Path.home()), '/tmp/app\necho injected'):
            with self.assertRaises(mod.InstallError):
                mod.safe_target(value)
        (self.root / 'link').symlink_to(self.root)
        with self.assertRaises(mod.InstallError):
            mod.safe_target(self.root / 'link/app')

    def test_missing_tools_provisioned_once_and_rechecked(self):
        self.app.missing_packages = Mock(side_effect=[['github-cli', 'libsecret'], []])
        self.app.command = Mock(return_value=result())
        self.app.packages()
        self.assertEqual(self.app.command.call_args_list[0].args[0],
                         ['/usr/bin/pkexec','/usr/bin/pacman','-S','--needed','github-cli','libsecret'])
        self.assertEqual(self.app.missing_packages.call_count, 2)

    def test_existing_alternative_tool_does_not_require_canonical_package(self):
        with patch.object(mod.shutil, 'which', return_value='/custom/bin/tool'):
            self.app.command = Mock(return_value=result())
            self.assertEqual(self.app.missing_packages(), [])
            self.assertEqual(len(self.app.command.call_args_list), len(mod.LIBRARIES))

    def test_missing_library_still_blocks_after_install(self):
        self.app.missing_packages = Mock(return_value=['libsecret'])
        self.app.command = Mock(return_value=result())
        with self.assertRaisesRegex(mod.InstallError, 'Ainda faltam'):
            self.app.packages()

    def test_access_denied_stops_before_clone(self):
        with patch.object(mod.shutil, 'which', return_value='/usr/bin/gh'):
            self.app.command = Mock(side_effect=[result(), result(1)])
            with self.assertRaisesRegex(mod.InstallError, 'ACESSO NEGADO'):
                self.app.source()
        self.assertFalse(self.app.target.exists())
        self.assertFalse(any('clone' in call.args[0] for call in self.app.command.call_args_list))

    def test_check_never_starts_login(self):
        with patch.object(mod.shutil, 'which', return_value='/usr/bin/gh'):
            self.app.command = Mock(return_value=result(1))
            with self.assertRaisesRegex(mod.InstallError, 'não autenticada'):
                self.app.access(login=False)
        self.assertEqual(self.app.command.call_count, 1)

    def test_node_probe_does_not_use_auto_installing_exec(self):
        self.app.command = Mock(side_effect=[result(0,str(self.root)), result(0,'v24.11.1\n')])
        self.app.verify_node()
        commands = [c.args[0] for c in self.app.command.call_args_list]
        self.assertEqual(commands[0], ['mise','where','node@24.11.1'])
        self.assertNotIn('exec', commands[0])
        self.assertNotIn('install', commands[0])

    def test_wrong_node_rejected(self):
        self.app.command = Mock(side_effect=[result(0,str(self.root)), result(0,'v26.9.0')])
        with self.assertRaisesRegex(mod.InstallError, 'diferente'):
            self.app.verify_node()

    def source_fixture(self):
        (self.app.target / '.git').mkdir(parents=True)

    def test_existing_wrong_revision_preserved(self):
        self.source_fixture()
        marker = self.app.target / 'precious.txt'
        marker.write_text('preserve')
        self.app.command = Mock(return_value=result(0, 'f'*40))
        with self.assertRaisesRegex(mod.InstallError, 'outra revisão'):
            self.app.verify_source()
        self.assertEqual(marker.read_text(), 'preserve')

    def test_dirty_checkout_preserved(self):
        self.source_fixture()
        self.app.command = Mock(side_effect=[result(0,mod.MANIFEST['commit']), result(0,' M package.json')])
        with self.assertRaisesRegex(mod.InstallError, 'alterações locais'):
            self.app.verify_source()

    def test_incorrect_hash_rejected(self):
        self.source_fixture()
        (self.app.target / 'package.json').write_text('{}')
        self.app.command = Mock(side_effect=[result(0,mod.MANIFEST['commit']), result()])
        with self.assertRaisesRegex(mod.InstallError, 'Hash divergente'):
            self.app.verify_source()

    def test_rebuild_missing_dependency_is_actionable(self):
        self.app.prebuild = Mock()
        with self.assertRaisesRegex(mod.InstallError, 'dependencies'):
            self.app.rebuild()

    def test_failed_command_does_not_continue_sequence(self):
        self.app.show_plan = Mock()
        self.app.step = Mock(side_effect=[None, mod.InstallError('falhou')])
        with self.assertRaises(mod.InstallError):
            self.app.install()
        self.assertEqual([c.args[0] for c in self.app.step.call_args_list], ['environment','packages'])

    def test_failure_recorded_with_exit(self):
        self.app.begin()
        with patch.object(mod.subprocess, 'run', return_value=result(7)):
            with self.assertRaisesRegex(mod.InstallError, 'exit 7'):
                self.app.command(['fake','argument'])
        evidence = json.loads((self.app.run_dir / 'report.json').read_text())
        self.assertEqual(evidence['commands'][0]['exit'], 7)

    def test_config_backup_and_idempotence(self):
        target = self.root / 'lionclaw.desktop'
        target.write_text('original')
        self.app.write_backed_up(target, 'updated')
        before = target.stat().st_mtime_ns
        self.app.write_backed_up(target, 'updated')
        self.assertEqual(target.stat().st_mtime_ns, before)
        self.assertEqual((self.app.run_dir / 'lionclaw.desktop.before').read_text(), 'original')

    def test_config_symlink_not_overwritten(self):
        real = self.root / 'important'
        real.write_text('original')
        link = self.root / 'launcher'
        link.symlink_to(real)
        with self.assertRaises(mod.InstallError):
            self.app.write_backed_up(link,'bad')
        self.assertEqual(real.read_text(), 'original')

    def test_desktop_metacharacters_and_spaces(self):
        target = self.root / 'app with spaces $HOME % test'
        launcher = target / 'launch.sh'
        text = mod.desktop_text(launcher, target)
        self.assertIn('\\$HOME', text)
        self.assertIn('%%', text)
        self.assertIn('Exec="', text)
        self.assertNotIn('sh -c', text)

    def test_launcher_uses_native_wayland(self):
        for name in ('verify_source', 'verify_build', 'native_check'):
            setattr(self.app, name, Mock())
        self.app.command = Mock(return_value=result())
        data = self.root / 'data'
        with patch.dict(mod.os.environ, {'XDG_DATA_HOME': str(data)}), \
             patch.object(mod.shutil, 'which', return_value='/usr/bin/mise'):
            self.app.menu()
        script = (data / 'lionclaw-omarchy/launch.sh').read_text()
        head = script[:script.index('exec ')]
        self.assertIn('export ELECTRON_OZONE_PLATFORM_HINT=wayland\n', head)
        self.assertIn('export LIONCLAW_ENABLE_HARDWARE_ACCELERATION=1\n', head)
        self.assertNotIn('x11', script)

    def test_first_run_uses_native_wayland(self):
        for name in ('verify_source', 'verify_build', 'native_check', 'confirm'):
            setattr(self.app, name, Mock())
        self.app.command = Mock(return_value=result())
        with patch.dict(mod.os.environ, {'CODEX_HOME': str(self.root / 'codex')}):
            self.app.first_run()
        env = self.app.command.call_args.kwargs['env']
        self.assertEqual(env['ELECTRON_OZONE_PLATFORM_HINT'], 'wayland')
        self.assertEqual(env['LIONCLAW_ENABLE_HARDWARE_ACCELERATION'], '1')

    def test_native_probe_does_not_launch_application(self):
        electron = self.app.target / 'node_modules/electron/dist/electron'
        electron.parent.mkdir(parents=True)
        electron.touch()
        payload = {'electron':'33.4.11','sqlite':'OK','pty':'PTY_OK'}
        self.app.command = Mock(return_value=result(0,json.dumps(payload)))
        self.app.native_check()
        call = self.app.command.call_args
        self.assertEqual(call.kwargs['env']['ELECTRON_RUN_AS_NODE'], '1')
        self.assertEqual(call.args[0][1], ROOT / 'native-check.cjs')
        self.assertIsNone(self.app.run_dir)

    def test_steps_are_shared_and_cover_sequence(self):
        self.assertEqual(len(mod.STEPS), 13)
        ids = [s['id'] for s in mod.STEPS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(mod.SEQUENCE).issubset(ids))
        for step in mod.STEPS:
            self.assertTrue(step['sections'])

    def test_plan_without_network_or_state(self):
        with patch.object(mod.subprocess, 'run', side_effect=AssertionError('no subprocess')):
            self.app.show_plan()
        self.assertFalse(self.app.state.exists())

    def test_bootstrap_without_python_does_not_mutate_check_mode(self):
        commands = self.root / 'bin'
        commands.mkdir()
        (commands / 'dirname').symlink_to('/usr/bin/dirname')
        run = subprocess.run(['/usr/bin/bash', str(ROOT / 'install.sh'), '--check'],
                             env={'PATH':str(commands)}, capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('Nenhuma alteração', run.stdout)


if __name__ == '__main__':
    unittest.main()
