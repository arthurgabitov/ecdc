@echo off
REM 
REM 
REM 
REM 
set "UTILS_DIR=%~dp0"
set "PORTABLE_ROOT=%UTILS_DIR%..\.."

REM 
for %%D in ("%PORTABLE_ROOT%\utils\WinOLPC\bin" "%PORTABLE_ROOT%\utils\ROBOGUIDE\bin" "%PORTABLE_ROOT%\utils\Shared\Utilities") do (
    if exist %%D (
        for %%F in (%%D\*.dll) do (
            if exist "%%F" (
                echo Unregistering %%F
                regsvr32 /u /s "%%F"
            )
        )
    )
)

REM Восстановление из reg_1 и reg_2
if exist "%UTILS_DIR%reg_1.reg" (
    echo Restoring registry from reg_1.reg
    reg import "%UTILS_DIR%reg_1.reg"
) else (
    echo No reg_1.reg found in utils.
)

if exist "%UTILS_DIR%reg_2.reg" (
    echo Restoring registry from reg_2.reg
    reg import "%UTILS_DIR%reg_2.reg"
) else (
    echo No reg_2.reg found in utils.
)

echo.
echo complete.
pause
