@echo off
setlocal
title Atualizar a skill lattes-apcn
echo Atualizando a skill lattes-apcn. Aguarde...
echo.
set "URL=https://github.com/jalinegm/lattes-apcn/releases/latest/download/lattes-apcn-instalador.zip"
set "PASTA=%TEMP%\lattes-apcn-%RANDOM%%RANDOM%"
mkdir "%PASTA%"

if defined LATTES_APCN_ZIP_TESTE (
  copy /y "%LATTES_APCN_ZIP_TESTE%" "%PASTA%\pacote.zip" >nul
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -Uri '%URL%' -OutFile '%PASTA%\pacote.zip' -UseBasicParsing"
)
if not exist "%PASTA%\pacote.zip" goto falha_download

powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%PASTA%\pacote.zip' -DestinationPath '%PASTA%\extraido' -Force"
if not exist "%PASTA%\extraido\INSTALAR-Windows.bat" goto falha_download

call "%PASTA%\extraido\INSTALAR-Windows.bat"
rmdir /s /q "%PASTA%" 2>nul
exit /b 0

:falha_download
echo.
echo ERRO: nao foi possivel baixar a atualizacao.
echo Confira a internet e tente de novo. Se continuar, avise quem enviou este arquivo.
rmdir /s /q "%PASTA%" 2>nul
echo.
pause
exit /b 1
