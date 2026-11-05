#!/usr/bin/env python3
"""Gera em dist/ os arquivos publicados em cada release da skill."""
import shutil
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SKILL = RAIZ / "lattes-apcn"
DIST = RAIZ / "dist"
ACOMPANHAM_O_INSTALADOR = ("README.md", "COMO-ATUALIZAR.md", "INSTALAR-Windows.bat", "instalar-mac-linux.sh")
PUBLICADOS_SOLTOS = ("ATUALIZAR-Windows.bat", "atualizar-mac-linux.sh")


def adicionar_skill(zf):
    arquivos = [SKILL] + sorted(p for p in SKILL.rglob("*") if "__pycache__" not in p.parts and p.suffix != ".pyc")
    for caminho in arquivos:
        nome = caminho.relative_to(RAIZ).as_posix()
        if caminho.is_dir():
            zf.writestr(nome + "/", "")
        else:
            zf.write(caminho, nome)


def main():
    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(DIST / "lattes-apcn.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        adicionar_skill(zf)
    with zipfile.ZipFile(DIST / "lattes-apcn-instalador.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        adicionar_skill(zf)
        for nome in ACOMPANHAM_O_INSTALADOR:
            zf.write(RAIZ / nome, nome)
    for nome in PUBLICADOS_SOLTOS:
        shutil.copy2(RAIZ / nome, DIST / nome)
    versao = (SKILL / "VERSAO.txt").read_text(encoding="utf-8").strip()
    print(f"Versao {versao} gerada em {DIST}:")
    for caminho in sorted(DIST.iterdir()):
        print(f"  {caminho.name}")


if __name__ == "__main__":
    main()
