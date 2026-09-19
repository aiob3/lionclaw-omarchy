# Registro de validação comunitária

Data: **19 de setembro de 2026**. Escopo: instalar e iniciar **LionClaw 3.8.0** em uma estação **Omarchy x86_64** já utilizada. Este registro não é certificação oficial do LionLabs ou Omarchy.

## Conjunto fixado

| Item | Valor observado |
|---|---|
| Revisão oficial | `051da4bdff2c44b43bd78a3166aa9374d1dba3b9` |
| Omarchy | `4.0.0.r2158.gd174d4a` (pacote `omarchy-dev`) |
| Arquitetura | x86_64 |
| Node das ferramentas | 24.11.1, via mise |
| npm observado | 11.6.2 |
| Electron do projeto | 33.4.11 |
| Node interno do Electron | 20.18.3 |
| ABI do Electron | 130 |
| better-sqlite3 do lockfile | 12.6.2 |
| SQLite no teste | 3.51.2 |
| electron-rebuild | 4.0.3 |
| Interface gráfica | Hyprland, execução do app por XWayland |

Hashes de package.json e package-lock.json estão em [manifest.json](manifest.json). Eles foram comparados antes e depois da instalação. Não houve alteração dos arquivos versionados do repositório oficial.

## Problema reproduzido nos registros locais

1. `npm install` usou Node **26.9.0**.
2. O pacote `better-sqlite3@12.6.2` não encontrou binário pré-compilado para esse alvo e tentou compilar.
3. A compilação falhou com `PropertyCallbackInfo<v8::Value> has no member named This`; npm retornou **1**.
4. A tentativa seguinte de `npm run rebuild:electron` retornou **127**. A ferramenta local não estava disponível após a instalação incompleta.

Diagnóstico: incompatibilidade do módulo nativo com o Node usado na instalação; a falta posterior de electron-rebuild era consequência. Instalar outro Electron no sistema não resolveria essa cadeia.

## Procedimento executado e resultados

| Comando / prova | Resultado |
|---|---|
| `mise exec node@24.11.1 -- npm ci --no-audit --no-fund` | Exit 0; 1.383 pacotes; MCP Build: 27 ok, 0 failed, 1 skipped |
| `mise exec node@24.11.1 -- npm run rebuild:electron` | Exit 0; `✔ Rebuild Complete` |
| SQLite em memória no runtime Electron | consulta executada; SQLite 3.51.2 |
| PTY no runtime Electron | `PTY_OK`; exit 0 |
| `mise exec node@24.11.1 -- npm run build` | Exit 0; main, preload e renderer presentes |
| Execução com `ELECTRON_OZONE_PLATFORM_HINT=wayland` | processos e log ready; janela não observada no compositor |
| Execução com `ELECTRON_OZONE_PLATFORM_HINT=x11` | janela `lionclaw` mapeada; `xwayland: true` |
| `desktop-file-validate` e `gtk-launch lionclaw` | exit 0; entrada descoberta pelo cadastro desktop |

A janela observada diretamente foi a execução de desenvolvimento por XWayland. O build de produção e o comando do atalho foram validados; o lançamento do atalho ocorreu com uma instância já aberta. Esse teste não prova, isoladamente, um primeiro boot visual de produção. O instalador registra essa distinção em vez de inferir renderização a partir do build.

## Testes do instalador público

### Execução real na estação

- `install.sh --check --target <checkout-existente>`: **exit 0**, seis verificações OK (ambiente, pacotes, acesso, Node, revisão e build).
- `install.sh --verify-native --target <checkout-existente>`: **exit 0** e saída:

```json
{"electron":"33.4.11","node":"v20.18.3","abi":"130","sqlite":"OK","keytar_load":"OK","pty":"PTY_OK"}
```

- Etapa `menu` executada duas vezes com XDG_DATA_HOME e XDG_STATE_HOME temporários: primeira criação validada; segunda retornou `Já atualizado`. Caminho de teste continha espaços. O atalho pessoal existente não foi substituído por esse ensaio.
- `desktop-file-validate` aprovou também candidato com espaços, `$`, `%`, aspas e crases no caminho; `bash -n` aprovou o launcher.
- TUI exercitada em pseudo-terminal de 120 × 32: renderização de duas colunas, seta para próxima etapa e saída por Q com **exit 0**. Nenhum pacote do sistema foi removido para simular ausência.
- Sintaxe Python, Bash e JavaScript validada.

### Ensaio completo do novo instalador

`install.sh --install --yes --target <pasta-nova-de-ensaio>`, com diretórios XDG temporários, terminou com **exit 0**. O clone foi obtido novamente do GitHub com a conta autorizada. O menu pessoal existente e a instalação já usada pelo operador foram preservados; a aplicação de ensaio não foi aberta automaticamente.

O relatório registrou **34 comandos** e **9 etapas PASSED**: environment, packages, access, node, source, dependencies, rebuild, build e menu. A revisão e os hashes conferiram no novo clone; npm ci, rebuild e build terminaram com sucesso. A prova de SQLite/PTY/keytar foi repetida no novo destino. Veja o resumo sem caminhos pessoais em [evidence/validation.json](evidence/validation.json).

### Cenários simulados, sem confundir com máquina limpa

