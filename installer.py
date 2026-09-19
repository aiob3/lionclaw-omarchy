#!/usr/bin/env python3
"""Instalador comunitário, sem dependências Python externas e sem código LionClaw."""
from __future__ import annotations

import argparse
import curses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / 'manifest.json').read_text())
STEPS = json.loads((ROOT / 'docs' / 'steps.json').read_text())
SEQUENCE = ['environment', 'packages', 'access', 'node', 'source',
            'dependencies', 'rebuild', 'build', 'menu']
# Comandos existentes são aceitos mesmo quando vieram de mise/bin ou pacote alternativo.
COMMAND_PACKAGES = {'git': 'git', 'gh': 'github-cli', 'mise': 'mise',
                    'python3': 'python', 'make': 'base-devel', 'gcc': 'base-devel',
                    'g++': 'base-devel', 'pkg-config': 'pkgconf',
                    'desktop-file-validate': 'desktop-file-utils',
                    'update-desktop-database': 'desktop-file-utils', 'Xwayland': 'xorg-xwayland'}
LIBRARIES = ['libsecret', 'gtk3', 'nss', 'alsa-lib', 'libxss', 'libxtst', 'libnotify']


class InstallError(RuntimeError):
    pass


def os_release(path=Path('/etc/os-release')):
    result = {}
    for line in path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            result[k] = v.strip('"\'')
    return result


def supported(info, machine):
    return info.get('ID') == 'omarchy' and machine == MANIFEST['architecture']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_target(raw):
    target = Path(raw).expanduser().absolute()
    if any(ord(c) < 32 for c in str(target)):
        raise InstallError('O caminho não pode conter caracteres de controle.')
    # Evita perder identidade do diretório por symlinks e recusa raízes gerais.
    if target.resolve() != target:
        raise InstallError('Use um caminho direto, sem symlinks ou segmentos ..')
    if target in {Path('/'), Path.home(), Path('/data'), Path('/usr'), Path('/etc'), Path('/tmp')}:
        raise InstallError('Escolha uma subpasta exclusiva para LionClaw.')
    return target


def desktop_quote(value):
    # Desktop Entry usa regras próprias, não aspas de shell.
    value = str(value).replace('%', '%%')
    for ch in ('\\', '"', '`', '$'):
        value = value.replace(ch, '\\' + ch)
    return '"' + value + '"'


def desktop_text(launcher, target):
    # Path e Icon não são Exec; espaços são literais, backslash é escape desktop.
    field = lambda p: str(p).replace('\\', '\\\\')
    return '\n'.join([
        '[Desktop Entry]', 'Version=1.0', 'Type=Application', 'Name=LionClaw',
        'Comment=Assistente pessoal de inteligência artificial',
        'Exec=' + desktop_quote(launcher), 'Path=' + field(target),
        'Icon=' + field(target / 'resources/logo-lionclaw.png'),
        'Terminal=false', 'Categories=Utility;', 'Keywords=IA;AI;assistente;LionLabs;',
        'StartupWMClass=lionclaw', 'StartupNotify=true', ''])


