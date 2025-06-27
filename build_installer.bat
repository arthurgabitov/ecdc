@echo off
REM Сборка установщика Station App через Inno Setup
REM Убедитесь, что ISCC.exe (Inno Setup Compiler) добавлен в PATH или укажите полный путь к ISCC.exe ниже

set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6"
set "PATH=%INNO_PATH%;%PATH%"

ISCC StationApp_Setup.iss

pause
