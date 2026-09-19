# Histórico de versões

## 1.1.0 — 19/09/2026

A primeira atualização do instalador comunitário corrige o ditado F9 que chegava ao Electron/XWayland como números e símbolos. A fala já era reconhecida corretamente; a falha ocorria na entrega por teclado virtual. A nova etapa usa a área de transferência e a colagem nativa do Hyprland.

## Como atualizar uma instalação existente

Na pasta do **instalador público** `lionclaw-omarchy`:

```bash
git pull --ff-only
./install.sh --step dictation --target /data/lionclaw
```

Substitua o destino se instalou o aplicativo em outro local. Quem baixou ZIP pode baixar o código desta versão, extrair em uma nova pasta e executar a mesma etapa. Não é necessário repetir npm ci, rebuild ou reinstalar o LionClaw para aplicar este ajuste.

Na TUI, a opção é **11 — Ditado F9 (opcional)**. A etapa faz backup, preserva modelo/idioma/microfone, exige Voxtype ocioso e tenta restaurar a configuração anterior em caso de falha. Hooks personalizados são preservados e exigem integração manual. A última transcrição permanece na área de transferência; o envio automático fica desativado.

## Validação

- 36 testes automatizados aprovados: 23 anteriores e 13 da correção.
- Bug reproduzido no Electron 33.4.11 via XWayland; o helper empacotado preservou a frase inteira, com acentos, na janela isolada.
- Nova etapa da TUI exercitada por teclado; guia atualizado para 13 etapas.
- Requer Voxtype configurado, wl-copy, Python 3.11+ e Hyprland 0.56. A revisão do LionClaw e as versões Node/Electron permanecem fixadas.

Após aplicar, dite uma frase no LionClaw com F9 e confira antes de enviar. A prova automatizada em janela isolada não substitui a confirmação visual no aplicativo nem representa homologação de uma VM Omarchy limpa.

[Abrir instruções da correção](https://aiob3.github.io/lionclaw-omarchy/#dictation) · [Diagnóstico e reversão](https://github.com/aiob3/lionclaw-omarchy/blob/v1.1.0/docs/DITADO-F9.md) · [Evidências do teste](https://github.com/aiob3/lionclaw-omarchy/blob/v1.1.0/evidence/dictation-20260919.json)

## 1.0.0 — 19/09/2026

Primeira publicação do guia e instalador TUI para a revisão fixada do LionClaw no Omarchy, com validação local de instalação, módulos nativos e abertura.
