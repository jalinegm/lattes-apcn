#!/usr/bin/env python3
"""Ferramentas para o XML do Curriculo Lattes (somente biblioteca padrao do Python).

Comandos:
  tipos                                 lista os tipos de item que o gerador aceita
  campos TIPO                           mostra os campos de um tipo, segundo a DTD
  inventario CV [--saida ARQ.json]      resume o curriculo sem dados pessoais sensiveis
  gerar PLANO --base CV --saida ARQ.xml cria o XML de importacao com os itens aprovados
  validar ARQ.xml                       confere um XML contra a DTD
  comparar PLANO --base CV              pre-diff: separa o que e novo do que ja esta no curriculo
  pasta CAMINHO --saida ARQ.json        cataloga uma pasta (ou ZIP) com varios comprovantes
  doi DOI                               busca os metadados de um DOI no Crossref (usa a internet)
  buscar --orcid ID --base CV           publicacoes do ORCID no OpenAlex ausentes do curriculo (usa a internet)
  assentamento ZIP --nome NOME --saida ARQ.json
                                        extrai carreira e portarias do Assentamento Funcional Digital (requer pypdf)

CV pode ser o .xml ou o .zip que o Lattes entrega. O arquivo original nunca e alterado.
Saidas de texto em UTF-8; o XML gerado em ISO-8859-1, como o Lattes exporta.
"""
import argparse
import difflib
import hashlib
import html
import io
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

DTD_PATH = Path(__file__).resolve().parent.parent / "assets" / "LMPLCurriculo.DTD"
RAIZES_ITENS = ("PRODUCAO-BIBLIOGRAFICA", "PRODUCAO-TECNICA", "OUTRA-PRODUCAO", "DADOS-COMPLEMENTARES")
LIMITE_XML = 40 * 1024 * 1024
LIMITE_MEMO = 2000  # DTD, versao 1.2: campos Memo do Lattes vao ate 2000 caracteres.
DADOS_GERAIS_PERMITIDOS = {"NOME-COMPLETO", "NOME-EM-CITACOES-BIBLIOGRAFICAS", "ORCID-ID"}
DADOS_GERAIS_EXIGIDOS = (
    "NOME-COMPLETO", "NOME-EM-CITACOES-BIBLIOGRAFICAS", "NACIONALIDADE", "SEXO", "PERMISSAO-DE-DIVULGACAO",
)
FILHOS_SENSIVEIS = {"ENDERECO", "LICENCAS"}
ATRIBUTO_SENSIVEL = re.compile(
    r"CPF|PASSAPORTE|IDENTIDADE|^RG$|ORGAO-EMISSOR|NOME-DO-PAI|NOME-DA-MAE|NASCIMENTO|^SEXO$|^RACA|^COR-|^PCD$"
    r"|TELEFONE|E-?MAIL|(^|-)CEP($|-)|LOGRADOURO|BAIRRO"
)
# Tipos com relato publico de importacao real (Auto Lattes, abr 2026). Os demais nao tem relato.
TIPOS_COM_RELATO = {
    "ARTIGO-PUBLICADO", "TRABALHO-EM-EVENTOS", "LIVRO-PUBLICADO-OU-ORGANIZADO", "CAPITULO-DE-LIVRO-PUBLICADO",
    "ORIENTACOES-CONCLUIDAS-PARA-MESTRADO", "ORIENTACOES-CONCLUIDAS-PARA-DOUTORADO",
    "ORIENTACOES-CONCLUIDAS-PARA-POS-DOUTORADO", "OUTRAS-ORIENTACOES-CONCLUIDAS", "PREMIO-TITULO",
}
# Registros que se repetem por ano ou edicao: mesmo titulo em outro ano pode ser item novo.
TIPOS_RECORRENTES = re.compile(
    r"CURSO-DE-CURTA|ORGANIZACAO-DE-EVENTO|EDITORACAO|MIDIA-SOCIAL|TRABALHO-TECNICO|OUTRA-PRODUCAO-TECNICA"
    r"|PARTICIPACAO-EM-(?!BANCA)|OUTRAS-PARTICIPACOES-EM-EVENTOS|APRESENTACAO-DE-TRABALHO|PROGRAMA-DE-RADIO"
)
CAMPOS_PESSOA = ("NOME-DO-CANDIDATO", "NOME-DO-ORIENTADO", "NOME-DO-ORIENTANDO")
EXTENSOES_DOCUMENTO = {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".html", ".htm", ".eml", ".msg",
                       ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".heic",
                       ".xls", ".xlsx", ".ods", ".csv", ".ppt", ".pptx"}
NOME_SENSIVEL = re.compile(
    r"\b(cnh|rg|cpf|passaporte|carteira.de.identidade|t[ií]tulo.de.eleitor|holerite|contracheque|nota.fiscal"
    r"|comprovante.de.resid|imposto.de.renda|irpf|extrato.banc|certid[aã]o.de.(nascimento|casamento)"
    r"|exame.(m[eé]dico|de.sangue|laborat)|receita.m[eé]dica|senhas?\b)",
    re.I,
)
# Fora do gerador de proposito: dados pessoais, sem utilidade para a APCN.
ELEMENTOS_BLOQUEADOS = {"ENDERECO", "ENDERECO-PROFISSIONAL", "ENDERECO-RESIDENCIAL"}
# Valores que o proprio Lattes exporta, embora a DTD nao os liste.
VALORES_OBSERVADOS = {
    ("PROJETO-DE-PESQUISA", "NATUREZA"): {"ENSINO"},
    ("DADOS-BASICOS-DE-ORIENTACOES-CONCLUIDAS-PARA-MESTRADO", "TIPO"): {"NAO_INFORMADO"},
    ("DADOS-BASICOS-DA-ORGANIZACAO-DE-EVENTO", "TIPO"): {"OLIMPIADA"},
    ("DADOS-BASICOS-DO-TRABALHO-TECNICO", "NATUREZA"): {"EXTENSAO_TECNOLOGICA"},
}
# Campo que identifica cada registro de dados gerais, para o pre-diff: (titulo, ano).
CHAVES_DADOS_GERAIS = {
    "PROJETO-DE-PESQUISA": ("NOME-DO-PROJETO", "ANO-INICIO"),
    "LINHA-DE-PESQUISA": ("TITULO-DA-LINHA-DE-PESQUISA", ""),
    "IDIOMA": ("IDIOMA", ""),
    "AREA-DE-ATUACAO": ("NOME-DA-AREA-DO-CONHECIMENTO", ""),
    "GRADUACAO": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "ESPECIALIZACAO": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "MESTRADO": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "MESTRADO-PROFISSIONALIZANTE": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "DOUTORADO": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "CURSO-TECNICO-PROFISSIONALIZANTE": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "FORMACAO-COMPLEMENTAR-CURSO-DE-CURTA-DURACAO": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "FORMACAO-COMPLEMENTAR-DE-EXTENSAO-UNIVERSITARIA": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "MBA": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
    "OUTROS": ("NOME-CURSO", "ANO-DE-CONCLUSAO"),
}
LIMITE_ARQUIVOS = 2000
LIMITE_RESPOSTA = 8 * 1024 * 1024
TIPOGRAFIA = {
    "–": "-", "—": "-", "‐": "-", "‑": "-", "−": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"', "…": "...",
    " ": " ", "​": "", "•": "-",
}


