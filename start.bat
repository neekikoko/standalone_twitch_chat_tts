@echo off
setlocal EnableDelayedExpansion

set "BASEPATH=%~dp0"
cd /d "%BASEPATH%"

if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" if not "%%A:~0,1%%"=="#" (
            set "%%A=%%B"
        )
    )
)

set "START_VOICEVOX=!START_VOICEVOX!"
if /I "!START_VOICEVOX!"=="true" (
    set "RUN_VOICEVOX=1"
) else (
    set "RUN_VOICEVOX=0"
)

set "VOICEVOX_EXE=!VOICEVOX_INSTALL_LOCATION!\vv-engine\run.exe"

if "!RUN_VOICEVOX!"=="1" (

    wt ^
      new-tab -p "Command Prompt" --title "VOICEVOX" cmd /k "cd /d !BASEPATH! && \"!VOICEVOX_EXE!\"" ^
      ; new-tab -p "Command Prompt" --title "TTS Server" cmd /k "cd /d !BASEPATH! && py scripts/tts_server.py" ^
      ; split-pane -V cmd /k "cd /d !BASEPATH! && py scripts/redeem_listener.py"

) else (

    wt ^
      new-tab -p "Command Prompt" --title "TTS Server" cmd /k "cd /d !BASEPATH! && py scripts/tts_server.py" ^
      ; split-pane -V cmd /k "cd /d !BASEPATH! && py scripts/redeem_listener.py"

)

endlocal
