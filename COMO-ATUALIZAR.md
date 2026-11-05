# Como atualizar a skill lattes-apcn

Não é preciso saber programar. Escolha o programa que você usa.

## Windows, com Claude Code ou Codex

1. Baixe o arquivo [ATUALIZAR-Windows.bat](https://github.com/jalinegm/lattes-apcn/releases/latest/download/ATUALIZAR-Windows.bat).
2. Na pasta Downloads, dê **dois cliques** no arquivo.
3. Se aparecer "O Windows protegeu o computador", clique em **Mais informações** e depois em **Executar assim mesmo**.
4. Se perguntar sobre instalar o Python, digite **S**. Ao terminar, dê dois cliques no arquivo mais uma vez.
5. Quando aparecer "Pronto", aperte qualquer tecla.
6. **Feche e abra de novo** o Claude Code ou o Codex.

O arquivo baixa a versão nova da skill e a copia para o lugar certo. Ele não acessa seu Lattes nem seus documentos.

## Mac ou Linux, com Claude Code ou Codex

1. Abra o aplicativo **Terminal**.
2. Copie a linha abaixo, cole no Terminal e aperte **Enter**:

   ```
   curl -fsSL https://github.com/jalinegm/lattes-apcn/releases/latest/download/atualizar-mac-linux.sh | sh
   ```
3. Quando aparecer "Pronto", **feche e abra de novo** o Claude Code ou o Codex.

## Claude.ai (site ou app)

1. Baixe [lattes-apcn.zip](https://github.com/jalinegm/lattes-apcn/releases/latest/download/lattes-apcn.zip). Não extraia.
2. Em **Configurações > Capacidades**, remova a skill `lattes-apcn` antiga.
3. Clique em **Enviar skill** e escolha o arquivo.

## Como conferir

Abra uma conversa nova e digite `/lattes-apcn`, ou acione a skill pelo nome. Deve aparecer um menu com três opções.

## Se algo der errado

| O que aconteceu | O que fazer |
|---|---|
| "Não foi possível baixar" | Confira a internet e tente de novo |
| "Não foi possível copiar" | Feche o Claude Code e o Codex e execute de novo |
| O computador é institucional e bloqueou o arquivo | Peça apoio à TI ou siga a instalação manual no [README](README.md) |
| O menu não apareceu | Feche e abra o programa de novo e abra uma conversa nova |

---

## Para quem mantém a skill

1. Altere `lattes-apcn/` e o número em `lattes-apcn/VERSAO.txt`.
2. Rode `python gerar-pacote.py`. Os arquivos ficam em `dist/`.
3. Depois de testar, publique:

   ```
   gh release create vX.Y.Z dist/* --title "vX.Y.Z" --notes "O que mudou"
   ```

Só a versão publicada chega aos professores: os links acima sempre apontam para a última release, e mudanças ainda não publicadas não os afetam.
