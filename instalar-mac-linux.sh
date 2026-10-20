#!/bin/sh
# Instala a skill lattes-apcn para Claude Code e Codex.
cd "$(dirname "$0")" || exit 1
if [ ! -f lattes-apcn/SKILL.md ]; then
  echo "ERRO: pasta lattes-apcn nao encontrada ao lado deste arquivo. Extraia o ZIP inteiro."
  exit 1
fi
for d in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  mkdir -p "$d"
  rm -rf "$d/lattes-apcn"
  cp -R lattes-apcn "$d/lattes-apcn"
  echo "  OK: $d/lattes-apcn"
done
echo
echo "Pronto. Feche e abra de novo o Claude Code ou o Codex."
echo 'Teste perguntando: "Onde cadastro uma cartilha no Lattes?"'
