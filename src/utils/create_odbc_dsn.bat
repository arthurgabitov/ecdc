@echo off
setlocal enabledelayedexpansion
REM Create 64-bit ODBC DSN CNC_HW_Details_id for SQL Server
REM Run as administrator!

echo %DATE% %TIME% > "%TEMP%\odbc_dsn_setup.log"

REM Verify that we're running on a 64-bit system
if not defined ProgramFiles(x86) (
    echo ERROR: This script requires a 64-bit Windows system >> "%TEMP%\odbc_dsn_setup.log"
    echo ERROR: This script requires a 64-bit Windows system.
    exit /b 2
)

echo Running on 64-bit Windows system >> "%TEMP%\odbc_dsn_setup.log"

set DSN_NAME=CNC_HW_Details_id
set DESCRIPTION=CNC_HW_Details_id
set SERVER=db-cnc-hw-details
set DB=master
set DRIVER_NAME=SQL Server

REM Auto-detect SQL Server driver path
echo Searching for SQL Server ODBC driver... >> "%TEMP%\odbc_dsn_setup.log"

REM Check common SQL Server driver locations
set DRIVER_PATH=
set DRIVER_KEY=

REM First check for the standard SQL Server driver (which is what we want)
echo Looking for standard SQL Server driver... >> "%TEMP%\odbc_dsn_setup.log"

REM Try registry lookup for SQL Server driver path
set "REG_KEY="
reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\SQL Server" /v Driver /reg:64 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\SQL Server" /v Driver /reg:64 ^| find "Driver"') do set "REG_KEY=%%b"
)

if not "!REG_KEY!"=="" (
    echo Found SQL Server driver in registry: !REG_KEY! >> "%TEMP%\odbc_dsn_setup.log"
    set "DRIVER_PATH=!REG_KEY!"
    set "DRIVER_NAME=SQL Server"
    set "DRIVER_KEY={SQL Server}"
    goto :DRIVER_FOUND
)

REM Check common paths for SQL Server driver
if exist "C:\Windows\System32\sqlsrv32.dll" (
    set "DRIVER_PATH=C:\Windows\System32\sqlsrv32.dll"
    set "DRIVER_NAME=SQL Server"
    set "DRIVER_KEY={SQL Server}"
    echo Found standard SQL Server driver: !DRIVER_PATH! >> "%TEMP%\odbc_dsn_setup.log"
    goto :DRIVER_FOUND
)

REM If standard driver not found, check for other SQL Server drivers
echo Standard SQL Server driver not found, checking alternatives... >> "%TEMP%\odbc_dsn_setup.log"

REM Try to find SQL Server Native Client drivers (check several versions)
FOR %%v IN (11.0 10.0) DO (
    if exist "C:\Windows\System32\sqlncli%%v.dll" (
        set "DRIVER_PATH=C:\Windows\System32\sqlncli%%v.dll"
        set "DRIVER_NAME=SQL Server Native Client %%v"
        set "DRIVER_KEY={SQL Server Native Client %%v}"
        echo Found SQL Native Client %%v: !DRIVER_PATH! >> "%TEMP%\odbc_dsn_setup.log"
        goto :DRIVER_FOUND
    )
)

REM Check for ODBC Driver for SQL Server
FOR %%v IN (17 13 11) DO (
    if exist "C:\Windows\System32\msodbcsql%%v.dll" (
        set "DRIVER_PATH=C:\Windows\System32\msodbcsql%%v.dll"
        set "DRIVER_NAME=ODBC Driver %%v for SQL Server"
        set "DRIVER_KEY={ODBC Driver %%v for SQL Server}"
        echo Found ODBC Driver %%v: !DRIVER_PATH! >> "%TEMP%\odbc_dsn_setup.log"
        goto :DRIVER_FOUND
    )
)

echo ERROR: SQL Server ODBC driver not found >> "%TEMP%\odbc_dsn_setup.log"
echo ERROR: SQL Server ODBC driver not found. Installation cannot continue.
exit /b 1

:DRIVER_FOUND
echo Using SQL Server driver: %DRIVER_NAME% (%DRIVER_PATH%) >> "%TEMP%\odbc_dsn_setup.log"

REM Use 64-bit registry path explicitly
echo Adding 64-bit ODBC DSN configuration... >> "%TEMP%\odbc_dsn_setup.log"

REM For 64-bit ODBC on a 64-bit system
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v Description /t REG_SZ /d "%DESCRIPTION%" /f /reg:64
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v Server /t REG_SZ /d "%SERVER%" /f /reg:64
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v Trusted_Connection /t REG_SZ /d "Yes" /f /reg:64
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v Database /t REG_SZ /d "%DB%" /f /reg:64
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v QuotedId /t REG_SZ /d "Yes" /f /reg:64
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v AnsiNPW /t REG_SZ /d "Yes" /f /reg:64
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v Translate /t REG_SZ /d "Yes" /f /reg:64
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v Language /t REG_SZ /d "English" /f /reg:64
reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources" /v %DSN_NAME% /t REG_SZ /d "SQL Server" /f /reg:64

REM If using SQL Server driver, use the SQL Server name for compatibility
if "%DRIVER_NAME%"=="SQL Server" (
    reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v Driver /t REG_SZ /d "%DRIVER_PATH%" /f /reg:64
) else (
    echo WARNING: Using non-standard driver: %DRIVER_NAME% >> "%TEMP%\odbc_dsn_setup.log"
    reg add "HKLM\SOFTWARE\ODBC\ODBC.INI\%DSN_NAME%" /v Driver /t REG_SZ /d "%DRIVER_PATH%" /f /reg:64
)

echo 64-bit ODBC DSN %DSN_NAME% created for server %SERVER% with classic SQL Server driver.
