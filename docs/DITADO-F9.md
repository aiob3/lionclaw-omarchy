# Ditado F9: números e símbolos no Electron via XWayland

> **Legado desde a 1.1.2.** O LionClaw agora abre nativo no Wayland e recebe a digitação do Voxtype sem ajuste. Este documento fica como diagnóstico e para a [reversão](#reversão-manual) de quem aplicou a 1.1.0/1.1.1.

## Diagnóstico observado em 19/09/2026

O F9 do Omarchy acionava o Voxtype corretamente. O reconhecimento Whisper
produzia português legível no journal, mas o texto chegava ao campo do
LionClaw como números e sinais. A janela LionClaw usava **XWayland**, com
**Electron 33.4.11**; o Voxtype **1.0.1** estava em `output.mode = "type"`.

O defeito foi reproduzido em uma janela isolada com o mesmo binário Electron:

| Entrega do mesmo texto sintético | Resultado |
|---|---|
| `wtype` caractere por caractere | `12345678906-q470w85e7` — falhou |
| Clipboard + Ctrl+V via `wtype` | Campo vazio — falhou |
| Clipboard + Shift+Insert via `wtype` | Campo vazio — falhou |
| Clipboard + Ctrl+V nativo do Hyprland | Frase idêntica, com acentos — passou |
| Clipboard + Shift+Insert nativo do Hyprland | Frase idêntica, com acentos — passou |

Frase de referência: **Olá, transcrição com acentuação: 123 + 45.**
Resultados capturados do campo de texto estão em
[evidence/dictation-20260919.json](../evidence/dictation-20260919.json).

A falha foi localizada na entrega de teclas virtuais do `wtype` ao
Electron/XWayland. O reconhecimento já estava correto. O teste não estabelece
qual componente upstream contém a causa interna definitiva. Não foi necessário
mudar o código privado do LionClaw, o modelo Whisper, idioma, microfone ou GPU.

## Correção incorporada ao instalador

Desde a versão 1.1.1, a instalação nova pela tecla **A** da TUI ou `--install`
já executa **Compatibilidade F9** após registrar o menu. Para começar:

```bash
git clone https://github.com/aiob3/lionclaw-omarchy.git
cd lionclaw-omarchy
./install.sh
```

Para repetir somente a etapa de ditado, executar:

```bash
./install.sh --step dictation --target /data/lionclaw
```

Pré-requisitos: Voxtype já configurado e ativo, Python 3.11+, `wl-copy` e uma
sessão Hyprland 0.56 acessível. O instalador não instala modelos de voz. O F9
continua sendo o atalho fornecido pelo Omarchy. A sequência `--install` inclui
a compatibilidade F9, e `--check` inclui sua situação sem modificar arquivos.
Se Voxtype estiver ausente, a etapa registra **NOT_APPLICABLE**: LionClaw pode
ser usado sem voz. Para habilitar o ditado depois, configurar Voxtype pelo
Omarchy e repetir `--step dictation`. Ausência não é aprovação de teste F9.

O ajuste é global para o Voxtype, com caminhos derivados de `XDG_CONFIG_HOME`:

```toml
[output]
mode = "clipboard"
post_output_command = "/usr/bin/python3 /caminho/do/usuario/.config/voxtype/paste-hyprland.py"
auto_submit = false
```

O instalador gera e escapa o caminho real; não copie literalmente o exemplo.
O helper consulta a janela ativa e envia eventos `hl.dsp.send_key_state` de
pressionamento e liberação separados por 50 ms. Usa Ctrl+V para aplicativos
e Shift+Insert para janelas com a tag `terminal`. Ambos os eventos têm o mesmo
endereço de destino. Não envia Enter. A liberação ocorre também diante de erro.

**A última transcrição fica na área de transferência.** Aplicativos que
interceptam colagem podem se comportar de forma diferente; testar os campos
efetivamente usados. Não se trata de uma homologação de todos os aplicativos.

Antes de escrever, a etapa exige serviço ocioso, valida o TOML e recusa hooks
personalizados, `smart_auto_submit` ativo e destinos por symlink. Faz backup,
preserva configurações não relacionadas e reinicia apenas o Voxtype. Se falhar,
tenta restaurar a configuração e o helper anteriores e reiniciar novamente.
A repetição com conteúdo idêntico verifica sem reescrever ou reiniciar.

## Reversão manual

O terminal informa o diretório de backup privado, sob
`${XDG_STATE_HOME:-~/.local/state}/lionclaw-installer/`. Nele, `config.toml.before`
é o TOML anterior. Se o helper já existia, `paste-hyprland.py.before` preserva
seu conteúdo anterior. Com o Voxtype ocioso, restaure esses arquivos nos caminhos
indicados e execute `systemctl --user restart voxtype`. Se o helper foi criado
pela etapa, sua remoção após restaurar o TOML é opcional. Não descarte backups.

## Evidência e limite de homologação

- Teste real: corrupção reproduzida e duas combinações de colagem nativa
  aprovadas na janela isolada Electron/XWayland. O helper empacotado também
  foi executado nessa janela, preservando a frase (`pass: true`).
- Na estação, `systemctl --user is-active voxtype` retornou `active`,
  `voxtype status` retornou `idle` e o journal registrou `Output mode: Clipboard`.
  Ditados posteriores registraram `post_output hook completed successfully`.
- O log comprova execução do hook; não comprova o texto visualmente exibido no
  LionClaw. Confirmação visual de F9 no LionClaw e no terminal: **NÃO VERIFICADO**
  neste registro. VM Omarchy limpa: **NÃO EXECUTADO**.
- Para fechar a interação, ditar uma frase com acentos no LionClaw, observar
  antes de enviar e repetir em um editor dentro do terminal. Exigir texto
  correto, inserção única e ausência de envio automático. Registrar captura
  sem conversas pessoais conforme [VM-LIMPA.md](VM-LIMPA.md), quando aplicável.

## Referências técnicas

- [Voxtype: configuração de saída](https://github.com/peteonrails/voxtype/blob/dev/docs/CONFIGURATION.md).
- [Relato e proposta no Omarchy](https://github.com/omacom/omarchy/discussions/7028).
- [Hyprland: dispatchers Lua](https://wiki.hypr.land/Configuring/Basics/Dispatchers/).

O helper adapta o mecanismo instalado de colagem universal em
`/usr/share/omarchy/default/hypr/bindings/clipboard.lua`. Esse arquivo do sistema
foi somente lido; a correção fica na configuração do usuário.
