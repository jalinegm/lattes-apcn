@echo off
setlocal
set "ORIGEM=%~dp0lattes-apcn"
if not exist "%ORIGEM%\SKILL.md" (
  echo ERRO: pasta lattes-apcn nao encontrada ao lado deste arquivo.
  echo Extraia o ZIP inteiro antes de executar.
  pause
  exit /b 1
)
echo Instalando a skill lattes-apcn...
for %%D in ("%USERPROFILE%\.claude\skills" "%USERPROFILE%\.agents\skills") do (
  if not exist "%%~D" mkdir "%%~D"
  if exist "%%~D\lattes-apcn" rmdir /s /q "%%~D\lattes-apcn"
  xcopy "%ORIGEM%" "%%~D\lattes-apcn\" /e /i /q /y >nul
  echo   OK: %%~D\lattes-apcn
)
echo.
echo Pronto. Feche e abra de novo o Claude Code ou o Codex.
echo Teste perguntando: "Onde cadastro uma cartilha no Lattes?"
pause
