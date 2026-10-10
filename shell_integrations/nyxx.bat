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
    echo nyxx: python not found at "%NYXX_PYTHON_BIN%"
    goto :eof
)

set "NYXX_ACTION_FILE=%USERPROFILE%\.nyxx\action"
rem Clear anything an earlier run left behind (e.g. Nyxx.exe started from
rem the Start menu) so only this run's action gets acted on below.
del "%NYXX_ACTION_FILE%" >nul 2>&1

set "NYXX_OLD_CWD=%NYXX_CWD%"
set "NYXX_CWD=%CD%"
set "NYXX_OLD_PYTHONPATH=%PYTHONPATH%"
set "PYTHONPATH=%NYXX_SCRIPT_DIR%"

"%NYXX_PYTHON_BIN%" -m src.nyxx.main %*

set "PYTHONPATH=%NYXX_OLD_PYTHONPATH%"
set "NYXX_CWD=%NYXX_OLD_CWD%"
set "NYXX_OLD_PYTHONPATH="
set "NYXX_OLD_CWD="

if not exist "%NYXX_ACTION_FILE%" goto :cleanup

rem Nyxx writes the action file as UTF-8. Read it under code page 65001
rem so non-ASCII paths come through intact, then put the old one back.
set "NYXX_OLD_CP="
for /f "tokens=2 delims=:." %%c in ('chcp') do set "NYXX_OLD_CP=%%c"
if defined NYXX_OLD_CP chcp 65001 >nul
set "NYXX_ACTION="
set /p NYXX_ACTION=<"%NYXX_ACTION_FILE%"
if defined NYXX_OLD_CP chcp %NYXX_OLD_CP% >nul
del "%NYXX_ACTION_FILE%" >nul 2>&1

rem Dispatch with goto rather than inside ( ... ) blocks: cmd expands
rem %NYXX_ACTION% before it parses a block, so a ")" in the path or
rem command (e.g. "C:\Program Files (x86)") would end the block early.
if "%NYXX_ACTION:~0,3%"=="CD:" goto :nyxx_cd
if "%NYXX_ACTION:~0,5%"=="EXEC:" goto :nyxx_exec
echo nyxx: unexpected action: "%NYXX_ACTION%"
goto :cleanup

:nyxx_cd
cd /d "%NYXX_ACTION:~3%" 2>nul || echo nyxx: cd failed: "%NYXX_ACTION:~3%"
goto :cleanup

:nyxx_exec
call %NYXX_ACTION:~5%

:cleanup
set "NYXX_ACTION="
set "NYXX_ACTION_FILE="
set "NYXX_OLD_CP="
