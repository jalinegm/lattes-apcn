#!/bin/sh
# Instala a skill lattes-apcn para Claude Code e Codex.
cd "$(dirname "$0")" || exit 1
if [ ! -f lattes-apcn/SKILL.md ]; then
  echo "ERRO: pasta lattes-apcn nao encontrada ao lado deste arquivo. Extraia o ZIP inteiro."
  exit 1
fi
echo "Instalando a skill lattes-apcn, versao $(cat lattes-apcn/VERSAO.txt)..."
for d in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  mkdir -p "$d"
  rm -rf "$d/lattes-apcn"
  cp -R lattes-apcn "$d/lattes-apcn"
  echo "  OK: $d/lattes-apcn"
done
echo
echo "Conferindo o Python, usado para ler o curriculo e o assentamento..."
if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
  if python3 -m pip install --user --quiet --disable-pip-version-check pypdf >/dev/null 2>&1; then
    echo "  OK: Python pronto."
  else
    echo "  Aviso: nao foi possivel instalar o componente pypdf."
    echo "  Tudo funciona, exceto a leitura do Assentamento Funcional Digital."
  fi
else
  echo "  O Python nao esta instalado. Sem ele, a analise de materiais funciona,"
  echo "  mas as opcoes com o XML do Lattes nao. Instale pelo site python.org."
fi
echo
echo "Pronto. Feche e abra de novo o Claude Code ou o Codex."
echo 'Teste perguntando: "Onde cadastro uma cartilha no Lattes?"'
