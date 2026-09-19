#!/usr/bin/env bash
# Bootstrap mínimo. Leia antes de executar; não use curl | bash.
set -euo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$ROOT_DIR/installer.py" "$@"
fi
case " ${*:-} " in
  *" --check "*|*" --plan "*|*" --help "*|*" -h "*)
    printf '%s\n' 'Python 3 ausente. O bootstrap pode provisionar python pelo pacman via pkexec.' 'Execute ./install.sh em um terminal para confirmar. Nenhuma alteração foi feita.'
    exit 2 ;;
esac
if [[ $EUID -eq 0 ]]; then
  printf '%s\n' 'Execute como usuário comum, não como root.' >&2
  exit 2
fi
if ! /usr/bin/grep -Eq '^ID=("omarchy"|omarchy)$' /etc/os-release; then
  printf '%s\n' 'Provisionamento suportado somente no Omarchy.' >&2
  exit 2
fi
if [[ ! -x /usr/bin/pacman || ! -x /usr/bin/pkexec || ! -t 0 ]]; then
  printf '%s\n' 'Requer terminal interativo, pacman e pkexec. Python não foi instalado.' >&2
  exit 2
fi
printf '%s\n' 'Python 3 não está instalado.' 'Comando: pkexec /usr/bin/pacman -S --needed python'
read -r -p 'Provisionar Python para iniciar o instalador? [s/N] ' answer
[[ "$answer" == [sS] ]] || exit 2
/usr/bin/pkexec /usr/bin/pacman -S --needed python
command -v python3 >/dev/null
exec python3 "$ROOT_DIR/installer.py" "$@"
