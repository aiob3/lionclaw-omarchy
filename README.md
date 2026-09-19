# LionClaw no Omarchy

Guia Prático que inclui Interface TUI para acompanhamento e autorização durante o processo de implementação para reproduzir a instalação local validada do **LionClaw 3.8.0** no **Omarchy 4.0.4** homologado em Setembro de 2026.

**[Abrir guia passo a passo →](https://aiob3.github.io/lionclaw-omarchy/)**

## Não conhece o Omarchy?

O Omarchy é uma distribuição Linux criada por David H. Hansson **(DHH)** (o criador do framework Ruby on Rails). 
- Ele nasceu a partir do projeto **Omakub (que rodava sobre o Ubuntu)** , mas evoluiu para um sistema operacional próprio baseado em **Arch Linux**, utilizando o gerenciador de janelas em mosaico **Hyprland** e focado em uma interface moderna gerenciada por agentes de IA com baixo consumo de recursos locais proporcionando ótimo desempenho quando colocado sob condições de multiplas instância de IA rodando localmente pois foi criado sob esta mesma condição. Voltado para desenvolvedores de IA, Usuários Avançados e por padrão é voltado para amantes de uso de sistemas operacionais que dispensam o uso do Mouse, que preferem guiar-se por atalhos de teclado otimizados por linguagem `vim`. 

### ESTA ULTIMA OBSERVAÇÃO NÃO REFLETE A PREFERENCIA DO AUTHOR DESTA PUBLICAÇÃO, QUE PREFERE SIM O USO DE TECLADO E DE JANELAS DE INTERAÇÃO INTERATIVAS VISUAIS DURANTE O USO DO SISTEMA OPERACIONAL, CASO VOCE SE IDENTIFIQUE SOBRE ESTE MESMO PERFIL, ACESSE O MEU GUIA COMPLETO PARA COMPATIBILIZAR E OTIMIZAR O OMARCHY PARA QUE SEJA VISUALMENTE RESPONSIVEL INCLUINDO O USO DO SEU MOUSE, ALÉM DE TODOS AS FUNÇÕES ADICIONAIS QUE ELE PODE PROPORCIONAR
[ provisionando-aqui ]

O guia traz o roteiro à esquerda e instruções práticas à direita. A TUI usa o mesmo catálogo de etapas. Este projeto não é afiliado ao LionLabs ou ao Omarchy e não redistribui o aplicativo oficial, seus recursos ou credenciais.

## Acesso ao aplicativo

O código oficial está em [LionLabsCommunity/lionclawv1.0](https://github.com/LionLabsCommunity/lionclawv1.0), um repositório privado. Você precisa de sua própria conta autorizada. Uma instalação do `gh` ou um login bem-sucedido não substituem o convite ao repositório. Sem acesso, o instalador interrompe antes do clone.

## Começar

Leia os arquivos antes de executar. Não requer bibliotecas Python externas.

```bash
git clone https://github.com/aiob3/lionclaw-omarchy.git
cd lionclaw-omarchy
./install.sh --plan
./install.sh
```

Se Git estiver ausente, use **Code → Download ZIP** no GitHub, extraia e abra um terminal na pasta. O bootstrap detecta Python ausente e oferece provisioná-lo via `pkexec /usr/bin/pacman -S --needed python`. Em `--check`/`--plan`, não instala nada.

O destino padrão da aplicação é `/data/lionclaw`. A pasta pai deve existir e ser gravável pelo usuário. Alternativa:

```bash
mkdir -p "$HOME/Applications"
./install.sh --target "$HOME/Applications/lionclaw"
```

Na TUI: **↑↓** selecionam, **Enter** executa a etapa, **A** instala a sequência, **C** verifica requisitos, **Q** sai. Requer terminal de pelo menos 78 × 20; há CLI para terminais menores e automação.

## Modos

```bash
./install.sh --check                       # diagnóstico; sem provisionamento
./install.sh --plan                        # sequência; sem rede
./install.sh --install                     # instala até registrar o menu
./install.sh --step access                 # validar conta/acesso
./install.sh --step source                 # clone da revisão fixada
./install.sh --step dependencies           # npm ci + postinstall
./install.sh --step rebuild                # recompilar e testar módulos
./install.sh --verify-native               # SQLite/PTY; não abre o app
./install.sh --step first-run              # backup de config e abertura consentida
```

Passe `--target` em cada chamada se o destino não for o padrão. `--yes` confirma operações de instalação, mas não login nem abertura. O pacman mantém sua própria confirmação. Códigos: **0** sucesso, **1** falha de etapa, **2** diagnóstico com pendências, **130** interrompido.

## Sequência e provisionamento

| Etapa | Se ausente ou divergente | Prova |
|---|---|---|
| Omarchy x86_64 | Interrompe; não transforma outra distro em Omarchy | `/etc/os-release`, arquitetura, usuário comum |
| Ferramentas/bibliotecas | Instala somente faltantes com pacman/pkexec | comandos disponíveis, pacman e pkg-config |
| Conta GitHub | Oferece login oficial e verifica permissão | API do repositório responde à conta |
| Node 24.11.1 | `mise install`, sem mudar Node global | binário instalado retorna v24.11.1 |
| Código | Clone autenticado em staging e checkout fixo | HEAD e hashes de package.json/lockfile |
| Dependências | `npm ci` com Node fixado | exit 0, Electron e rebuild locais |
| Rebuild | `npm run rebuild:electron` | SQLite, PTY e carregamento keytar no Electron |
| Build | `npm run build` | main, preload, renderer e prova nativa |
| Menu | Launcher/desktop do usuário com backup | desktop-file-validate e cadastro atualizado |
| Primeiro início | Abertura separada com confirmação | janela visível; login fica com o usuário |

Electron vem do npm do projeto, não de pacman/yay. Ferramentas já presentes por mise ou pacotes alternativos são reaproveitadas. Se pacman falhar por bases/espelhos desatualizados, atualize o Omarchy pelo fluxo normal antes de repetir; não execute `pacman -Sy` isoladamente.

## Revisão validada e limites

[manifest.json](manifest.json) fixa a revisão `051da4bdff2c44b43bd78a3166aa9374d1dba3b9`, Node `24.11.1`, Electron `33.4.11` e hashes dos manifests privados. O instalador não segue automaticamente `main` e não oferece atualização automática de versões. Uma nova revisão exige nova validação.

[HOMOLOGACAO.md](HOMOLOGACAO.md) distingue a instalação local observada, os testes automatizados com cenários simulados e os limites ainda abertos. Não alegamos certificação oficial, instalação testada em Omarchy limpo, compatibilidade universal de hardware ou validação dos provedores.

Um futuro ensaio em VM limpa deverá seguir o [protocolo de capturas](docs/VM-LIMPA.md): imagens reais por etapa e da aplicação funcionando, resultados, índice e hashes. O ensaio em VM limpa ainda não foi executado.

## Dados, permissões e recuperação

- Git, npm, mise e app rodam como usuário. Somente pacman usa pkexec. Sem `sudo`, Electron global ou `--no-sandbox`.
- Checkout divergente ou alterado é recusado. Não há `reset --hard`, descarte de trabalho ou modificação do Node global.
- A instalação não abre o app. O primeiro início do upstream pode criar `~/.lionclaw`, migrar perfil, sincronizar MCPs no Codex e baixar componentes LionDesign. `--step first-run` faz backup do `config.toml` do Codex quando existente. Se já há perfil LionClaw, faça backup com o app fechado antes de abrir outra revisão.
- Relatórios e backups locais ficam em `${XDG_STATE_HOME:-~/.local/state}/lionclaw-installer/` com permissões privadas. Contêm comandos e códigos de saída; não são enviados a servidor algum. Não publique backups ou logs pessoais.
- A repetição de `--install` recria dependências e build. O menu preserva arquivo idêntico e faz backup antes de substituir conteúdo diferente. Para retomar, use `--step` depois de corrigir a causa.
- Para remover o atalho, remova apenas `applications/lionclaw.desktop` e `lionclaw-omarchy/launch.sh` sob `${XDG_DATA_HOME:-~/.local/share}`. Aplicação e perfil são independentes. Não há desinstalação destrutiva automática.

## Desenvolvimento e verificação

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh
python3 -m py_compile installer.py
python3 -m http.server 8765 --directory docs
```

A CI pública executa cenários simulados e consistência dos arquivos; ela não recebe credenciais nem clona o repositório privado. Problemas do instalador podem ser relatados em Issues sem incluir código upstream, segredos ou logs pessoais.

## Fontes

- [Electron: instalação](https://www.electronjs.org/docs/latest/tutorial/installation)
- [Electron: módulos nativos e rebuild](https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules)
- [mise install](https://mise.jdx.dev/cli/install.html)
- [GitHub CLI: autenticação](https://cli.github.com/manual/gh_auth_login)
- [Omarchy Manual](https://learn.omacom.io/2/the-omarchy-manual)

O código original deste instalador é MIT. As licenças e condições do LionClaw, Electron, Node e demais dependências são próprias; a licença deste repositório não se estende a eles.