`python3 -m unittest discover -s tests -v` executa **23 testes**. Eles cobrem pacotes faltantes e reprova após provisionamento incompleto; ferramentas de origem alternativa; acesso negado antes do clone; falta de login sem iniciar autenticação em diagnóstico; Node divergente; revisão alterada; dirty checkout; hash incorreto; rebuild ausente; interrupção na primeira falha; códigos de saída registrados; backups/idempotência; symlink recusado; caminhos com metacaracteres; bootstrap sem Python; sequência compartilhada e plano sem rede.

O provisionamento de requisitos ausentes foi testado por simulação de comandos. **Não foi executada uma instalação do zero em uma VM Omarchy limpa**. O ensaio integral acima usou uma pasta nova nesta estação, cujas ferramentas e bibliotecas já estavam presentes. Contribuições com ensaios em máquinas limpas devem registrar versão, revisão, comandos e saídas sem expor segredos.

## Guia visual

Navegador real (Chrome conectado): navegação desktop, duas colunas, seleção de etapa, marcação manual, cópia de comando confirmada no clipboard e versão móvel com menu Etapas. Viewports de QA: 1536 × 1046 e 390 × 844. O acompanhamento usa armazenamento local e não atesta o sistema do visitante.

## Limites de homologação

- Login, keychain completo, provedores, cobrança, assinaturas, ferramentas de agentes, pipelines e todos os MCPs em uso real: **não homologados**.
- ARM, outras distros, outras revisões, GPUs e sessões Wayland nativas: **não homologados**.
- Pacotes npm possuem suas próprias condições de manutenção. A revisão fixada não significa atualização de segurança automática nem auditoria integral de dependências.
- O primeiro início do app pode criar perfil, migrar dados, sincronizar MCPs no Codex e baixar dependências do LionDesign. O instalador informa isso e não abre o aplicativo automaticamente.
- Relatórios, logs e backups originais são locais. Nenhum código privado, credencial ou conteúdo pessoal foi necessário para compor este registro público.

## Critério para uma próxima revisão

Se for realizado um ensaio em VM limpa, seguir obrigatoriamente o [protocolo de capturas por etapa](docs/VM-LIMPA.md). Ele exige imagens reais numeradas, inclusive da aplicação funcionando, primeira abertura pelo menu, interface, terminal integrado e reabertura, com resultados e SHA-256. Esse ensaio permanece **NÃO EXECUTADO**.

Atualizar explicitamente manifest.json, rever requisitos e efeitos de primeiro boot, passar testes do instalador, instalar a revisão em ambiente de ensaio, validar módulos, build, menu e janela. Registrar separadamente os recursos funcionais exercitados. Publicar nova versão do instalador somente com evidência correspondente.

## Adendo: correção do ditado F9 (versão 1.1.0)

O diagnóstico, a mudança de configuração e seus limites estão em
[docs/DITADO-F9.md](docs/DITADO-F9.md). A entrega de texto via `wtype` foi
reproduzida como números no Electron 33.4.11/XWayland; a colagem nativa
do Hyprland preservou a frase e os acentos. O helper empacotado também foi
executado na janela isolada com resultado exato: `pass: true`.

Comando `python3 -m unittest discover -s tests -v`: **36 testes / 36 aprovados**,
exit 0 (23 anteriores + 13 do ditado). As novas provas cobrem preservação do
TOML, backup, repetição, recusa de gravação ativa e hooks personalizados,
rollback, caminhos com metacaracteres, diagnóstico sem escrita, opcionalidade,
symlinks e eventos de pressionamento/liberação para aplicativos e terminais.
Sintaxe Python/Bash/JavaScript e `--plan`: exit 0. TUI exercitada em
pseudo-terminal 80 × 24: seleção da etapa 11 por setas e saída Q com exit 0.
Resultados sem dados pessoais
em [evidence/dictation-20260919.json](evidence/dictation-20260919.json).

O guia e a TUI passam a compartilhar 13 etapas; ditado é opcional e fica fora
da sequência obrigatória de instalação. Serviço e configuração aprovados não
equivalem a texto visualmente conferido no LionClaw. F9 no aplicativo real e
no terminal: **NÃO VERIFICADO** neste registro. VM limpa: **NÃO EXECUTADO**.
As evidências da versão anterior acima descrevem aquela rodada e não são
ampliadas por este adendo. A versão 1.1.0 distribui a correção e seu procedimento
de verificação; consulte também as notas da release pública.

## Adendo: primeira instalação com compatibilidade F9 (1.1.1)

A sequência atual tem 10 etapas de execução, incluindo `dictation` depois
de `menu`. O catálogo do guia/TUI mantém 13 etapas, contando orientação,
primeiro início e diagnóstico. A correção é oferecida durante a primeira
instalação quando Voxtype estiver presente; ausência é `NOT_APPLICABLE`,
com orientação para habilitar voz e repetir a etapa depois. O aplicativo
continua não sendo aberto automaticamente.

`python3 -m unittest discover -s tests -q`: **38 testes, OK, exit 0**.
Os testes de fluxo verificam que a instalação chama `dictation`, aplica o
ajuste com Voxtype presente e registra não aplicabilidade sem escrever a
configuração quando ele está ausente. São cenários simulados, não instalação
em VM limpa. A prova real anterior do helper continua limitada à janela
isolada Electron/XWayland; este adendo não amplia sua homologação visual.
