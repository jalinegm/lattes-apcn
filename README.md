# Skill "lattes-apcn": onde cadastrar no Lattes

Ajuda você a descobrir **em qual menu do Lattes** lançar uma produção ou ideia (cartilha, curso, parecer, evento, projeto etc.), como a Capes enxerga o item e o que falta para ele contar na APCN. Baseada na Oficina Lattes da Profa. Priscila Tavares (15 out 2026).

**Baixando deste repositório:** clique em **Code > Download ZIP** (é preciso ter acesso ao repositório privado), extraia e siga o caso A. Onde o texto diz `lattes-apcn-instalador.zip`, use este ZIP. Para o Claude.ai (caso B), compacte a pasta `lattes-apcn` em um ZIP (a pasta com `SKILL.md` deve ficar na raiz do ZIP).

Escolha o seu caso:

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
5. Aparecerão três linhas com `OK:`. Aperte qualquer tecla para fechar.
6. **Feche e abra de novo** o Claude Code ou o Codex.

### Mac ou Linux

1. Baixe e extraia `lattes-apcn-instalador.zip`.
2. Abra o Terminal na pasta extraída e rode:
   ```
   sh instalar-mac-linux.sh
   ```
3. Feche e abra de novo o Claude Code ou o Codex.

### Para atualizar

Baixe a versão nova e rode o instalador de novo. Ele substitui a versão antiga.

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

Converse normalmente e anexe o material (PDF, DOCX, imagem), cole o link ou descreva a ideia:

- "Onde cadastro essa cartilha no meu Lattes?" (com o PDF anexado)
- "Quero dar uma oficina de 6 h para a Secretaria de Meio Ambiente. Como planejo e cadastro?"
- "Classifique esta lista de produções no Lattes" (cole a lista)

Se o material puder ir para mais de um menu, a skill faz perguntas antes de recomendar. Cada regra vem marcada como **[Oficina]** (dita pela especialista), **[Doc. CiAmb]** (Documento de Área 49, Ciências Ambientais), **[Doc. Ensino]** (Documento de APCN 2026 da Área 46, Ensino) ou **[Inferido]** (confirme com a especialista, a PROPPG ou na tela do Lattes).

No Codex, se a skill não for escolhida sozinha, comece a mensagem com `$lattes-apcn`.

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| A skill não aparece na lista | Feche e abra o programa de novo. Confira que existe `skills\lattes-apcn\SKILL.md` |
| `ERRO: pasta lattes-apcn nao encontrada` | Você executou de dentro do ZIP. Extraia tudo antes |
| Windows bloqueou o `.bat` | Mais informações > Executar assim mesmo, ou use a instalação manual (C) |
| Claude.ai não aceita o ZIP | Use `lattes-apcn.zip`, não o `...-instalador.zip`, e não extraia |

## Limites

Não acessa nem edita seu Lattes: só orienta. Nomes de menus do Lattes mudam; confira na tela. Cobre as listas de produções técnicas de **Ciências Ambientais** (16 tipologias de PTT) e da **Área de Ensino** (9 tipos de produto educacional). Para outras áreas, a skill avisa que a lista muda.
