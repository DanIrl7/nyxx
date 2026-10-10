# Nyxx shell integration for PowerShell.
#
# Copy the nyxx function below into your PowerShell profile ($PROFILE),
# then update $projectRoot to match your actual install path.
#
# Python can't change its parent shell's working directory or run a
# command in it directly, so instead of doing that itself, Nyxx writes
# what it wants done to ~/.nyxx/action as "CD:<path>" or "EXEC:<cmd>".
# This wrapper runs Nyxx, then reads that file and acts on it here, in
# the actual interactive shell.
function nyxx {
    $projectRoot = "C:\path\to\nyxx"
    $pythonExecutable = Join-Path $projectRoot ".venv\Scripts\python.exe"

    if (-not (Test-Path -LiteralPath $pythonExecutable)) {
        Write-Host "nyxx: python not found at $pythonExecutable"
        return
    }

    # Same place Python resolves ~/.nyxx to on Windows.
    $actionFile = Join-Path $env:USERPROFILE ".nyxx\action"
    # Clear anything an earlier run left behind (e.g. Nyxx.exe started from
    # the Start menu) so only this run's action gets acted on below.
    Remove-Item -LiteralPath $actionFile -ErrorAction SilentlyContinue

    $oldPath    = $env:PYTHONPATH
    $oldCwd     = $env:NYXX_CWD
    $env:PYTHONPATH = $projectRoot
    $env:NYXX_CWD   = (Get-Location).Path      # ← pass current directory

    & $pythonExecutable -m src.nyxx.main @args

    $env:PYTHONPATH = $oldPath
    $env:NYXX_CWD   = $oldCwd

    if (Test-Path -LiteralPath $actionFile) {
        # -Encoding UTF8: Nyxx writes UTF-8 without a BOM, which Windows
        # PowerShell 5.1 would otherwise read as ANSI, garbling any
        # non-ASCII characters in the path.
        $action = (Get-Content -LiteralPath $actionFile -Raw -Encoding UTF8).Trim()
        Remove-Item -LiteralPath $actionFile
        if ($action -match "^CD:(.*)") {
            # -LiteralPath: folder names can contain [ ], which -Path
            # would treat as wildcards.
            Set-Location -LiteralPath $Matches[1].Trim()
        } elseif ($action -match "^EXEC:(.*)") {
            Invoke-Expression $Matches[1].Trim()
        } else {
            Write-Host "nyxx: unexpected action: $action"
        }
    }
}
