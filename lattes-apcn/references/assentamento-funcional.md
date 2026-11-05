# Assentamento Funcional Digital: carreira e portarias

Para servidor público federal. O ZIP reúne a vida funcional inteira: portarias, mas também dados bancários, reservista, diploma, documentos de família e, no assentamento antigo digitalizado, páginas de outros servidores. A skill aproveita apenas o que vai para o Lattes: **portarias, principalmente progressões e promoções**.

## Quando indicar

Na opção 3, e na opção 2 quando o assunto for vínculo. Confira no inventário (`dados_gerais` > `ATUACOES-PROFISSIONAIS`) o vínculo de servidor. Indique o assentamento se houver:

- um único bloco de enquadramento desde o ingresso, sem a progressão;
- enquadramento sem classe e número, como apenas "Professor";
- blocos que não citam a portaria em informações adicionais.

## Como baixar

Passe ao docente:

1. Entre no **SouGov.br**.
2. Na área **Serviços Disponíveis**, clique em **Todos os Serviços**.
3. Clique em **Assentamento Funcional Digital**.
4. Clique na caixinha **Selecionar todos para baixar**. Os arquivos são compactados e baixados em um único `.zip`.
5. Envie o `.zip` aqui, ou diga onde foi salvo.

Avise antes: o arquivo traz dados pessoais e de terceiros; a skill abre só o que interessa ao Lattes. Quem não é servidor federal não tem esse serviço: peça as portarias à gestão de pessoas.

## Como extrair

Não abra os PDFs do ZIP com ferramentas de leitura nem o extraia em pasta: o comando lê tudo em memória e devolve só os atos do próprio docente, com CPF, identidade e matrícula mascarados.

```
python -X utf8 scripts/lattes_xml.py assentamento documentos.zip --base CV.zip --saida assentamento.json
```

Requer `pypdf` (`python -m pip install pypdf`). Sem o currículo, use `--nome "Nome Completo"`: o nome separa as páginas de outros servidores. Depois, leia `assentamento.json`.

Cada evento traz categoria, caminho sugerido no Lattes, número da portaria, data do ato, efeitos, classe e nível, arquivo e página. Em `curriculo` vêm os vínculos e as comissões já lançados, para comparar.

Texto de assentamento antigo vem de digitalização e pode ter erro de leitura em número e data. Antes de usar, peça ao docente para conferir no arquivo e na página indicados. Se ele pedir para você olhar um PDF, abra só aquela página. O campo `paginas_sem_texto` conta o que não foi lido; informe esse total.

## O que fazer com cada categoria

| Categoria | No Lattes |
|---|---|
| `progressao_promocao` | Atuação profissional > vínculo: encerra o bloco anterior e abre um novo, citando a portaria em informações adicionais [Oficina 26 out] |
| `posse_nomeacao` | Início do vínculo e do primeiro bloco [Oficina] |
| `rsc`, `retribuicao_titulacao` | Não mudam classe nem nível: citar em informações adicionais do bloco [Inferido] |
| `funcao` | Atividade > Direção e administração, com a portaria [Inferido] |
| `comissao_colegiado` | Atividade > Conselhos, comissões e consultoria, com a portaria [Oficina] |
| `afastamento_licenca` | Bloco de licença sem sobrepor o de servidor; o que fez no período vai em atividade [Inferido, a partir do exemplo da oficina] |
| `redistribuicao_remocao` | Conferir instituição e datas do vínculo [Inferido] |

Regras da oficina para o vínculo [Oficina; Oficina 26 out]:

- **Vínculo** é a relação formal: servidor público. **Enquadramento** é o que está no contracheque, na nomenclatura da instituição. No EBTT: classe A, B, C ou D e número.
- A progressão fica em **blocos fechados e sucessivos**, com início e fim. Não lance o nível atual desde o ingresso.
- **Não sobreponha** blocos de servidor: parece mais de um concurso. Função, coordenação e comissão são atividade, não vínculo.
- A **portaria** vai em informações adicionais de cada bloco: fará falta na promoção a titular.
- **Atividades atravessam a progressão:** a disciplina dada desde o ingresso segue como uma atividade, sem abrir nova a cada classe.

## O que entregar

```
## Trajetória no vínculo
| Início | Fim | Enquadramento | Portaria | Conferir em |

## Atividades para lançar
| Atividade | Tipo | Portaria | Já está no currículo? | Conferir em |

## O que não encontrei
[progressões, classes ou períodos sem documento; páginas sem texto]
```

- Use a data dos **efeitos** como início do bloco, quando houver; sem ela, peça a data ao docente. O fim de um bloco vem do início do seguinte.
- **Não deduza** progressão pelo intervalo de tempo, nem classe ou data que o documento não traz. Se `tem_progressao_ou_promocao` for `false`, avise claramente: as progressões não apareceram nesse arquivo, e isso não significa que o servidor não as teve. Oriente procurar a **Gestão de Pessoas do campus** para obter as portarias. Com elas, a trajetória pode ser montada.
- Compare comissões com `curriculo.comissoes` pelo sentido: o texto no Lattes costuma estar escrito de outro modo. Em dúvida, pergunte.
- Comissões entram na janela e na aderência como evidência de atuação, mas não são produto. Não trate portaria como produção.

Esses itens ficam em dados gerais: a orientação padrão é **lançar e corrigir na tela**. A importação não altera bloco existente, e a de dados gerais tem efeito desconhecido (ver `importacao-xml.md`).
