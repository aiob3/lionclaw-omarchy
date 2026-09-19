#!/usr/bin/env python3
"""Cola o resultado do Voxtype usando eventos nativos do Hyprland 0.56."""
import json
import re
import subprocess
import time


def hyprctl(*args):
    return subprocess.check_output(['/usr/bin/hyprctl', *args], text=True, timeout=5)


def main():
    window = json.loads(hyprctl('activewindow', '-j'))
    address = window.get('address', '')
    if not re.fullmatch(r'0x[0-9a-fA-F]+', address):
        raise SystemExit('Sem janela ativa; texto preservado na área de transferência.')
    terminal = any(tag.rstrip('*') == 'terminal' for tag in window.get('tags', []))
    mods, key = ('SHIFT', 'Insert') if terminal else ('CTRL', 'V')

    def send(state):
        hyprctl('dispatch', 'hl.dsp.send_key_state({ '
                f'mods = "{mods}", key = "{key}", state = "{state}", '
                f'window = "address:{address}"' + ' })')

    # Mantém destino fixo e libera a tecla mesmo se o pressionamento falhar.
    try:
        send('down')
        time.sleep(0.05)
    finally:
        send('up')


if __name__ == '__main__':
    main()
