@echo off
setlocal

REM -------------------------------------------------
REM Resolve base path (same as %~dp0)
REM -------------------------------------------------
set "BASEPATH=%~dp0"
cd /d "%BASEPATH%"

wt ^
  new-tab -p "Command Prompt" --title "TTS Stack" cmd /k "cd /d %BASEPATH% && py scripts/tts_server.py" ^
  ; split-pane -V cmd /k "cd /d %BASEPATH% && py scripts/redeem_listener.py"
