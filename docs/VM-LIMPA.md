# Protocolo obrigatório: ensaio em VM Omarchy limpa

**Estado: NÃO EXECUTADO.** Este documento define a evidência exigida para um ensaio futuro. Não é resultado de teste e não contém capturas simuladas.

Requisito do operador: se o ensaio em VM limpa for realizado, registrar as capturas de tela de todos os procedimentos aplicáveis e da aplicação funcionando depois deles. Log, processo ativo, exit 0 ou tela do instalador não substituem imagens do aplicativo.

## Preparação

1. Criar uma VM nova com Omarchy x86_64. Registrar imagem de origem e seu SHA-256, versão instalada, hipervisor, vCPU, memória, disco, resolução e modo gráfico.
2. Guardar um snapshot antes de provisionar requisitos. Registrar quais ferramentas já vieram com a imagem; não chamar a VM de limpa se reutilizar instalação anterior sem restauração do snapshot.
3. Baixar a versão publicada do instalador e registrar commit/tag, hashes, manifesto e revisão upstream fixada.
4. Autenticar uma conta própria autorizada ao repositório oficial. Não fotografar tokens, códigos de dispositivo, senhas, chaves ou telas que os exibam.
5. Reservar uma pasta de evidências fora do checkout público. Relatórios brutos ficam privados até revisão explícita para publicação.

## Capturas numeradas por procedimento

Faça a captura **depois de verificar o resultado**, usando a tela real da VM. Se houver falha, capture o erro e registre como falha; não reutilize uma imagem de outra rodada como aprovação.

| Arquivo sugerido | Procedimento e conteúdo mínimo |
|---|---|
| `01-ambiente.png` | Identificação Omarchy, arquitetura e usuário comum no terminal da VM |
| `02-requisitos-antes.png` | Lista de requisitos presentes e ausentes antes de provisionar |
| `03-requisitos-depois.png` | Resultado do provisionamento e nova verificação |
| `04-acesso-confirmado.png` | Conta autorizada consegue ler o repositório; sem dados de autenticação sensíveis |
| `05-node.png` | Node 24.11.1 efetivo; evidência de que os comandos usam a versão fixada |
| `06-revisao-hashes.png` | HEAD e comparação dos hashes esperados |
| `07-npm.png` | Final do npm ci e do postinstall sem falha |
| `08-rebuild.png` | Rebuild Complete e teste de SQLite/PTY/keytar |
| `09-build.png` | Final do build e presença dos artefatos |
| `10-menu.png` | Menu do Omarchy contendo LionClaw com nome e ícone |
| `11-primeira-janela.png` | Janela real do LionClaw aberta pelo menu, dentro do desktop da VM |
| `12-onboarding.png` | Fluxo inicial da aplicação sem credenciais expostas |
| `13-interface-principal.png` | Interface principal renderizada após concluir o onboarding autorizado |
| `14-terminal-funcionando.png` | Terminal integrado executando um comando inofensivo, por exemplo printf LIONCLAW_VM_OK |
| `15-reabertura.png` | Aplicação fechada e reaberta pelo menu, interface novamente renderizada |

Capture também cada erro intermediário e sua correção, por exemplo `08a-rebuild-falhou.png` e `08b-rebuild-corrigido.png`. Se outros procedimentos ou recursos forem exercitados, adicione imagens correspondentes e registre exatamente o que foi verificado.

Onboarding e recursos dependentes de credenciais exigem conta e permissões apropriadas. Não chamar o ensaio de completo se essas etapas não puderem ser executadas: registrar **NÃO VERIFICADO** e o motivo. Não executar chamadas pagas ou ações externas apenas para produzir uma imagem sem autorização correspondente.

## Registro de cada captura

Para cada arquivo, registrar em uma tabela ou JSON:

- identificador da rodada e da etapa;
- data/hora UTC;
- comando ou ação de UI que precedeu a captura;
- resultado esperado e observado;
- caminho do arquivo, resolução e SHA-256;
- estado: PASSOU, FALHOU ou NÃO VERIFICADO;
- versão do instalador, revisão LionClaw e snapshot de VM usados.

Exemplo de geração do manifesto de integridade, na pasta de evidências:

```bash
sha256sum -- *.png > SHA256SUMS
sha256sum --check SHA256SUMS
```

O hash comprova integridade do arquivo guardado, não o funcionamento do aplicativo por si só. Relacione cada imagem à execução e ao resultado. Preserve os originais; se precisar ocultar informações para publicação, produza uma cópia derivada identificada, com hash próprio e nota de redação.

## Critérios de fechamento

1. Todas as etapas aplicáveis têm comando/ação, saída e captura correspondente.
2. A primeira janela, a interface principal, o terminal integrado e a reabertura foram inspecionados visualmente.
3. Arquivos de imagem realmente existem, abrem e têm hashes conferidos. Um nome em uma lista não é uma captura.
4. Falhas, limitações e etapas não exercitadas são explícitas. A verificação é limitada ao conjunto efetivamente observado.
5. Atualizar HOMOLOGACAO.md e evidence/validation.json com o resultado real, sem substituir a evidência anterior. Acrescentar um índice navegável das capturas aprovadas para compartilhamento.
6. Publicar somente após conferir que as imagens e os logs não contêm credenciais, dados pessoais, mensagens privadas ou código oficial redistribuído indevidamente. Até essa conferência, manter o lote local.

Não marcar “VM limpa homologada” antes de cumprir esses critérios.
