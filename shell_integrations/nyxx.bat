@echo off
rem Nyxx shell integration for Command Prompt (cmd.exe).
rem
rem Save this file on your PATH as nyxx.bat, then update NYXX_SCRIPT_DIR
rem below to match your actual install path.
rem
rem Unlike PowerShell or Bash, cmd.exe runs a .bat file typed at the
rem prompt in the SAME process rather than spawning a child shell for
rem it — so this plain script can `cd` the calling prompt directly; it
rem doesn't need to be wired into a profile as a function the way the
rem PowerShell/Bash versions do.
rem
rem Python can't change its parent shell's working directory or run a
rem command in it directly, so instead of doing that itself, Nyxx writes
rem what it wants done to %%USERPROFILE%%\.nyxx\action as "CD:<path>" or
rem "EXEC:<cmd>". This script runs Nyxx, then reads that file and acts
rem on it here, in the actual interactive shell.

set "NYXX_SCRIPT_DIR=C:\path\to\nyxx"
set "NYXX_PYTHON_BIN=%NYXX_SCRIPT_DIR%\.venv\Scripts\python.exe"

if not exist "%NYXX_PYTHON_BIN%" (
    echo nyxx: python not found at %NYXX_PYTHON_BIN%
    goto :eof
)

set "NYXX_OLD_CWD=%NYXX_CWD%"
set "NYXX_CWD=%CD%"
set "NYXX_OLD_PYTHONPATH=%PYTHONPATH%"
set "PYTHONPATH=%NYXX_SCRIPT_DIR%"

"%NYXX_PYTHON_BIN%" -m src.nyxx.main %*

set "PYTHONPATH=%NYXX_OLD_PYTHONPATH%"
set "NYXX_CWD=%NYXX_OLD_CWD%"
set "NYXX_OLD_PYTHONPATH="
set "NYXX_OLD_CWD="

set "NYXX_ACTION_FILE=%USERPROFILE%\.nyxx\action"
if not exist "%NYXX_ACTION_FILE%" goto :eof

set "NYXX_ACTION="
set /p NYXX_ACTION=<"%NYXX_ACTION_FILE%"
del "%NYXX_ACTION_FILE%" >nul 2>&1

if "%NYXX_ACTION:~0,3%"=="CD:" (
    cd /d "%NYXX_ACTION:~3%" 2>nul || echo nyxx: cd failed: %NYXX_ACTION:~3%
    goto :cleanup
)

if "%NYXX_ACTION:~0,5%"=="EXEC:" (
    call %NYXX_ACTION:~5%
    goto :cleanup
)

echo nyxx: unexpected action: %NYXX_ACTION%

:cleanup
set "NYXX_ACTION="
set "NYXX_ACTION_FILE="