class Installer:
    def __init__(self, target, assume_yes=False):
        self.target = safe_target(target)
        self.assume_yes = assume_yes
        self.state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'lionclaw-installer'
        self.run_dir = None
        self.report = {'installer': MANIFEST['installer_version'], 'revision': MANIFEST['commit'], 'steps': []}

    def confirm(self, message, *, always=False):
        if self.assume_yes and not always:
            return
        if not sys.stdin.isatty():
            raise InstallError('Confirmação requer terminal. Use --yes apenas para as etapas de instalação; abertura é sempre interativa.')
        if input(message + ' [s/N] ').strip().lower() not in ('s', 'sim'):
            raise InstallError('Cancelado; nenhuma etapa seguinte foi executada.')

    def begin(self):
        if self.run_dir is None:
            self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.run_dir = Path(tempfile.mkdtemp(prefix=dt.datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=self.state))
            self.save_report()

    def save_report(self):
        if self.run_dir:
            path = self.run_dir / 'report.json'
            path.write_text(json.dumps(self.report, ensure_ascii=False, indent=2) + '\n')
            path.chmod(0o600)

    def command(self, args, *, cwd=None, capture=False, check=True, env=None, timeout=None, record=True):
        command = [str(a) for a in args]
        if not capture:
            print('\n$ ' + shlex.join(command), flush=True)
        try:
            result = subprocess.run(command, cwd=cwd, env=env, text=True,
                                    stdout=subprocess.PIPE if capture else None,
                                    stderr=subprocess.PIPE if capture else None,
                                    timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise InstallError(f'Não foi possível executar {command[0]}: {exc}') from exc
        if record and self.run_dir:
            self.report.setdefault('commands', []).append({'argv': command, 'exit': result.returncode})
            self.save_report()
        if check and result.returncode:
            # Não publica stdout de autenticação, tokens ou subprocessos do upstream.
            raise InstallError(f'Comando falhou (exit {result.returncode}): {shlex.join(command)}. Corrija a causa antes de repetir a etapa.')
        return result

    def environment(self):
        if os.geteuid() == 0:
            raise InstallError('Execute como usuário comum. Somente pacman será elevado via pkexec.')
        info = os_release()
        if not supported(info, platform.machine()):
            raise InstallError('Escopo validado: Omarchy Linux x86_64. Este ambiente não corresponde.')
        if not Path('/usr/bin/pacman').is_file() or not Path('/usr/bin/pkexec').is_file():
            raise InstallError('pacman e pkexec são requisitos do sistema Omarchy.')
        print(f"OK: {info.get('PRETTY_NAME', 'Omarchy')} · {platform.machine()}")

    def missing_packages(self):
        missing = {package for cmd, package in COMMAND_PACKAGES.items() if not shutil.which(cmd)}
        for package in LIBRARIES:
            if self.command(['/usr/bin/pacman', '-Q', package], capture=True, check=False, record=False).returncode:
                missing.add(package)
        return sorted(missing)

    def packages(self):
        missing = self.missing_packages()
        if missing:
            print('Pacotes ausentes: ' + ', '.join(missing))
            self.confirm('Provisionar esses pacotes com pacman?')
            self.command(['/usr/bin/pkexec', '/usr/bin/pacman', '-S', '--needed', *missing])
        remaining = self.missing_packages()
        if remaining:
            raise InstallError('Ainda faltam: ' + ', '.join(remaining))
        self.command(['pkg-config', '--exists', 'libsecret-1'])
        print('OK: ferramentas e bibliotecas presentes. Nenhum Electron global é necessário.')

    def access(self, login=True):
        if not shutil.which('gh'):
            raise InstallError('GitHub CLI ausente. Execute a etapa packages primeiro.')
        authenticated = self.command(['gh', 'auth', 'status', '--hostname', 'github.com'], capture=True, check=False).returncode == 0
        if not authenticated and login:
            self.confirm('Autenticar sua conta GitHub pelo fluxo oficial do gh?', always=True)
            self.command(['gh', 'auth', 'login', '--hostname', 'github.com', '--git-protocol', 'https', '--web'])
        elif not authenticated:
            raise InstallError('Conta GitHub não autenticada.')
        response = self.command(['gh', 'api', 'repos/' + MANIFEST['repository'], '--jq', '.full_name'], capture=True, check=False)
        if response.returncode or response.stdout.strip().lower() != MANIFEST['repository'].lower():
            raise InstallError('ACESSO NEGADO ou GitHub indisponível. Confirme rede, conta e convite ao repositório oficial. O instalador público não concede acesso.')
        print('OK: sua conta consegue ler o repositório oficial.')

    def node(self):
        if not shutil.which('mise'):
            raise InstallError('mise ausente. Execute packages primeiro.')
        self.command(['mise', 'install', 'node@' + MANIFEST['node']], cwd=Path.home())
        self.verify_node()

    def node_command(self, *args):
        return ['mise', 'exec', 'node@' + MANIFEST['node'], '--', *args]

    def verify_node(self):
        # mise exec pode auto-instalar. O diagnóstico só consulta instalações existentes.
        location = self.command(['mise', 'where', 'node@' + MANIFEST['node']], cwd=Path.home(), capture=True)
        executable = Path(location.stdout.strip()) / 'bin/node'
        result = self.command([executable, '--version'], cwd=Path.home(), capture=True)
        if result.stdout.strip() != 'v' + MANIFEST['node']:
            raise InstallError('Node efetivo diferente da versão fixada.')
        print('OK: Node ' + result.stdout.strip())

    def verify_source(self):
        if not (self.target / '.git').is_dir():
            raise InstallError('Destino não é um checkout Git independente. Execute source ou use outra pasta.')
        head = self.command(['git', '-C', self.target, 'rev-parse', 'HEAD'], capture=True).stdout.strip()
        if head != MANIFEST['commit']:
            raise InstallError('Checkout existente está em outra revisão. Não será sobrescrito; escolha uma nova pasta.')
        dirty = self.command(['git', '-C', self.target, 'status', '--porcelain'], capture=True).stdout.strip()
        if dirty:
            raise InstallError('Checkout tem alterações locais. Preserve seu trabalho antes de instalar; nenhum reset foi executado.')
        for filename, expected in MANIFEST['sha256'].items():
            path = self.target / filename
            if not path.is_file() or digest(path) != expected:
                raise InstallError('Hash divergente: ' + filename)
        package = json.loads((self.target / 'package.json').read_text())
        if package['version'] != MANIFEST['application_version']:
            raise InstallError('Versão da aplicação diverge do manifesto.')
        print('OK: revisão e hashes conferidos.')

    def source(self):
        self.access(login=False)
        if self.target.exists():
            self.verify_source()
            return
        if not self.target.parent.is_dir() or not os.access(self.target.parent, os.W_OK):
            raise InstallError('O diretório pai deve existir e pertencer a você. Escolha --target em uma pasta gravável; não execute Git como root.')
        self.confirm(f'Clonar a revisão validada em {self.target}?')
        stage = Path(tempfile.mkdtemp(prefix='.lionclaw-staging-', dir=self.target.parent))
        # Credencial temporária por comando: não reescreve ~/.gitconfig nem incorpora token em URL.
        helper = '!' + shlex.quote(shutil.which('gh')) + ' auth git-credential'
        git_auth = ['git', '-c', 'credential.helper=', '-c', 'credential.helper=' + helper]
        try:
            self.command([*git_auth, 'clone', '--filter=blob:none', '--no-checkout',
                          'https://github.com/' + MANIFEST['repository'] + '.git', stage])
            self.command([*git_auth, '-C', stage, 'checkout', '--detach', MANIFEST['commit']])
            for name, expected in MANIFEST['sha256'].items():
                if digest(stage / name) != expected:
                    raise InstallError('Hash divergente no clone: ' + name)
            if self.target.exists():
                raise InstallError('O destino apareceu durante o clone; staging preservado.')
            stage.rename(self.target)
        except BaseException:
            print(f'Clone parcial preservado para inspeção: {stage}', file=sys.stderr)
            raise
        self.verify_source()

    def require_stopped(self):
        executable = str(self.target / 'node_modules/electron/dist/electron')
        for proc in Path('/proc').glob('[0-9]*/cmdline'):
            try:
                first = proc.read_bytes().split(b'\0', 1)[0].decode(errors='replace')
                if first == executable:
                    raise InstallError('LionClaw está aberto neste destino. Feche a aplicação antes de recompilar ou reinstalar.')
            except (OSError, PermissionError):
                continue

    def prebuild(self):
        self.verify_source()
        self.verify_node()
        self.require_stopped()

    def dependencies(self):
        self.prebuild()
        if self.missing_packages():
            raise InstallError('Há requisitos ausentes. Execute packages primeiro.')
        self.confirm('Instalar dependências e executar postinstall do código oficial? npm ci recria node_modules.')
        self.command(self.node_command('npm', 'ci', '--no-audit', '--no-fund'), cwd=self.target)
        if not (self.target / 'node_modules/.bin/electron-rebuild').is_file():
            raise InstallError('electron-rebuild continua ausente após npm ci.')
        installed = json.loads((self.target / 'node_modules/electron/package.json').read_text())
        if installed['version'] != MANIFEST['electron']:
            raise InstallError('Electron instalado diverge do manifesto.')
        print('OK: dependências e ferramenta electron-rebuild disponíveis.')

    def rebuild(self):
        self.prebuild()
        if not (self.target / 'node_modules/.bin/electron-rebuild').is_file():
            raise InstallError('Execute dependencies com sucesso antes do rebuild. Não instale electron-rebuild globalmente.')
        self.command(self.node_command('npm', 'run', 'rebuild:electron'), cwd=self.target)
        self.native_check()

    def native_check(self):
        electron = self.target / 'node_modules/electron/dist/electron'
        if not electron.is_file():
            raise InstallError('Binário local Electron ausente. Execute dependencies.')
        # Teste não inicializa o app, banco pessoal ou sincronização de MCPs.
        env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
        result = self.command([electron, ROOT / 'native-check.cjs'], cwd=self.target, env=env, capture=True, timeout=30)
        evidence = json.loads(result.stdout.strip().splitlines()[-1])
        if evidence.get('sqlite') != 'OK' or evidence.get('pty') != 'PTY_OK' or evidence.get('electron') != MANIFEST['electron']:
            raise InstallError('Prova nativa incompleta.')
        print(json.dumps(evidence, ensure_ascii=False))
        self.report['native_evidence'] = evidence
        self.save_report()

    def build(self):
        self.prebuild()
        self.command(self.node_command('npm', 'run', 'build'), cwd=self.target)
        self.verify_build()
        self.native_check()

    def verify_build(self):
        for name in ['dist/main/index.js', 'dist/preload/index.js', 'dist/renderer/index.html']:
            if not (self.target / name).is_file():
                raise InstallError('Artefato ausente: ' + name + '. Execute build.')
        print('OK: main, preload e interface compilados.')

    def write_backed_up(self, path, content, mode=0o644):
        if path.is_symlink():
            raise InstallError('Destino de configuração é symlink; não será substituído: ' + str(path))
        if path.is_file() and path.read_text() == content:
            print('Já atualizado: ' + str(path))
            return
        self.begin()
        if path.exists():
            backup = self.run_dir / (path.name + '.before')
            if not backup.exists():
                shutil.copy2(path, backup)
            backup.chmod(0o600)
            print('Backup: ' + str(backup))
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as stream:
            stream.write(content)
            temp = Path(stream.name)
        temp.chmod(mode)
        temp.replace(path)

    def menu(self):
        self.verify_source()
        self.verify_build()
        self.native_check()
        data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
        launcher = data / 'lionclaw-omarchy' / 'launch.sh'
        desktop = data / 'applications' / 'lionclaw.desktop'
        mise = shutil.which('mise')
        if not mise:
            raise InstallError('mise ausente.')
        env = 'unset ELECTRON_RUN_AS_NODE\nexport NODE_ENV=production\nexport ELECTRON_OZONE_PLATFORM_HINT=x11\n'
        command = [mise, 'exec', 'node@' + MANIFEST['node'], '--',
                   str(self.target / 'node_modules/electron/dist/electron'), str(self.target)]
        script = '#!/usr/bin/env bash\nset -euo pipefail\n' + env
        script += 'cd -- ' + shlex.quote(str(self.target)) + '\nexec ' + shlex.join(command) + '\n'
        self.write_backed_up(launcher, script, 0o755)
        content = desktop_text(launcher, self.target)
        # Valida o candidato antes de substituir o arquivo do usuário.
        self.begin()
        candidate = self.run_dir / 'lionclaw.desktop'
        candidate.write_text(content)
        self.command(['desktop-file-validate', candidate])
        self.write_backed_up(desktop, content)
        self.command(['update-desktop-database', desktop.parent])
        print('OK: procure LionClaw no menu. A aplicação não foi aberta automaticamente.')

    def first_run(self):
        self.verify_source()
        self.verify_build()
        self.native_check()
        print('O aplicativo criará ~/.lionclaw e poderá sincronizar MCPs em ~/.codex/config.toml.')
        print('O componente LionDesign pode baixar dependências adicionais no primeiro início.')
        self.confirm('Abrir o aplicativo agora? Login e credenciais serão preenchidos por você.', always=True)
        config = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'config.toml'
        self.begin()
        if config.exists():
            backup = self.run_dir / 'codex-config.toml.before'
            if not backup.exists():
                shutil.copy2(config, backup)
            backup.chmod(0o600)
            print('Backup privado da configuração Codex: ' + str(backup))
        env = dict(os.environ, NODE_ENV='production', ELECTRON_OZONE_PLATFORM_HINT='x11')
        env.pop('ELECTRON_RUN_AS_NODE', None)
        print('Feche a janela para retornar ao instalador. Nenhuma chave será solicitada aqui.')
        self.command(self.node_command(str(self.target / 'node_modules/electron/dist/electron'), str(self.target)), cwd=self.target, env=env)

    def check(self):
        rows = []
        def probe(name, call):
            try:
                value = call()
                rows.append({'id': name, 'status': 'OK', 'detail': value or 'Verificado'})
            except (InstallError, OSError, ValueError, KeyError) as exc:
                rows.append({'id': name, 'status': 'PENDENTE', 'detail': str(exc)})
        probe('environment', self.environment)
        def packages_probe():
            missing = self.missing_packages()
            if missing:
                raise InstallError(', '.join(missing))
        probe('packages', packages_probe)
        probe('access', lambda: self.access(login=False))
        probe('node', self.verify_node)
        probe('source', self.verify_source)
        probe('build', self.verify_build)
        print(json.dumps({'target': str(self.target), 'checks': rows}, ensure_ascii=False, indent=2))
        return 0 if all(r['status'] == 'OK' for r in rows) else 2

    def step(self, identifier):
        methods = {'first-run': self.first_run, 'diagnosis': self.check, 'overview': self.show_plan}
        method = methods.get(identifier) or getattr(self, identifier, None)
        if not method or identifier not in {s['id'] for s in STEPS}:
            raise InstallError('Etapa desconhecida: ' + identifier)
        self.environment()
        self.begin()
        row = {'id': identifier, 'status': 'RUNNING'}
        self.report['steps'].append(row)
        self.save_report()
        try:
            result = method()
            if isinstance(result, int) and result != 0:
                raise InstallError('Diagnóstico contém pendências.')
        except BaseException:
            row['status'] = 'FAILED'
            self.save_report()
            raise
        row['status'] = 'PASSED'
        self.save_report()
        print('Etapa concluída: ' + identifier)

    def show_plan(self):
        print(f"LionClaw {MANIFEST['application_version']} · revisão {MANIFEST['commit']}\nDestino: {self.target}")
        for step in STEPS:
            print(f"{step['number']:02d} {step['title']}\n   {step['summary']}")

    def install(self):
        self.show_plan()
        self.confirm('Executar a sequência até registrar o menu? O aplicativo não será aberto.')
        for identifier in SEQUENCE:
            self.step(identifier)

    def tui(self):
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            self.show_plan()
            print('\nTUI requer terminal. Use --check, --plan ou --install.')
            return
        def draw(screen):
            try:
                curses.curs_set(0)
            except curses.error:
                pass
            screen.keypad(True)
            current = 0
            while True:
                screen.erase()
                h, w = screen.getmaxyx()
                def put(y, x, value, attr=0):
                    if 0 <= y < h - 1 and 0 <= x < w - 1:
                        try:
                            screen.addnstr(y, x, value, max(0, w - x - 1), attr)
                        except curses.error:
                            pass
                put(0, 2, 'LionClaw / Omarchy — instalador comunitário', curses.A_BOLD)
                if w < 78 or h < 20:
                    put(3, 2, 'Amplie o terminal para 78 × 20. Q sai; --plan funciona em qualquer tamanho.')
                else:
                    for i, step in enumerate(STEPS):
                        history = [row for row in self.report['steps'] if row['id'] == step['id']]
                        status = history[-1]['status'] if history else ''
                        marker = '+' if status == 'PASSED' else '!' if status == 'FAILED' else ' '
                        put(i + 3, 2, f"{step['number']:02d}{marker} {step['title'][:27]}", curses.A_REVERSE if i == current else 0)
                    step = STEPS[current]
                    put(3, 37, step['title'], curses.A_BOLD)
                    desc = step['summary'] + '\n\n' + step['tui']
                    y = 5
                    for paragraph in desc.split('\n'):
                        for line in textwrap.wrap(paragraph, w - 40) or ['']:
                            put(y, 37, line)
                            y += 1
                    put(h - 4, 2, 'Destino: ' + str(self.target))
                put(h - 2, 2, '↑↓ selecionar · Enter executar etapa · A instalar sequência · C verificar · Q sair')
                screen.refresh()
                key = screen.getch()
                if key in (ord('q'), ord('Q'), 27):
                    return
                if key == curses.KEY_UP:
                    current = (current - 1) % len(STEPS)
                elif key == curses.KEY_DOWN:
                    current = (current + 1) % len(STEPS)
                elif key in (10, 13, ord('a'), ord('A'), ord('c'), ord('C')):
                    curses.def_prog_mode()
                    curses.endwin()
                    try:
                        if key in (ord('a'), ord('A')):
                            self.install()
                        elif key in (ord('c'), ord('C')):
                            self.check()
                        else:
                            self.step(STEPS[current]['id'])
                    except (InstallError, KeyboardInterrupt) as exc:
                        print('\nInterrompido: ' + str(exc))
                    input('\nEnter para voltar ao roteiro…')
                    curses.reset_prog_mode()
                    screen.clear()
        curses.wrapper(draw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='diagnóstico sem provisionar ou gravar relatório')
    group.add_argument('--plan', action='store_true', help='mostrar sequência sem rede ou alterações')
    group.add_argument('--install', action='store_true', help='executar sequência até o menu')
    group.add_argument('--step', choices=[s['id'] for s in STEPS], help='executar apenas uma etapa')
    group.add_argument('--verify-native', action='store_true', help='testar SQLite/PTY no Electron sem abrir o app')
    parser.add_argument('--target', default='/data/lionclaw', help='pasta exclusiva da aplicação (padrão: /data/lionclaw)')
    parser.add_argument('--yes', action='store_true', help='confirmar instalação; não aceita login nem abertura automaticamente')
    args = parser.parse_args(argv)
    try:
        installer = Installer(args.target, args.yes)
        if args.plan:
            installer.show_plan()
        elif args.check:
            return installer.check()
        elif args.verify_native:
            installer.verify_source()
            installer.native_check()
        elif args.install:
            installer.install()
        elif args.step:
            installer.step(args.step)
        else:
            installer.tui()
        return 0
    except (InstallError, OSError, ValueError, KeyError) as exc:
        print('\nERRO: ' + str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nInterrompido. Nenhuma etapa seguinte foi executada.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    sys.exit(main())
