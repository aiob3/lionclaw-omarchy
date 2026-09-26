# Histórico de versões

## 1.1.2 — 26/09/2026

**LionClaw 3.9.0 nativo no Wayland.** O atalho do menu e o primeiro início abrem o LionClaw com `ELECTRON_OZONE_PLATFORM_HINT=wayland` e a chave oficial do app `LIONCLAW_ENABLE_HARDWARE_ACCELERATION=1`. Dois defeitos do XWayland somem juntos:

- **Ditado:** o Voxtype, no modo digitar de sempre, chega ao LionClaw como texto, e não mais como `121345672153819370-=1`.
- **Escala:** letras e textos no tamanho certo; o `GDK_SCALE=2` do Omarchy dobrava a interface.

**A instalação não altera mais o Voxtype.** A etapa Ditado F9, que trocava a digitação por colagem, saiu da sequência e do diagnóstico. Quem a aplicou na 1.1.0/1.1.1 pode voltar ao modo digitar pela [reversão manual](docs/DITADO-F9.md#reversão-manual) e atualizar o atalho:

```bash
git pull --ff-only
./install.sh --step menu --target /data/lionclaw
```

**LionClaw 3.9.0.** A revisão fixada passa a ser `b0907f7` (3.9.0), com Node 24.11.1 e Electron 33.4.11 inalterados.

**Validação:** 40 testes aprovados. Build de produção e atalho do menu executados pelo instalador; aberto pelo menu, o LionClaw rodou nativo no Wayland, com tamanho e ditado corretos confirmados pelo operador. Detalhes no [adendo da homologação](HOMOLOGACAO.md#adendo-lionclaw-nativo-no-wayland-112).

## 1.1.1 — 19/09/2026

O instalador publicado no lançamento de hoje já inclui a correção do ditado F9 no fluxo de **primeira instalação** do LionClaw no Omarchy.

## Instalar do zero

```bash
git clone https://github.com/aiob3/lionclaw-omarchy.git
cd lionclaw-omarchy
./install.sh
```

Na TUI, pressione **A** para executar a instalação guiada, incluindo requisitos, acesso ao repositório oficial, Node, dependências, rebuild, build, menu e **Compatibilidade F9**. Também é possível executar `./install.sh --install`.

A etapa F9 já faz parte da sequência: quando o Voxtype está configurado no Omarchy, o instalador aplica a colagem nativa do Hyprland com backup e confirmação. Assim, quem está começando não precisa instalar primeiro e procurar a correção separadamente. A última transcrição fica na área de transferência.

Se o Voxtype não estiver instalado, o relatório registra **NÃO APLICÁVEL**, sem bloquear o uso do LionClaw sem voz. Para habilitar voz depois, configure o Voxtype pelo Omarchy e execute `./install.sh --step dictation`. A etapa não baixa modelos de voz. Voxtype existente precisa estar configurado, ativo e ocioso; hooks personalizados são preservados.

**Validação:** 38 testes aprovados, incluindo presença da etapa no fluxo completo, aplicação com Voxtype e registro de não aplicabilidade sem ele. O helper já foi testado com texto acentuado em Electron 33.4.11/XWayland. Instalação integral em VM limpa e confirmação visual do F9 no LionClaw continuam separadas e não são alegadas por esses testes.

[Guia para começar](https://aiob3.github.io/lionclaw-omarchy/) · [Etapa Compatibilidade F9](https://aiob3.github.io/lionclaw-omarchy/#dictation) · [Diagnóstico técnico](https://github.com/aiob3/lionclaw-omarchy/blob/v1.1.1/docs/DITADO-F9.md)

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
