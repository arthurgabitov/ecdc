@echo off
REM 
REM 
REM 

REM
set "UTILS_DIR=%~dp0"
REM
for %%I in ("%UTILS_DIR%..\") do set "PORTABLE_ROOT=%%~fI"

REM
if "%PORTABLE_ROOT:~-1%"=="\" set "PORTABLE_ROOT=%PORTABLE_ROOT:~0,-1%"

REM === Запись переменных напрямую через reg add ===
reg add "HKLM\SOFTWARE\WOW6432Node\FANUC" /v InstallDir /t REG_SZ /d "%PORTABLE_ROOT%\utils" /f
reg add "HKLM\SOFTWARE\WOW6432Node\FANUC\ROBOGUIDE" /v BasePath /t REG_SZ /d "%PORTABLE_ROOT%\utils\\" /f
reg add "HKLM\SOFTWARE\WOW6432Node\FANUC\ROBOGUIDE\bin" /v Path /t REG_SZ /d "%PORTABLE_ROOT%\utils\ROBOGUIDE\bin" /f

REM 
set "REGSVR32=%SystemRoot%\SysWOW64\regsvr32.exe"
for %%f in ("%PORTABLE_ROOT%\utils\WinOLPC\bin\*.dll") do %REGSVR32% /s "%%f"
for %%f in ("%PORTABLE_ROOT%\utils\ROBOGUIDE\bin\*.dll") do %REGSVR32% /s "%%f"
for %%f in ("%PORTABLE_ROOT%\utils\Shared\Utilities\*.dll") do %REGSVR32% /s "%%f"
for %%f in ("%PORTABLE_ROOT%\utils\WinOLPC\Versions\V930-1\bin\*.dll") do %REGSVR32% /s "%%f"
for %%f in ("%PORTABLE_ROOT%\utils\WinOLPC\Versions\V940-1\bin\*.dll") do %REGSVR32% /s "%%f"

echo === Done ===
pause
