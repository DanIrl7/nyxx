@echo off
rem The `nyxx` command for Command Prompt (cmd.exe), as installed to
rem {app}\shims by setup_script.iss. That folder goes on PATH ahead of
rem {app}, so typing `nyxx` runs this script rather than Nyxx.exe itself.
rem
rem cmd.exe runs a .bat file typed at the prompt in the SAME process, so
rem this script can `cd` the calling prompt directly. Nyxx writes what it
rem wants done to %%USERPROFILE%%\.nyxx\action as "CD:<path>" or
rem "EXEC:<cmd>"; this script runs Nyxx, then reads that file and acts
rem on it here, in the actual interactive shell.

set "NYXX_ACTION_FILE=%USERPROFILE%\.nyxx\action"
rem Clear anything an earlier run left behind (e.g. Nyxx.exe started from
rem the Start menu) so only this run's action gets acted on below.
del "%NYXX_ACTION_FILE%" >nul 2>&1

"%~dp0..\Nyxx.exe" %*

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
