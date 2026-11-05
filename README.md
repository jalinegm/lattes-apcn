# Skill "lattes-apcn": onde cadastrar no Lattes

Ajuda com o Currículo Lattes para APCN nas áreas de **Ensino** e **Ciências Ambientais**. Serve a qualquer docente dessas áreas. Ao acionar a skill, você escolhe entre três opções:

1. **Enviar um material para análise:** em qual menu do Lattes lançar uma produção, atividade ou ideia (cartilha, curso, parecer, evento, projeto, disciplina, orientação, banca etc.), como a Capes enxerga o item e o que falta para ele contar.
2. **Criar o XML para importação no Lattes:** você envia o currículo e o que falta lançar, mesmo uma pasta inteira de comprovantes; a skill separa o que já está lá, monta um plano e, com a sua aprovação, gera o arquivo.
3. **Analisar o currículo:** o quanto ele é aderente à área e o que deveria ser corrigido. Servidor federal também pode enviar o **Assentamento Funcional Digital** (SouGov.br > Serviços Disponíveis > Todos os Serviços > Assentamento Funcional Digital > caixinha "Selecionar todos para baixar", que gera um único `.zip`): a skill aproveita só portarias, progressões e promoções para o vínculo. Se as progressões não aparecerem no arquivo, procure a Gestão de Pessoas do seu campus. Essa leitura usa o pacote `pypdf`.

As opções 2 e 3 usam o XML do Lattes e precisam de **Python** no computador, salvo no Claude.ai, que já o traz.

Baseada nas Oficinas Lattes da Profa. Priscila Tavares (Ciências Ambientais, 15 out 2026; Ensino/Área 46, 26 out 2026).

**Já tem a skill?** Veja [como atualizar](COMO-ATUALIZAR.md). No Windows, são dois cliques em um arquivo.

