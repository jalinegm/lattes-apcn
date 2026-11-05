@echo off
setlocal
set "ORIGEM=%~dp0lattes-apcn"
if not exist "%ORIGEM%\SKILL.md" (
  echo ERRO: pasta lattes-apcn nao encontrada ao lado deste arquivo.
  echo Extraia o ZIP inteiro antes de executar.
  pause
  exit /b 1
)
set /p VERSAO=<"%ORIGEM%\VERSAO.txt"
echo Instalando a skill lattes-apcn, versao %VERSAO%...
set "FALHOU="
for %%D in ("%USERPROFILE%\.claude\skills" "%USERPROFILE%\.agents\skills") do (
  if not exist "%%~D" mkdir "%%~D"
  if exist "%%~D\lattes-apcn" rmdir /s /q "%%~D\lattes-apcn"
  xcopy "%ORIGEM%" "%%~D\lattes-apcn\" /e /i /q /y >nul
  if exist "%%~D\lattes-apcn\SKILL.md" (
    echo   OK: %%~D\lattes-apcn
  ) else (
    echo   ERRO: nao foi possivel copiar para %%~D
    set "FALHOU=1"
  )
)
if defined FALHOU (
  echo.
  echo Feche o Claude Code e o Codex e execute este arquivo de novo.
  pause
  exit /b 1
)

echo.
echo Conferindo o Python, usado para ler o curriculo e o assentamento...
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if defined PY goto tem_python

echo.
echo O Python nao esta instalado neste computador.
echo Sem ele, a analise de materiais funciona, mas as opcoes com o XML do Lattes nao.
where winget >nul 2>&1
if errorlevel 1 goto sem_winget
choice /C SN /M "Deseja instalar o Python agora"
if not "%ERRORLEVEL%"=="1" goto fim
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
echo.
echo Depois de terminar, execute este arquivo mais uma vez para concluir.
goto fim

:sem_winget
echo Instale pelo site python.org e execute este arquivo mais uma vez.
goto fim

:tem_python
%PY% -m pip install --user --quiet --disable-pip-version-check pypdf >nul 2>&1
if errorlevel 1 (
  echo   Aviso: nao foi possivel instalar o componente pypdf.
  echo   Tudo funciona, exceto a leitura do Assentamento Funcional Digital.
) else (
  echo   OK: Python pronto.
)

:fim
echo.
echo Pronto. Feche e abra de novo o Claude Code ou o Codex.
echo Teste perguntando: "Onde cadastro uma cartilha no Lattes?"
pause
