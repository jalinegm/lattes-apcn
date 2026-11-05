#!/bin/sh
# Baixa a ultima versao publicada da skill lattes-apcn e instala.
URL="https://github.com/jalinegm/lattes-apcn/releases/latest/download/lattes-apcn-instalador.zip"
PASTA="$(mktemp -d)" || exit 1
trap 'rm -rf "$PASTA"' EXIT
echo "Atualizando a skill lattes-apcn. Aguarde..."
if [ -n "$LATTES_APCN_ZIP_TESTE" ]; then
  cp "$LATTES_APCN_ZIP_TESTE" "$PASTA/pacote.zip" || exit 1
elif ! curl -fsSL "$URL" -o "$PASTA/pacote.zip"; then
  echo "ERRO: nao foi possivel baixar a atualizacao. Confira a internet e tente de novo."
  exit 1
fi
if ! unzip -q "$PASTA/pacote.zip" -d "$PASTA/extraido" || [ ! -f "$PASTA/extraido/instalar-mac-linux.sh" ]; then
  echo "ERRO: o arquivo baixado esta incompleto. Avise quem enviou o comando."
  exit 1
fi
sh "$PASTA/extraido/instalar-mac-linux.sh"
