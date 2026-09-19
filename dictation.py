"""Edição conservadora do TOML do Voxtype, sem dependências externas."""
import json
import re
import shlex
import tomllib


def hook_command(helper):
    return shlex.join(['/usr/bin/python3', str(helper)])


def configure(text, helper):
    parsed = tomllib.loads(text)
    output = parsed.get('output', {})
    command = hook_command(helper)
    if output.get('post_output_command') not in (None, '', command):
        raise ValueError('post_output_command personalizado: preserve e integre manualmente.')
    if output.get('pre_output_command'):
        raise ValueError('pre_output_command personalizado: preserve e integre manualmente.')
    if parsed.get('text', {}).get('smart_auto_submit', False):
        raise ValueError('smart_auto_submit ativo: desative conscientemente antes de configurar o ditado.')
    # Não serializa o documento inteiro: mantém comentários, modelo e microfone.
    lines = text.splitlines(keepends=True)
    headers = [i for i, line in enumerate(lines) if re.match(r'^\s*\[output\]\s*(?:#.*)?$', line)]
    if len(headers) != 1:
        raise ValueError('Requer uma seção [output] explícita; TOML original preservado.')
    start = headers[0] + 1
    end = next((i for i in range(start, len(lines)) if re.match(r'^\s*\[', lines[i])), len(lines))
    values = {'mode': 'clipboard', 'post_output_command': command, 'auto_submit': False}
    section = lines[start:end]
    for key, value in values.items():
        positions = [i for i, line in enumerate(section) if re.match(r'^\s*' + key + r'\s*=', line)]
        replacement = key + ' = ' + json.dumps(value, ensure_ascii=False) + '\n'
        if positions:
            section[positions[0]] = replacement
        else:
            if section and not section[-1].endswith('\n'):
                section[-1] += '\n'
            section.append(replacement)
    candidate = ''.join(lines[:start] + section + lines[end:])
    expected = dict(parsed)
    expected['output'] = {**output, **values}
    if tomllib.loads(candidate) != expected:
        raise ValueError('Formato TOML não suportado para edição segura; original preservado.')
    return candidate