def erro(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    return 1


# ---------------------------------------------------------------- DTD ----------
class DTD:
    """Le a DTD do Lattes: modelos de conteudo e atributos."""

    def __init__(self, caminho=DTD_PATH):
        texto = Path(caminho).read_text(encoding="latin-1")
        texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
        self.modelos, self.attrs, self.regex = {}, {}, {}
        for nome, modelo in re.findall(r"<!ELEMENT\s+(\S+)\s+(.*?)>", texto, flags=re.S):
            self.modelos[nome] = re.sub(r"\s+", "", modelo)
        padrao = re.compile(
            r'(\S+)\s+(CDATA|NMTOKENS?|IDREFS?|ID|\([^)]*\))\s+(#REQUIRED|#IMPLIED|#FIXED\s+"[^"]*"|"[^"]*")'
        )
        for nome, corpo in re.findall(r"<!ATTLIST\s+(\S+)(.*?)>", texto, flags=re.S):
            campos = self.attrs.setdefault(nome, {})
            for attr, tipo, padrao_valor in padrao.findall(corpo):
                enum = [v.strip() for v in tipo.strip("()").split("|")] if tipo.startswith("(") else None
                obrig = padrao_valor == "#REQUIRED"
                fixo = padrao_valor.startswith("#FIXED")
                default = padrao_valor.split('"')[1] if '"' in padrao_valor else None
                campos[attr] = {"enum": enum, "obrigatorio": obrig, "fixo": fixo, "default": default}
        self.pais = self._mapear_caminhos()
        self.caminhos = self._mapear_caminhos(("CURRICULO-VITAE",))

    def filhos(self, elemento):
        modelo = self.modelos.get(elemento, "EMPTY")
        if modelo in ("EMPTY", "ANY") or "#PCDATA" in modelo and "|" not in modelo:
            return []
        vistos = []
        for nome in re.findall(r"[A-Za-z][\w:.-]*", modelo.replace("#PCDATA", "")):
            if nome not in vistos:
                vistos.append(nome)
        return vistos

    def _regex_de(self, elemento):
        if elemento not in self.regex:
            modelo = self.modelos[elemento]
            if modelo == "ANY":
                self.regex[elemento] = None
            elif modelo == "EMPTY":
                self.regex[elemento] = re.compile(r"")
            else:
                semtexto = modelo.replace("#PCDATA|", "").replace("(#PCDATA)", "()")
                corpo = re.sub(r"[A-Za-z][\w:.-]*", lambda m: f"(?:{m.group(0)} )", semtexto).replace(",", "")
                self.regex[elemento] = re.compile(corpo)
        return self.regex[elemento]

    def _mapear_caminhos(self, raizes=RAIZES_ITENS):
        caminhos = {raiz: [raiz] for raiz in raizes}
        fila = list(raizes)
        while fila:
            atual = fila.pop(0)
            for filho in self.filhos(atual):
                if filho not in caminhos:
                    caminhos[filho] = caminhos[atual] + [filho]
                    fila.append(filho)
        return caminhos

    def tipos(self):
        """Elementos abaixo das producoes que tem DADOS-BASICOS: sao os itens lancaveis."""
        return sorted(
            nome for nome in self.pais
            if any(f.startswith("DADOS-BASICOS") for f in self.filhos(nome))
        )

    def tipos_arvore(self):
        """Registros fora das producoes. Atuacao carrega dentro dela vinculos, disciplinas, projetos etc."""
        return sorted(
            {"RESUMO-CV", "OUTRAS-INFORMACOES-RELEVANTES", "ATUACAO-PROFISSIONAL", "AREA-DE-ATUACAO", "IDIOMA",
             "PREMIO-TITULO", "INFORMACAO-ADICIONAL-CURSO", "INFORMACAO-ADICIONAL-INSTITUICAO"}
            | set(self.filhos("FORMACAO-ACADEMICA-TITULACAO")) | set(self.filhos("FORMACAO-COMPLEMENTAR"))
        )

    def validar(self, raiz):
        problemas = []
        for elem in raiz.iter():
            nome = elem.tag
            if nome not in self.modelos:
                problemas.append(f"Elemento nao declarado: {nome}")
                continue
            sequencia = "".join(f"{f.tag} " for f in elem)
            rx = self._regex_de(nome)
            if rx is not None and not rx.fullmatch(sequencia):
                problemas.append(f"Conteudo fora da ordem/forma da DTD em {nome}: {sequencia.strip()[:200]}")
            declarados = self.attrs.get(nome, {})
            for attr, valor in elem.attrib.items():
                info = declarados.get(attr)
                if info is None:
                    problemas.append(f"Atributo nao declarado: {nome}/{attr}")
                elif info["enum"] and valor not in info["enum"] and valor not in VALORES_OBSERVADOS.get((nome, attr), ()):
                    problemas.append(f'Valor "{valor}" invalido em {nome}/{attr}; opcoes: {" | ".join(info["enum"])}')
            for attr, info in declarados.items():
                if info["obrigatorio"] and attr not in elem.attrib:
                    problemas.append(f"Atributo obrigatorio ausente: {nome}/{attr}")
        return problemas


# --------------------------------------------------------------- leitura --------
def ler_bytes_cv(caminho):
    caminho = Path(caminho)
    if not caminho.is_file():
        raise ValueError(f"arquivo nao encontrado: {caminho}")
    if zipfile.is_zipfile(caminho):
        with zipfile.ZipFile(caminho) as zf:
            xmls = [i for i in zf.infolist() if i.filename.lower().endswith(".xml") and not i.is_dir()]
            if len(xmls) != 1:
                raise ValueError(f"o ZIP deveria ter um unico XML; tem {len(xmls)}")
            if xmls[0].file_size > LIMITE_XML:
                raise ValueError("XML dentro do ZIP e grande demais para um curriculo")
            return zf.read(xmls[0])
    if caminho.stat().st_size > LIMITE_XML:
        raise ValueError("arquivo grande demais para um curriculo")
    return caminho.read_bytes()


def ler_cv(caminho):
    dados = ler_bytes_cv(caminho)
    if b"<!ENTITY" in dados[:4096]:
        raise ValueError("o XML declara entidades; o Lattes nao faz isso. Arquivo recusado por seguranca")
    raiz = ET.fromstring(dados)
    if raiz.tag != "CURRICULO-VITAE":
        raise ValueError(f"nao parece um Curriculo Lattes (raiz: {raiz.tag})")
    return raiz


def limpar(atributos):
    return {k: v for k, v in atributos.items() if v and not ATRIBUTO_SENSIVEL.search(k)}


def primeiro(atributos, prefixos, excluir="-INGLES"):
    for chave, valor in atributos.items():
        if any(chave.startswith(p) for p in prefixos) and not chave.endswith(excluir) and valor:
            return valor
    return ""


def arvore_limpa(elem):
    """Converte um elemento em dicionario, sem atributos vazios nem sensiveis."""
    saida = limpar(elem.attrib)
    if elem.text and elem.text.strip():
        saida["_texto"] = elem.text.strip()
    for filho in elem:
        if filho.tag in FILHOS_SENSIVEIS:
            continue
        convertido = arvore_limpa(filho)
        if convertido:
            saida.setdefault(filho.tag, []).append(convertido)
    return saida


def registro_geral(tipo, titulo, ano):
    return {"bloco": "DADOS-GERAIS", "tipo": tipo, "titulo": titulo, "titulo_ingles": "", "pessoa": "", "ano": ano,
            "natureza": "", "doi": "", "link": "", "divulgacao_cientifica": "", "detalhes": {}, "autores": [],
            "palavras_chave": [], "outras_informacoes": ""}


def itens_de(raiz):
    itens = []
    for nome_raiz in RAIZES_ITENS:
        secao = raiz.find(nome_raiz)
        if secao is None:
            continue
        for elem in secao.iter():
            basicos = next((f for f in elem if f.tag.startswith("DADOS-BASICOS")), None)
            if basicos is None:
                continue
            detalhe = next((f for f in elem if f.tag.startswith("DETALHAMENTO")), None)
            pessoas = [
                primeiro(f.attrib, ("NOME-COMPLETO",))
                for f in elem if f.tag == "AUTORES" or f.tag.startswith("PARTICIPANTE")
            ]
            chaves = elem.find("PALAVRAS-CHAVE")
            info = elem.find("INFORMACOES-ADICIONAIS")
            itens.append({
                "bloco": nome_raiz,
                "tipo": elem.tag,
                "titulo": primeiro(basicos.attrib, ("TITULO",)),
                "titulo_ingles": next((v for k, v in basicos.attrib.items()
                                       if k.startswith("TITULO") and k.endswith("-INGLES") and v), ""),
                "pessoa": primeiro(detalhe.attrib, CAMPOS_PESSOA) if detalhe is not None else "",
                "ano": primeiro(basicos.attrib, ("ANO",)),
                "natureza": basicos.get("NATUREZA", "") or basicos.get("TIPO", ""),
                "doi": basicos.get("DOI", ""),
                "link": basicos.get("HOME-PAGE-DO-TRABALHO", "") or basicos.get("HOME-PAGE", ""),
                "divulgacao_cientifica": basicos.get("FLAG-DIVULGACAO-CIENTIFICA", ""),
                "detalhes": limpar(detalhe.attrib) if detalhe is not None else {},
                "autores": [p for p in pessoas if p],
                "palavras_chave": [v for v in chaves.attrib.values() if v] if chaves is not None else [],
                "outras_informacoes": info.get("DESCRICAO-INFORMACOES-ADICIONAIS", "") if info is not None else "",
            })
    gerais = raiz.find("DADOS-GERAIS")
    for elem in gerais.iter() if gerais is not None else ():
        chave = CHAVES_DADOS_GERAIS.get(elem.tag)
        if chave and elem.get(chave[0]):
            itens.append(registro_geral(elem.tag, elem.get(chave[0]), elem.get(chave[1], "") if chave[1] else ""))
    secao = raiz.find("DADOS-COMPLEMENTARES/FORMACAO-COMPLEMENTAR")
    for elem in secao if secao is not None else ():
        chave = CHAVES_DADOS_GERAIS.get(elem.tag)
        if chave and elem.get(chave[0]):
            itens.append(registro_geral(elem.tag, elem.get(chave[0]), elem.get(chave[1], "")))
    for premio in raiz.iterfind("DADOS-GERAIS/PREMIOS-TITULOS/PREMIO-TITULO"):
        itens.append({
            "bloco": "DADOS-GERAIS", "tipo": "PREMIO-TITULO",
            "titulo": premio.get("NOME-DO-PREMIO-OU-TITULO", ""),
            "titulo_ingles": premio.get("NOME-DO-PREMIO-OU-TITULO-INGLES", ""),
            "pessoa": "", "ano": premio.get("ANO-DA-PREMIACAO", ""), "natureza": "", "doi": "", "link": "",
            "divulgacao_cientifica": "", "detalhes": limpar(premio.attrib), "autores": [],
            "palavras_chave": [], "outras_informacoes": "",
        })
    return itens


# ------------------------------------------------------------ duplicatas --------
def normalizar(texto):
    texto = unicodedata.normalize("NFKD", html.unescape(texto or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def limpar_doi(doi):
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", (doi or "").strip(), flags=re.I)


def descrever(ex):
    return f"{ex['tipo']}: {ex['titulo']} ({ex['ano']})"


def diferencas(novo, ex):
    saida = []
    if novo["ano"] and ex["ano"] and novo["ano"] != ex["ano"]:
        saida.append(f"ano: curriculo {ex['ano']}, documento {novo['ano']}")
    doi_novo, doi_ex = limpar_doi(novo["doi"]).lower(), limpar_doi(ex["doi"]).lower()
    if doi_novo and doi_novo != doi_ex:
        saida.append(f"DOI: curriculo {doi_ex or '(vazio)'}, documento {doi_novo}")
    if novo["link"] and not ex["link"]:
        saida.append("link: vazio no curriculo")
    return saida


def classificar(novo, existentes):
    """Pre-diff de um item. Status: NOVO, JA_EXISTE, DIVERGENTE, NOVA_EDICAO ou POSSIVEL."""
    titulo = normalizar(novo["titulo"])
    doi = limpar_doi(novo["doi"]).lower()
    pessoa = normalizar(novo.get("pessoa", ""))
    recorrente = TIPOS_RECORRENTES.search(novo["tipo"])
    if doi:
        for ex in existentes:
            if limpar_doi(ex["doi"]).lower() == doi:
                difs = diferencas(novo, ex)
                return {"status": "DIVERGENTE" if difs else "JA_EXISTE", "motivo": "mesmo DOI", "item": ex,
                        "diferencas": difs}
    outro_menu, outra_edicao = None, None
    for ex in existentes:
        if not titulo or titulo not in (normalizar(ex["titulo"]), normalizar(ex.get("titulo_ingles", ""))):
            continue
        if novo["tipo"] and ex["tipo"] != novo["tipo"]:
            outro_menu = outro_menu or ex
        elif recorrente and novo["ano"] and ex["ano"] and novo["ano"] != ex["ano"]:
            outra_edicao = outra_edicao or ex
        else:
            difs = diferencas(novo, ex)
            return {"status": "DIVERGENTE" if difs else "JA_EXISTE", "motivo": "mesmo titulo e mesmo tipo",
                    "item": ex, "diferencas": difs}
    if outra_edicao:
        return {"status": "NOVA_EDICAO", "motivo": "mesmo titulo em outro ano; cada edicao tem registro proprio",
                "item": outra_edicao, "diferencas": []}
    if outro_menu:
        return {"status": "POSSIVEL", "motivo": "mesmo titulo em outro menu", "item": outro_menu, "diferencas": []}
    if pessoa:
        for ex in existentes:
            if ex["tipo"] == novo["tipo"] and ex["ano"] == novo["ano"] and normalizar(ex.get("pessoa", "")) == pessoa:
                return {"status": "POSSIVEL", "motivo": "mesma pessoa, mesmo tipo e mesmo ano", "item": ex,
                        "diferencas": []}
    melhor = None
    for ex in existentes:
        ex_n = normalizar(ex["titulo"])
        if not ex_n or not titulo:
            continue
        menor, maior = sorted((ex_n, titulo), key=len)
        razao = 0.95 if len(menor) >= 25 and maior.startswith(menor) else \
            difflib.SequenceMatcher(None, ex_n, titulo).ratio()
        if razao >= 0.85 and (melhor is None or razao > melhor[0]):
            melhor = (razao, ex)
    if melhor:
        return {"status": "POSSIVEL", "motivo": f"titulo parecido ({melhor[0]:.0%})", "item": melhor[1],
                "diferencas": []}
    return {"status": "NOVO", "motivo": "", "item": None, "diferencas": []}


def resumos_arvore(tipo, no):
    """Registros identificaveis dentro de um item em arvore."""
    saida = []
    chave = CHAVES_DADOS_GERAIS.get(tipo)
    atributos = no.get("atributos", {})
    if chave and atributos.get(chave[0]):
        saida.append({"tipo": tipo, "titulo": atributos[chave[0]], "titulo_ingles": "",
                      "ano": atributos.get(chave[1], "") if chave[1] else "", "doi": "", "link": "", "pessoa": ""})
    for filho in no.get("filhos", []):
        saida += resumos_arvore(filho.get("tipo", ""), filho)
    return saida


def resumos_do_item(item):
    if item.get("xml") is None or item.get("tipo") == "PREMIO-TITULO":
        return [resumo_item(item)]
    achados = resumos_arvore(item.get("tipo", ""), item["xml"])
    return achados or [resumo_item(item)]


def resumo_item(item):
    dados = item.get("dados") or (item.get("xml") or {}).get("atributos", {})
    pessoa = primeiro({**dados, **item.get("detalhamento", {})}, CAMPOS_PESSOA)
    link = dados.get("HOME-PAGE-DO-TRABALHO", "") or dados.get("HOME-PAGE", "")
    return {"tipo": item.get("tipo", ""), "titulo": primeiro(dados, ("TITULO", "NOME-DO-PREMIO")),
            "titulo_ingles": "", "ano": primeiro(dados, ("ANO",)), "doi": dados.get("DOI", ""), "link": link,
            "pessoa": pessoa}


# --------------------------------------------------------------- comandos -------
def cmd_tipos(_):
    dtd = DTD()
    for tipo in dtd.tipos():
        print(f"{tipo}  <-  {' > '.join(dtd.pais[tipo][:-1])}")
    print("\nFora das producoes (efeito da importacao desconhecido; exigem risco_aceito, salvo premio):")
    for tipo in dtd.tipos_arvore():
        print(f"{tipo}  <-  {' > '.join(dtd.caminhos[tipo][1:-1])}")
    return 0


def descrever_attrs(dtd, elemento):
    for attr, info in dtd.attrs.get(elemento, {}).items():
        if info["fixo"]:
            continue
        marca = []
        if info["enum"]:
            marca.append("opcoes: " + " | ".join(info["enum"]))
        if info["default"]:
            marca.append(f"padrao: {info['default']}")
        print(f"    {attr}" + (f"  ({'; '.join(marca)})" if marca else ""))


def cmd_campos(args):
    dtd = DTD()
    if args.tipo not in dtd.modelos:
        parecidos = difflib.get_close_matches(args.tipo, list(dtd.modelos), n=5, cutoff=0.4)
        return erro(f"nao existe na DTD: {args.tipo}. Parecidos: {parecidos}.")
    print(f"{args.tipo}\nCaminho no XML: {' > '.join(dtd.caminhos[args.tipo][1:])}\nModelo: {dtd.modelos[args.tipo]}")
    descrever_attrs(dtd, args.tipo)
    for filho in dtd.filhos(args.tipo):
        print(f"\n  {filho}")
        descrever_attrs(dtd, filho)
    return 0


def cmd_inventario(args):
    raiz = ler_cv(args.cv)
    gerais = raiz.find("DADOS-GERAIS")
    identificacao = {k: gerais.get(k, "") for k in sorted(DADOS_GERAIS_PERMITIDOS)}
    identificacao["NUMERO-IDENTIFICADOR"] = raiz.get("NUMERO-IDENTIFICADOR", "")
    identificacao["DATA-ATUALIZACAO"] = raiz.get("DATA-ATUALIZACAO", "")
    resto = {f.tag: arvore_limpa(f) for f in gerais if f.tag not in FILHOS_SENSIVEIS}
    itens = itens_de(raiz)
    saida = {"identificacao": identificacao, "dados_gerais": resto, "itens": itens}
    texto = json.dumps(saida, ensure_ascii=False, indent=1)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
        print(f"Inventario gravado em {args.saida}")
    else:
        print(texto)
    if args.saida:
        print(f"Curriculo atualizado em {identificacao['DATA-ATUALIZACAO'] or '(sem data)'}; {len(itens)} itens:")
        for tipo, qtde in Counter(i["tipo"] for i in itens).most_common():
            print(f"  {qtde:4d}  {tipo}")
    return 0


def sanear(valor, avisos, onde):
    """Deixa o texto representavel em ISO-8859-1 sem mudar letras acentuadas."""
    original = str(valor)
    texto = "".join(TIPOGRAFIA.get(c, c) for c in unicodedata.normalize("NFC", original))
    texto = re.sub(r"\s*[\r\n\t]+\s*", " ", texto).strip()
    if texto != original.strip():
        avisos.append(f"{onde}: pontuacao ou espacos ajustados para o padrao do Lattes")
    try:
        texto.encode("iso-8859-1")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{onde}: caractere {original[exc.start]!r} nao existe em ISO-8859-1; reescreva o trecho")
    return texto


def montar_attrs(dtd, elemento, valores, avisos, problemas, rotulo):
    declarados = dtd.attrs.get(elemento, {})
    saida = {}
    for attr in valores:
        if attr not in declarados:
            problemas.append(f"{rotulo}: campo {attr} nao existe em {elemento}")
    for attr, info in declarados.items():
        if info["fixo"] or (ATRIBUTO_SENSIVEL.search(attr) and elemento != "DADOS-GERAIS"):
            if attr in valores:
                problemas.append(f"{rotulo}: nao inclua {attr} no arquivo de importacao")
            continue
        valor = valores.get(attr)
        if valor is None or valor == "":
            if info["default"] is not None:
                saida[attr] = info["default"]
            elif not info["enum"]:
                saida[attr] = ""
            continue
        try:
            valor = sanear(valor, avisos, f"{rotulo}/{attr}")
        except ValueError as exc:
            problemas.append(str(exc))
            continue
        if info["enum"] and valor not in info["enum"]:
            if valor in VALORES_OBSERVADOS.get((elemento, attr), ()):
                avisos.append(f'{rotulo}: "{valor}" em {attr} nao esta na DTD, mas o Lattes exporta esse valor; confira no teste')
            else:
                problemas.append(f'{rotulo}: "{valor}" invalido em {attr}; opcoes: {" | ".join(info["enum"])}')
        if len(valor) > LIMITE_MEMO:
            avisos.append(f"{rotulo}/{attr}: {len(valor)} caracteres; o Lattes aceita ate {LIMITE_MEMO} em textos longos")
        saida[attr] = valor
    return saida


def ajustar_basicos(dados):
    dados = dict(dados)
    if dados.get("DOI"):
        dados["DOI"] = limpar_doi(dados["DOI"])
    for campo in ("HOME-PAGE-DO-TRABALHO", "HOME-PAGE"):
        link = (dados.get(campo) or "").strip()
        if link and not link.startswith("["):  # O Lattes exporta links entre colchetes.
            dados[campo] = f"[{link}]"
    return dados


def construir_no(dtd, tipo, no, contador, avisos, problemas, rotulo):
    """Monta um elemento a partir de {"atributos": {...}, "filhos": [{"tipo": ...}], "texto": ...}."""
    if tipo in ELEMENTOS_BLOQUEADOS:
        problemas.append(f"{rotulo}: {tipo} traz dados pessoais e fica fora do arquivo")
        return None
    if tipo not in dtd.modelos:
        problemas.append(f"{rotulo}: {tipo!r} nao existe na DTD")
        return None
    valores = ajustar_basicos(no.get("atributos", {}))
    for attr in dtd.attrs.get(tipo, {}):
        if attr.startswith("SEQUENCIA") and not valores.get(attr):
            contador[0] += 1
            valores[attr] = str(contador[0])
    elem = ET.Element(tipo, montar_attrs(dtd, tipo, valores, avisos, problemas, rotulo))
    if no.get("texto"):
        elem.text = sanear(no["texto"], avisos, f"{rotulo}/{tipo}")
    permitidos = dtd.filhos(tipo)
    for filho in no.get("filhos", []):
        nome = filho.get("tipo", "")
        if nome not in permitidos:
            problemas.append(f"{rotulo}: {nome!r} nao pode ficar dentro de {tipo}; aceitos: {permitidos}")
            continue
        convertido = construir_no(dtd, nome, filho, contador, avisos, problemas, rotulo)
        if convertido is not None:
            elem.append(convertido)
    return elem


def montar_item(dtd, item, seq, avisos, problemas):
    rotulo = f"item {item.get('id', '?')}"
    tipo = item.get("tipo", "")
    if tipo not in dtd.tipos():
        problemas.append(f"{rotulo}: tipo {tipo!r} nao aceito. Use o comando 'tipos'.")
        return None
    elem = ET.Element(tipo)
    valores_item = {a: str(seq) for a in dtd.attrs.get(tipo, {}) if a.startswith("SEQUENCIA")}
    elem.attrib.update(montar_attrs(dtd, tipo, valores_item, avisos, problemas, rotulo))
    filhos = dtd.filhos(tipo)
    for filho in filhos:
        if filho.startswith("DADOS-BASICOS"):
            dados = ajustar_basicos(item.get("dados", {}))
            attrs = montar_attrs(dtd, filho, dados, avisos, problemas, rotulo)
            for attr in dtd.attrs.get(filho, {}):
                if (attr.startswith("TITULO") and not attr.endswith("-INGLES") or attr.startswith("ANO")) \
                        and not attrs.get(attr):
                    problemas.append(f"{rotulo}: falta {attr}")
            ano = primeiro(attrs, ("ANO",))
            if ano and not re.fullmatch(r"\d{4}", ano):
                problemas.append(f"{rotulo}: ano deve ter 4 digitos, veio {ano!r}")
            ET.SubElement(elem, filho, attrs)
        elif filho.startswith("DETALHAMENTO"):
            ET.SubElement(elem, filho, montar_attrs(dtd, filho, item.get("detalhamento", {}), avisos, problemas, rotulo))
        elif filho == "AUTORES" or filho.startswith("PARTICIPANTE"):
            pessoas = item.get("autores", [])
            if not pessoas:
                problemas.append(f"{rotulo}: informe os autores/participantes, incluindo o docente")
            campos = dtd.attrs.get(filho, {})
            for ordem, pessoa in enumerate(pessoas, 1):
                valores = {}
                for attr in campos:
                    if attr.startswith("NOME-COMPLETO"):
                        valores[attr] = pessoa.get("nome", "")
                    elif attr.startswith("NOME-PARA-CITACAO"):
                        valores[attr] = pessoa.get("citacao", "")
                    elif attr.startswith("ORDEM"):
                        valores[attr] = str(pessoa.get("ordem", ordem))
                    elif attr.startswith("NRO-ID"):
                        valores[attr] = pessoa.get("id_cnpq", "")
                ET.SubElement(elem, filho, montar_attrs(dtd, filho, valores, avisos, problemas, rotulo))
        elif filho == "PALAVRAS-CHAVE" and item.get("palavras_chave"):
            chaves = item["palavras_chave"][:6]
            valores = {f"PALAVRA-CHAVE-{i}": c for i, c in enumerate(chaves, 1)}
            ET.SubElement(elem, filho, montar_attrs(dtd, filho, valores, avisos, problemas, rotulo))
        elif filho == "INFORMACOES-ADICIONAIS" and item.get("outras_informacoes"):
            valores = {"DESCRICAO-INFORMACOES-ADICIONAIS": item["outras_informacoes"]}
            ET.SubElement(elem, filho, montar_attrs(dtd, filho, valores, avisos, problemas, rotulo))
    contador = [seq * 100]
    for extra in item.get("extras", []):
        nome = extra.get("tipo", "")
        if nome not in filhos:
            problemas.append(f"{rotulo}: extra {nome!r} nao pode ficar dentro de {tipo}; aceitos: {filhos}")
            continue
        convertido = construir_no(dtd, nome, extra, contador, avisos, problemas, rotulo)
        if convertido is not None:
            elem.append(convertido)
    return elem


def anexar(dtd, raiz, tipo, elem):
    atual = raiz
    for nome in dtd.caminhos[tipo][1:-1]:
        existente = atual.find(nome)
        atual = ET.SubElement(atual, nome) if existente is None else existente
    atual.append(elem)


def ordenar(dtd, elem):
    """Coloca os filhos na ordem que a DTD exige."""
    ordem = {nome: i for i, nome in enumerate(dtd.filhos(elem.tag))}
    elem[:] = sorted(elem, key=lambda f: ordem.get(f.tag, 9999))
    for filho in elem:
        ordenar(dtd, filho)


def serializar(elem, nivel=0):
    margem = "  " * nivel
    attrs = "".join(f' {k}="{html.escape(v, quote=True).replace("&#x27;", chr(39))}"' for k, v in elem.attrib.items())
    if not len(elem) and not elem.text:
        return f"{margem}<{elem.tag}{attrs}/>\n"
    corpo = "".join(serializar(f, nivel + 1) for f in elem)
    if elem.text:
        return f"{margem}<{elem.tag}{attrs}>{html.escape(elem.text, quote=False)}{corpo}</{elem.tag}>\n"
    return f"{margem}<{elem.tag}{attrs}>\n{corpo}{margem}</{elem.tag}>\n"


def cmd_gerar(args):
    dtd = DTD()
    plano = json.loads(Path(args.plano).read_text(encoding="utf-8"))
    base = ler_cv(args.base)
    existentes = itens_de(base)
    gerais_base = base.find("DADOS-GERAIS")
    avisos, problemas, gerados, duplicados, ignorados, lote = [], [], [], [], [], []
    somente = set(args.somente.split(",")) if args.somente else None
    excluir = set(args.excluir.split(",")) if args.excluir else set()

    raiz = ET.Element("CURRICULO-VITAE", {
        "SISTEMA-ORIGEM-XML": base.get("SISTEMA-ORIGEM-XML") or "LATTES_OFFLINE",
        "NUMERO-IDENTIFICADOR": base.get("NUMERO-IDENTIFICADOR", ""),
    })
    faltando = [c for c in DADOS_GERAIS_EXIGIDOS if not gerais_base.get(c)]
    if faltando:
        problemas.append(f"curriculo de base sem campos obrigatorios: {faltando}")
    ET.SubElement(raiz, "DADOS-GERAIS", {c: gerais_base.get(c, "") for c in DADOS_GERAIS_EXIGIDOS})

    nome_docente = normalizar(gerais_base.get("NOME-COMPLETO", ""))
    # Continua a numeracao do curriculo para nao repetir nenhuma sequencia existente.
    seq = max([int(v) for e in base.iter() for k, v in e.attrib.items()
               if k.startswith("SEQUENCIA") and v.isdigit()] or [0])
    for item in plano.get("itens", []):
        id_item = str(item.get("id", "?"))
        if (somente is not None and id_item not in somente) or id_item in excluir:
            continue
        if item.get("aprovado") is not True:
            ignorados.append(id_item)
            continue
        dados = item.get("dados", {})
        resumo = resumo_item(item)
        titulo, ano = resumo["titulo"], resumo["ano"]
        resumos = resumos_do_item(item)
        dup = next((d for d in (classificar(r, existentes + lote) for r in resumos) if d["status"] != "NOVO"), None)
        if dup and item.get("confirmar_duplicata") is not True:
            duplicados.append({
                "id": id_item, "titulo": titulo, "status": dup["status"], "motivo": dup["motivo"],
                "diferencas": dup["diferencas"], "ja_existe": descrever(dup["item"]),
            })
            continue
        lote += resumos
        tipo_item = item.get("tipo", "")
        em_arvore = tipo_item in dtd.tipos_arvore()
        if tipo_item not in TIPOS_COM_RELATO:
            avisos.append(f"item {id_item}: {tipo_item} sem relato de importacao real; confira no item de teste")
        if em_arvore and tipo_item != "PREMIO-TITULO" and item.get("risco_aceito") is not True:
            problemas.append(f"item {id_item}: {tipo_item} fica nos dados gerais; o efeito de importar esse bloco "
                             "e desconhecido. Exige risco_aceito depois de explicar ao docente")
            continue
        if tipo_item == "ATUACAO-PROFISSIONAL":
            instituicao = (item.get("xml") or {}).get("atributos", {}).get("NOME-INSTITUICAO", "")
            if any(normalizar(i) == normalizar(instituicao)
                   for i in (e.get("NOME-INSTITUICAO", "") for e in base.iter("ATUACAO-PROFISSIONAL"))):
                avisos.append(f"item {id_item}: instituicao ja consta na atuacao; a importacao pode criar outra atuacao")
        seq += 1
        if item.get("xml") is not None or em_arvore:
            if tipo_item not in dtd.caminhos or tipo_item in ELEMENTOS_BLOQUEADOS or \
                    not (em_arvore or tipo_item in dtd.tipos()):
                problemas.append(f"item {id_item}: tipo {tipo_item!r} nao aceito. Use o comando 'tipos'.")
                continue
            no = item.get("xml") or {"atributos": dados}
            contador = [seq * 100]
            elem = construir_no(dtd, tipo_item, no, contador, avisos, problemas, f"item {id_item}")
            if elem is None:
                continue
            if tipo_item == "PREMIO-TITULO" and not (titulo and ano):
                problemas.append(f"item {id_item}: falta nome do premio ou ano")
            anexar(dtd, raiz, tipo_item, elem)
            gerados.append({"id": id_item, "tipo": tipo_item, "titulo": titulo, "ano": ano})
            continue
        elem = montar_item(dtd, item, seq, avisos, problemas)
        if elem is None:
            continue
        nomes = [normalizar(p.get("nome", "")) for p in item.get("autores", [])]
        if nome_docente and item.get("autores") and nome_docente not in nomes:
            avisos.append(f"item {id_item}: o docente nao aparece com o nome completo do curriculo entre os autores")
        if dados.get("FLAG-DIVULGACAO-CIENTIFICA") == "SIM" and item["tipo"] == "ARTIGO-PUBLICADO":
            avisos.append(f"item {id_item}: a oficina orienta a nao marcar popularizacao em artigo cientifico")
        anexar(dtd, raiz, item["tipo"], elem)
        gerados.append({"id": id_item, "tipo": item["tipo"], "titulo": titulo, "ano": ano})

    ordenar(dtd, raiz)
    problemas += dtd.validar(raiz)
    relatorio = {
        "gerados": gerados, "nao_incluidos_pelo_pre_diff": duplicados,
        "nao_aprovados": ignorados, "avisos": sorted(set(avisos)), "problemas": sorted(set(problemas)),
    }
    print(json.dumps(relatorio, ensure_ascii=False, indent=1))
    if problemas:
        return erro("arquivo NAO gerado; corrija os problemas acima")
    if not gerados:
        return erro("nenhum item aprovado para gerar")
    if args.simular:
        print("Simulacao concluida: nenhum arquivo gravado.")
        return 0
    destino = Path(args.saida)
    if destino.exists() and destino.resolve() in {Path(args.base).resolve(), Path(args.plano).resolve()}:
        return erro("o destino nao pode ser o curriculo original nem o plano")
    cabecalho = '<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>\n'
    if not args.sem_doctype:
        cabecalho += '<!DOCTYPE CURRICULO-VITAE SYSTEM "LMPLCurriculo.dtd">\n'
    destino.write_bytes((cabecalho + serializar(raiz)).encode("iso-8859-1"))
    ET.fromstring(destino.read_bytes())
    print(f"Gerado: {destino} ({len(gerados)} itens; validado contra a DTD)")
    return 0


def cmd_comparar(args):
    plano = json.loads(Path(args.plano).read_text(encoding="utf-8"))
    existentes = itens_de(ler_cv(args.base))
    lote, linhas = [], []
    for item in plano.get("itens", []):
        resumo = resumo_item(item)
        resumos = resumos_do_item(item)
        res = next((d for d in (classificar(r, existentes) for r in resumos) if d["status"] != "NOVO"),
                   {"status": "NOVO", "motivo": "", "item": None, "diferencas": []})
        if res["status"] == "NOVO":
            no_lote = next((d for d in (classificar(r, lote) for r in resumos) if d["status"] != "NOVO"), None)
            if no_lote:
                res = {**no_lote, "status": "REPETIDO_NO_LOTE"}
        lote += resumos
        linhas.append({
            "id": str(item.get("id", "?")), "titulo": resumo["titulo"], "ano": resumo["ano"], "status": res["status"],
            "motivo": res["motivo"], "diferencas": res["diferencas"],
            "comparado_com": descrever(res["item"]) if res["item"] else "", "origem": item.get("origem", []),
        })
    print(json.dumps({"total": dict(Counter(l["status"] for l in linhas)), "itens": linhas},
                     ensure_ascii=False, indent=1))
    return 0


def identificar_cv(dados):
    """Dados do curriculo, se os bytes forem um XML do Lattes. So campos nao sensiveis."""
    if b"CURRICULO-VITAE" not in dados[:2048] or b"<!ENTITY" in dados[:4096]:
        return None
    try:
        raiz = ET.fromstring(dados)
    except ET.ParseError:
        return None
    if raiz.tag != "CURRICULO-VITAE":
        return None
    return {"id_lattes": raiz.get("NUMERO-IDENTIFICADOR", ""), "data_atualizacao": raiz.get("DATA-ATUALIZACAO", "")}


def catalogar_bytes(rel, dados):
    extensao = Path(rel).suffix.lower()
    registro = {"arquivo": rel, "extensao": extensao, "tamanho_kb": round(len(dados) / 1024, 1),
                "sha256": hashlib.sha256(dados).hexdigest()}
    if NOME_SENSIVEL.search(Path(rel).name):
        registro["categoria"] = "sensivel_nao_abrir"
    elif extensao == ".xml" and identificar_cv(dados):
        registro.update(categoria="curriculo_lattes", curriculo=identificar_cv(dados))
    elif extensao == ".zip":
        registro["categoria"] = "zip"
    elif extensao in EXTENSOES_DOCUMENTO or extensao == ".xml":
        registro["categoria"] = "documento"
    else:
        registro["categoria"] = "ignorado"
    return registro


def cv_em_zip(caminho):
    try:
        with zipfile.ZipFile(caminho) as zf:
            infos = zf.infolist()
            if len(infos) == 1 and infos[0].filename.lower().endswith(".xml") and infos[0].file_size <= LIMITE_XML:
                return identificar_cv(zf.read(infos[0]))
    except (zipfile.BadZipFile, OSError, RuntimeError):
        pass
    return None


def eh_assentamento(caminho):
    """O SouGov.br nomeia os arquivos como Documento_<numero>-<CODIGO>-<ano>.pdf."""
    try:
        with zipfile.ZipFile(caminho) as zf:
            nomes = [Path(n).name for n in zf.namelist() if not n.endswith("/")]
    except (zipfile.BadZipFile, OSError):
        return False
    return bool(nomes) and all(re.fullmatch(r"Documento_\d+-[A-Z]+-\d{4}\.pdf", n) for n in nomes)


def extrair_zip(origem, destino):
    """Extrai para uma pasta nova, recusando caminhos que escapem dela."""
    destino = Path(destino)
    if destino.exists() and any(destino.iterdir()):
        raise ValueError(f"a pasta de extracao precisa ser nova ou vazia: {destino}")
    with zipfile.ZipFile(origem) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        if len(infos) > LIMITE_ARQUIVOS or sum(i.file_size for i in infos) > 2 * 1024 ** 3:
            raise ValueError("ZIP grande demais para extrair")
        raiz = destino.resolve()
        alvos = []
        for info in infos:
            alvo = (raiz / info.filename).resolve()
            if raiz not in alvo.parents:
                raise ValueError(f"caminho inseguro no ZIP: {info.filename}")
            alvos.append((info, alvo))
        for info, alvo in alvos:
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_bytes(zf.read(info))
    return destino


def data_do_cv(registro):
    data = registro["curriculo"]["data_atualizacao"]
    return data[4:8] + data[2:4] + data[:2] if len(data) == 8 else ""


def cmd_pasta(args):
    origem = Path(args.caminho)
    if origem.is_file() and zipfile.is_zipfile(origem):
        if not args.extrair_em:
            raise ValueError("para ler um ZIP de comprovantes, informe --extrair-em PASTA_NOVA")
        origem = extrair_zip(origem, args.extrair_em)
    if not origem.is_dir():
        raise ValueError(f"pasta nao encontrada: {origem}")
    registros = []
    for caminho in sorted(origem.rglob("*")):
        rel = caminho.relative_to(origem).as_posix()
        if not caminho.is_file() or caminho.is_symlink() or any(p.startswith((".", "~$")) for p in rel.split("/")):
            continue
        if len(registros) >= LIMITE_ARQUIVOS:
            raise ValueError(f"mais de {LIMITE_ARQUIVOS} arquivos; divida a pasta")
        if caminho.stat().st_size > 200 * 1024 * 1024:
            registros.append({"arquivo": rel, "extensao": caminho.suffix.lower(), "categoria": "ignorado",
                              "observacao": "maior que 200 MB"})
            continue
        registro = catalogar_bytes(rel, caminho.read_bytes())
        if registro["categoria"] == "zip":
            cv = cv_em_zip(caminho)
            if cv:
                registro.update(categoria="curriculo_lattes", curriculo=cv)
            elif eh_assentamento(caminho):
                registro["categoria"] = "assentamento_funcional"
        registros.append(registro)
    vistos = {}
    for reg in registros:
        if reg.get("sha256") in vistos:
            reg["copia_identica_de"] = vistos[reg["sha256"]]
        elif reg.get("sha256"):
            vistos[reg["sha256"]] = reg["arquivo"]
    curriculos = [r for r in registros if r["categoria"] == "curriculo_lattes"]
    mais_recente = max(curriculos, key=data_do_cv)["arquivo"] if curriculos else ""
    a_ler = [r["arquivo"] for r in registros if r["categoria"] == "documento" and "copia_identica_de" not in r]
    lotes = [a_ler[i:i + args.tamanho_lote] for i in range(0, len(a_ler), args.tamanho_lote)]
    saida = {
        "pasta": str(origem), "totais": dict(Counter(r["categoria"] for r in registros)),
        "copias_identicas": sum(1 for r in registros if "copia_identica_de" in r),
        "curriculo_mais_recente": mais_recente,
        "ids_lattes": sorted({r["curriculo"]["id_lattes"] for r in curriculos}),
        "lotes_de_leitura": lotes, "arquivos": registros,
    }
    Path(args.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Catalogo gravado em {args.saida}")
    print(json.dumps({k: saida[k] for k in ("totais", "copias_identicas", "curriculo_mais_recente", "ids_lattes")},
                     ensure_ascii=False, indent=1))
    print(f"{len(a_ler)} documentos para ler em {len(lotes)} lotes.")
    return 0


def baixar_json(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "lattes-apcn-skill/1.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=25) as resposta:
            return json.loads(resposta.read(LIMITE_RESPOSTA))
    except urllib.error.HTTPError as exc:
        raise ValueError(f"{urllib.parse.urlsplit(url).netloc} respondeu {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"sem acesso a internet neste ambiente ({exc}); peca o dado ao docente")


def sem_tags(texto):
    return html.unescape(re.sub(r"<[^>]+>", "", texto or "")).strip()


def cmd_doi(args):
    doi = limpar_doi(args.doi)
    if not re.fullmatch(r"10\.\d{4,9}/\S+", doi):
        raise ValueError(f"DOI invalido: {args.doi}")
    obra = baixar_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""))["message"]
    data = (obra.get("issued") or {}).get("date-parts") or [[None]]
    paginas = (obra.get("page") or "").split("-")
    print(json.dumps({
        "fonte": "Crossref", "doi": doi, "tipo_crossref": obra.get("type", ""),
        "titulo": sem_tags((obra.get("title") or [""])[0]), "ano": data[0][0],
        "periodico_ou_livro": sem_tags((obra.get("container-title") or [""])[0]),
        "issn_por_meio": obra.get("issn-type") or obra.get("ISSN") or [], "isbn": obra.get("ISBN") or [],
        "volume": obra.get("volume", ""), "fasciculo": obra.get("issue", ""),
        "pagina_inicial": paginas[0], "pagina_final": paginas[-1] if len(paginas) > 1 else "",
        "editora": obra.get("publisher", ""), "idioma": obra.get("language", ""),
        "autores": [" ".join(x for x in (a.get("given"), a.get("family")) if x) or a.get("name", "")
                    for a in obra.get("author", [])],
    }, ensure_ascii=False, indent=1))
    return 0


def cmd_buscar(args):
    orcid = re.sub(r"^https?://orcid\.org/", "", args.orcid.strip())
    if not re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", orcid):
        raise ValueError(f"ORCID invalido: {args.orcid}")
    existentes = itens_de(ler_cv(args.base))
    url = ("https://api.openalex.org/works?per-page=200&select=doi,title,publication_year,type"
           f"&filter=author.orcid:https://orcid.org/{orcid}")
    resposta = baixar_json(url)
    candidatos, ja = [], 0
    for obra in resposta.get("results", []):
        resumo = {"tipo": "", "titulo": sem_tags(obra.get("title")), "titulo_ingles": "",
                  "ano": str(obra.get("publication_year") or ""), "doi": obra.get("doi") or "", "link": "", "pessoa": ""}
        if classificar(resumo, existentes)["status"] == "NOVO":
            candidatos.append({"titulo": resumo["titulo"], "ano": resumo["ano"], "doi": limpar_doi(resumo["doi"]),
                               "tipo_openalex": obra.get("type", "")})
        else:
            ja += 1
    print(json.dumps({
        "fonte": "OpenAlex", "total_na_base": (resposta.get("meta") or {}).get("count"), "ja_no_curriculo": ja,
        "candidatos_a_conferir": sorted(candidatos, key=lambda c: c["ano"], reverse=True),
    }, ensure_ascii=False, indent=1))
    return 0


# ------------------------------------------------- Assentamento Funcional Digital -------
# A ordem importa: o primeiro padrao que casa define a categoria da pagina.
CATEGORIAS_ASSENTAMENTO = (
    ("comissao_colegiado", r"comiss[aã]o[^.]{0,60}progress[aã]o"),
    ("progressao_promocao", r"progress[aã]o (funcional|por|de|na)|conced\w+ (a )?progress|promo[cç][aã]o (funcional|para|de classe|[aà] classe|por)"
                            r"|acelera[cç][aã]o da promo|promover .{0,120}classe"),
    ("rsc", r"reconhecimento de saberes"),
    ("retribuicao_titulacao", r"retribui[cç][aã]o por titula"),
    ("posse_nomeacao", r"termo de posse|\bnomear\b|entrada em exerc[ií]cio"),
    ("funcao", r"exercer a fun[cç][aã]o|dispensar .{0,120}fun[cç][aã]o"),
    ("comissao_colegiado", r"comiss[aã]o|colegiado|grupo de trabalho|\bGT\b|conselho|n[uú]cleo docente"),
    ("afastamento_licenca", r"afastamento|licen[cç]a (para|de) (capacita|qualifica|p[oó]s|estudo)"),
    ("redistribuicao_remocao", r"redistribui[cç][aã]o|remo[cç][aã]o"),
)
ATO_FORMAL = re.compile(r"\bresolve\b|termo de posse", re.I)
# Documento pessoal ou de rotina: a pagina e ignorada por inteiro, mesmo que cite portaria.
DOCUMENTO_PESSOAL = re.compile(
    r"dados banc[aá]rios|conta corrente|reservista|uni[aã]o est[aá]vel|tabelionato|certid[aã]o de (nascimento|casamento|quita)"
    r"|imposto de renda|atestado|f[eé]rias|aux[ií]lio|dependente|diploma|hist[oó]rico escolar|exame m[eé]dico|contrato de trabalho",
    re.I,
)
PAGINAS_DOCUMENTO_CURTO = 6
COMO_LANCAR = {
    "progressao_promocao": "Atuacao profissional > vinculo: novo bloco de enquadramento, citando a portaria em informacoes adicionais",
    "posse_nomeacao": "Atuacao profissional > vinculo: inicio do vinculo e primeiro bloco de enquadramento",
    "rsc": "Atuacao profissional > vinculo: citar em informacoes adicionais; nao muda classe nem nivel [Inferido]",
    "retribuicao_titulacao": "Atuacao profissional > vinculo: citar em informacoes adicionais; nao muda classe nem nivel [Inferido]",
    "funcao": "Atuacao profissional > atividade: Direcao e administracao [Inferido]",
    "comissao_colegiado": "Atuacao profissional > atividade: Conselhos, comissoes e consultoria",
    "afastamento_licenca": "Atuacao profissional > vinculo: bloco de licenca, sem sobrepor servidor; o que fez no periodo vai em atividade [Inferido]",
    "redistribuicao_remocao": "Atuacao profissional > vinculo: conferir instituicao e datas [Inferido]",
}


def mascarar_numeros(texto):
    texto = re.sub(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", "[CPF]", texto)
    texto = re.sub(r"(?i)(siape|matr[ií]cula)([^\d]{0,20})[\d'’. ]*\d", r"\1\2[N]", texto)
    return re.sub(r"\b\d{7,}\b", "[N]", texto)


def nome_na_pagina(nome, texto):
    """Compara primeiro e ultimo nome, tolerando erro de OCR. Evita pegar pagina de outro servidor."""
    alvo = normalizar(nome).split()
    if not alvo:
        return False
    palavras = set(normalizar(texto).split())
    return all(difflib.get_close_matches(p, palavras, n=1, cutoff=0.75) for p in (alvo[0], alvo[-1]))


def ler_evento(categoria, arquivo, pagina, texto):
    limpo = re.sub(r"\s+", " ", texto)
    numero = re.search(r"(?i)portaria[^\d]{0,40}(\d[\d.]{0,6}(?: ?/ ?\d{4})?)", limpo)
    carreira = re.search(r"(?i)classe\s+[A-E](?:\s?[IVX]+|\s?\d)?[^.;]{0,25}?n[ií]vel\s*\d+", limpo)
    data = re.search(r"(\d{1,2}) de (janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
                     r" de (\d{4})", limpo, re.I)
    efeitos = re.search(r"(?i)(a partir de|com efeitos? [^.]{0,30}?|a contar de) (\d{2}/\d{2}/\d{4})", limpo)
    inicio = re.search(r"(?i)\bresolve\b:?|termo de posse", limpo)
    trecho = limpo[inicio.start():] if inicio else limpo
    if categoria == "comissao_colegiado":  # A lista de membros traz nomes de terceiros.
        trecho = re.split(r"(?i)designando|seguintes (membros|servidores)", trecho)[0]
    return {
        "categoria": categoria, "como_lancar": COMO_LANCAR[categoria], "arquivo": arquivo, "pagina": pagina,
        "portaria": numero.group(1).replace(" ", "") if numero else "",
        "data_do_ato": " de ".join(data.groups()) if data else "",
        "efeitos_a_partir_de": efeitos.group(2) if efeitos else "",
        "classe_e_nivel": re.sub(r"\s+", " ", carreira.group(0)) if carreira else "",
        "trecho": mascarar_numeros(trecho[:320]),
    }


def resumir_vinculos(raiz):
    """Vinculos e comissoes ja lancados, para comparar com o assentamento."""
    vinculos, comissoes = [], []
    for atuacao in raiz.iterfind("DADOS-GERAIS/ATUACOES-PROFISSIONAIS/ATUACAO-PROFISSIONAL"):
        for v in atuacao.findall("VINCULOS"):
            if v.get("TIPO-DE-VINCULO") == "LIVRE" and "servidor" not in v.get("OUTRO-VINCULO-INFORMADO", "").lower():
                continue
            vinculos.append({
                "instituicao": atuacao.get("NOME-INSTITUICAO", ""),
                "vinculo": v.get("TIPO-DE-VINCULO", "") + (" " + v.get("OUTRO-VINCULO-INFORMADO", "")).rstrip(),
                "enquadramento": v.get("OUTRO-ENQUADRAMENTO-FUNCIONAL-INFORMADO") or v.get("ENQUADRAMENTO-FUNCIONAL", ""),
                "inicio": f"{v.get('MES-INICIO', '')}/{v.get('ANO-INICIO', '')}",
                "fim": f"{v.get('MES-FIM', '')}/{v.get('ANO-FIM', '')}".strip("/") or "atual",
                "cita_portaria": bool(re.search(r"(?i)portaria", v.get("OUTRAS-INFORMACOES", ""))),
            })
        for c in atuacao.iter("CONSELHO-COMISSAO-E-CONSULTORIA"):
            comissoes.append({"especificacao": c.get("ESPECIFICACAO", ""), "orgao": c.get("NOME-ORGAO", ""),
                              "inicio": c.get("ANO-INICIO", ""), "fim": c.get("ANO-FIM", "")})
    return {"vinculos": vinculos, "comissoes": comissoes}


def cmd_assentamento(args):
    try:
        import pypdf
    except ImportError:
        raise ValueError("este comando precisa de pypdf. Instale com: python -m pip install pypdf")
    import logging
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    base = ler_cv(args.base) if args.base else None
    nome = args.nome or (base.find("DADOS-GERAIS").get("NOME-COMPLETO", "") if base is not None else "")
    if not nome:
        raise ValueError("informe --nome ou --base: o nome filtra as paginas de outros servidores")
    padroes = [(c, re.compile(r, re.I)) for c, r in CATEGORIAS_ASSENTAMENTO]
    eventos, documentos = [], []
    with zipfile.ZipFile(args.zip) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        if sum(i.file_size for i in infos) > 2 * 1024 ** 3:
            raise ValueError("ZIP grande demais")
        for info in infos:
            registro = {"arquivo": info.filename, "paginas": 0, "paginas_sem_texto": 0, "eventos": 0}
            documentos.append(registro)
            if not info.filename.lower().endswith(".pdf"):
                registro["situacao"] = "nao e PDF; nao aberto"
                continue
            try:
                leitor = pypdf.PdfReader(io.BytesIO(zf.read(info)))
                paginas = [(pag.extract_text() or "") for pag in leitor.pages]
            except Exception:
                registro["situacao"] = "nao foi possivel ler"
                continue
            registro["paginas"] = len(paginas)
            registro["paginas_sem_texto"] = sum(1 for t in paginas if len(t.strip()) < 40)
            # Em documento curto o ato ocupa o arquivo todo: o nome costuma estar em outra pagina que o "resolve".
            trechos = [(1, " ".join(paginas))] if len(paginas) <= PAGINAS_DOCUMENTO_CURTO else list(enumerate(paginas, 1))
            for numero, texto in trechos:
                texto = re.sub(r"\s+", " ", texto)  # Quebras de linha nao podem esconder as expressoes.
                if len(texto.strip()) < 40 or DOCUMENTO_PESSOAL.search(texto[:600]):
                    continue
                if not ATO_FORMAL.search(texto) or not nome_na_pagina(nome, texto):
                    continue
                categoria = next((c for c, rx in padroes if rx.search(texto)), None)
                if categoria:
                    eventos.append(ler_evento(categoria, info.filename, numero, texto))
                    registro["eventos"] += 1
            registro["situacao"] = "com eventos" if registro["eventos"] else "sem carreira nem portaria do docente"
    unicos, vistos = [], set()
    for ev in eventos:  # O mesmo ato costuma aparecer mais de uma vez no assentamento antigo.
        chave = (ev["categoria"], ev["portaria"], ev["data_do_ato"], ev["trecho"][:80])
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(ev)
    saida = {
        "totais": dict(Counter(e["categoria"] for e in unicos)),
        "tem_progressao_ou_promocao": any(e["categoria"] == "progressao_promocao" for e in unicos),
        "paginas_sem_texto": sum(d["paginas_sem_texto"] for d in documentos),
        "eventos": unicos, "documentos": documentos,
    }
    if base is not None:
        saida["curriculo"] = resumir_vinculos(base)
    Path(args.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Resultado gravado em {args.saida}")
    print(json.dumps({k: saida[k] for k in ("totais", "tem_progressao_ou_promocao", "paginas_sem_texto")}, ensure_ascii=False))
    print(f"{len(documentos)} arquivos no ZIP; {sum(1 for d in documentos if d['eventos'])} com eventos.")
    return 0


def cmd_validar(args):
    raiz = ler_cv(args.xml)
    problemas = DTD().validar(raiz)
    if not problemas:
        print("Valido contra a DTD.")
        return 0
    for problema, qtde in Counter(problemas).most_common():
        print(f"{qtde:4d}  {problema}")
    print(f"{len(problemas)} problemas.")
    return 1


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("tipos").set_defaults(func=cmd_tipos)
    p = sub.add_parser("campos")
    p.add_argument("tipo")
    p.set_defaults(func=cmd_campos)
    p = sub.add_parser("inventario")
    p.add_argument("cv")
    p.add_argument("--saida")
    p.set_defaults(func=cmd_inventario)
    p = sub.add_parser("gerar")
    p.add_argument("plano")
    p.add_argument("--base", required=True, help="curriculo atual (.xml ou .zip)")
    p.add_argument("--saida", help="arquivo .xml de importacao")
    p.add_argument("--simular", action="store_true", help="confere tudo sem gravar")
    p.add_argument("--somente", help="ids separados por virgula, para um teste pequeno")
    p.add_argument("--excluir", help="ids separados por virgula, para gerar o restante depois do teste")
    p.add_argument("--sem-doctype", action="store_true")
    p.set_defaults(func=cmd_gerar)
    p = sub.add_parser("validar")
    p.add_argument("xml")
    p.set_defaults(func=cmd_validar)
    p = sub.add_parser("comparar")
    p.add_argument("plano")
    p.add_argument("--base", required=True)
    p.set_defaults(func=cmd_comparar)
    p = sub.add_parser("pasta")
    p.add_argument("caminho", help="pasta ou ZIP com os comprovantes")
    p.add_argument("--saida", required=True)
    p.add_argument("--extrair-em", help="pasta nova para extrair o ZIP")
    p.add_argument("--tamanho-lote", type=int, default=10)
    p.set_defaults(func=cmd_pasta)
    p = sub.add_parser("doi")
    p.add_argument("doi")
    p.set_defaults(func=cmd_doi)
    p = sub.add_parser("assentamento")
    p.add_argument("zip", help="ZIP baixado do SouGov.br")
    p.add_argument("--nome", help="nome do servidor, para ignorar paginas de outras pessoas")
    p.add_argument("--base", help="curriculo atual, para comparar vinculos e comissoes")
    p.add_argument("--saida", required=True)
    p.set_defaults(func=cmd_assentamento)
    p = sub.add_parser("buscar")
    p.add_argument("--orcid", required=True)
    p.add_argument("--base", required=True)
    p.set_defaults(func=cmd_buscar)
    args = parser.parse_args()
    if args.comando == "gerar" and not args.simular and not args.saida:
        parser.error("informe --saida ou use --simular")
    try:
        return args.func(args)
    except (ValueError, ET.ParseError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        return erro(str(exc))


if __name__ == "__main__":
    sys.exit(main())