Para instalar pela primeira vez, baixe os arquivos da [última versão](https://github.com/jalinegm/lattes-apcn/releases/latest) e escolha o seu caso:

- [A. Uso o **Claude Code** ou o **Codex**](#a-claude-code-ou-codex-instalador-automático) (instalador de dois cliques)
- [B. Uso o **Claude.ai** (site ou app)](#b-claudeai-site-ou-app)
- [C. Instalar **manualmente** (copiando a pasta)](#c-instalação-manual)

---

## A. Claude Code ou Codex: instalador automático

O mesmo instalador serve para os dois. Ele copia a skill para as pastas que cada programa lê.

### Windows

1. Baixe o arquivo `lattes-apcn-instalador.zip`.
2. Clique com o botão direito no ZIP e escolha **Extrair tudo...** e depois **Extrair**.
   Importante: extraia a pasta inteira. Não execute de dentro do ZIP.
3. Abra a pasta extraída e dê **dois cliques** em `INSTALAR-Windows.bat`.
4. Se o Windows mostrar "O Windows protegeu o computador", clique em **Mais informações** e depois em **Executar assim mesmo**. O arquivo só copia pastas; você pode abri-lo no Bloco de Notas para conferir.
5. Aparecerão duas linhas com `OK:` e a conferência do Python. Se perguntar sobre instalar o Python, digite **S**. Aperte qualquer tecla para fechar.
6. **Feche e abra de novo** o Claude Code ou o Codex.

### Mac ou Linux

1. Baixe e extraia `lattes-apcn-instalador.zip`.
2. Abra o Terminal na pasta extraída e rode:
   ```
   sh instalar-mac-linux.sh
   ```
3. Feche e abra de novo o Claude Code ou o Codex.

### Para atualizar

Siga [COMO-ATUALIZAR.md](COMO-ATUALIZAR.md).

### Como conferir que funcionou

- **Claude Code:** digite `/skills` e procure `lattes-apcn`. Ou apenas pergunte: "Onde cadastro uma cartilha no Lattes?".
- **Codex:** digite `/skills` (CLI ou extensão do IDE) e procure `lattes-apcn`. Também dá para chamar diretamente com `$lattes-apcn`.

---

## B. Claude.ai (site ou app)

Use o arquivo `lattes-apcn.zip` (**não** extraia).

1. Entre em claude.ai.
2. Abra **Configurações** (seu nome, canto inferior esquerdo) e vá em **Capacidades** (em algumas contas aparece como **Personalizar**) > **Skills**.
3. Clique em **Enviar skill** (ou **Carregar skill**) e escolha `lattes-apcn.zip`.
4. Deixe a skill **ativada**.
5. Abra uma conversa nova e anexe seu material.

Observações: o envio de skills exige plano pago (Pro, Max, Team ou Enterprise) e o nome exato dos menus pode mudar. Se não encontrar, busque "Skills" nas configurações. A skill instalada no Claude.ai fica só na sua conta.

---

## C. Instalação manual

Use se o instalador não rodar (computador institucional bloqueado, por exemplo).

1. Extraia o ZIP e localize a pasta `lattes-apcn` (a que contém o arquivo `SKILL.md`).
2. Copie a pasta inteira para:

| Programa | Onde colar |
|---|---|
| Claude Code | `C:\Users\SEU_USUARIO\.claude\skills\` (Mac/Linux: `~/.claude/skills/`) |
| Codex | `C:\Users\SEU_USUARIO\.agents\skills\` (Mac/Linux: `~/.agents/skills/`) |

3. Se a pasta `skills` não existir, crie. A pasta `.claude` ou `.agents` começa com ponto e pode estar oculta (Windows: Exibir > Mostrar > Itens ocultos).
4. O resultado deve ser `...\skills\lattes-apcn\SKILL.md`. Se ficar `...\skills\lattes-apcn\lattes-apcn\SKILL.md`, mova a pasta de dentro um nível acima.
5. Reinicie o Claude Code ou o Codex.

---

## Como usar

Acione a skill e escolha uma opção no menu, ou diga direto o que quer. Para a opção 1, anexe o material (PDF, DOCX, imagem), cole o link ou descreva a ideia:

- "Onde cadastro essa cartilha no meu Lattes?" (com o PDF anexado)
- "Quero dar uma oficina de 6 h para a Secretaria de Meio Ambiente. Como planejo e cadastro?"
- "Sou responsável pela disciplina X e dou um módulo avulso em outro curso. Onde lanço?"
- "Oriento três alunos de IC e participo de bancas. Como registro?"
- "Coordeno um curso FIC e produzi uma cartilha. O que vai para repositório?"
- "Classifique esta lista de produções no Lattes" (cole a lista)
- "Gere o XML para importar no Lattes com o que está nesta pasta" (com o ZIP do currículo)
- "Meu currículo serve para a APCN de Ensino? O que corrijo?" (com o ZIP do currículo)

O XML do Lattes traz CPF, documentos e endereço. A skill lê o arquivo por um script que descarta esses dados, mas o arquivo fica no ambiente em que você a usa. Antes de importar, guarde o ZIP original como cópia de segurança e importe primeiro o arquivo de teste, com um item só.

Se o material puder ir para mais de um menu, a skill faz perguntas antes de recomendar. Cada regra vem marcada como **[Oficina]** (15 out), **[Oficina 26 out]** (Ensino/Área 46), **[Doc. Ensino]** ou **[Inferido]** (confirme com a especialista, a PROPPG ou na tela do Lattes).

No Codex, se a skill não for escolhida sozinha, comece a mensagem com `$lattes-apcn`.

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| A skill não aparece na lista | Feche e abra o programa de novo. Confira que existe `skills\lattes-apcn\SKILL.md` |
| `ERRO: pasta lattes-apcn nao encontrada` | Você executou de dentro do ZIP. Extraia tudo antes |
| Windows bloqueou o `.bat` | Mais informações > Executar assim mesmo, ou use a instalação manual (C) |
| Claude.ai não aceita o ZIP | Use `lattes-apcn.zip`, não o `...-instalador.zip`, e não extraia |

## Limites

Área de concentração e linhas de cada APCN vêm dos rascunhos de nov 2026 e podem mudar. Não acessa nem edita seu Lattes: orienta e prepara arquivos, e quem importa e salva é você. **A importação do XML ainda não foi confirmada por nós no Lattes:** o arquivo segue a DTD do CNPq, mas só o Lattes confirma o aceite. Importar acrescenta itens e não corrige os existentes. Produtos técnicos, atuação, projetos e formação não têm relato público de importação. Nomes de menus do Lattes mudam; confira na tela. A lista de produções técnicas de **Ciências Ambientais** vem da oficina e do Documento de Área 49 (16 tipologias); a de **Ensino** vem do Documento de APCN 2026 da Área 46 (9 tipos de produto educacional, regras de destaque) e da oficina de 26 out (que também cita relatório técnico e prioriza produtos/processos educacionais). A oficina de 26 out informa T1-T3 e pesos 25/25/50 no Quesito 3, mas há ambiguidades entre slide e transcrição; elas estão marcadas em `references/ensino.md` seção 13.
