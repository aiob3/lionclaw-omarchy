# Guia e instalador LionClaw para Omarchy

## Pedido e contrato

Dois entregáveis independentes: guia público de duas colunas (roteiro e instruções práticas) e repositório público com instalador no terminal. Ambos usam a mesma sequência. Código, recursos, credenciais e histórico do repositório privado não são redistribuídos. Acesso GitHub ao upstream continua obrigatório.

## Comportamento

- Linux Omarchy x86_64; revisão oficial fixa, Node 24.11.1 e Electron 33.4.11.
- Verificar primeiro; instalar requisitos ausentes; confirmar operações; abortar na primeira falha; registrar comando, código e evidência local.
- Modo diagnóstico sem alterações e modo plano sem rede. Interface terminal com seleção por etapa e instalação sequencial.
- Privilégios somente por pkexec para pacman; npm/git/mise como usuário. Nunca instalar Electron global, executar npm como root, alterar Node global ou desabilitar sandbox.
- GitHub autenticado antes do clone; checkout exato em staging; recusar diretório incompatível ou trabalho alterado; validar hashes de package.json e lockfile.
- Menu aponta para build local, Node fixado e XWayland. Não iniciar automaticamente durante instalação. Primeiro início explica efeitos no perfil e faz backup de config do Codex se existente.
- Provas separadas: dependências, ABI nativa SQLite/PTY, build, registro desktop, abertura de janela, autenticação de provedores. Nenhuma implica a seguinte.
- Guia navegável por teclado, links diretos, cópia de comandos, progresso local explicitamente manual, responsivo e impressão integral.

## Aceitação

1. Cenários simulados: requisito ausente, acesso negado, checkout divergente, hash incorreto, falha de comando, caminho com espaços e metacaracteres, repetição e bootstrap sem Python.
2. Execução real de diagnóstico e validação de módulos na instalação existente, sem reinstalar ou alterar sessão do operador.
3. Teste de TUI em pseudo-terminal, sintaxe Bash/Python, conteúdo e links do site, desktop e viewport móvel no navegador real.
4. Repositório público e URL Pages acessíveis; CI pública sem acesso ao upstream privado.
5. Homologação declarada como validação local da revisão, não certificação oficial ou prova de instalação em Omarchy limpo.
