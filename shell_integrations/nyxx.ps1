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
    $projectRoot = "C:\Users\t430\3D Objects\coding\projects\Nyxx"
    $pythonExecutable = Join-Path $projectRoot ".venv\Scripts\python.exe"

    if (-not (Test-Path $pythonExecutable)) {
        Write-Host "nyxx: python not found at $pythonExecutable"
        return
    }

    $oldPath    = $env:PYTHONPATH
    $oldCwd     = $env:NYXX_CWD
    $env:PYTHONPATH = $projectRoot
    $env:NYXX_CWD   = (Get-Location).Path      # ← pass current directory

    & $pythonExecutable -m src.nyxx.main @args

    $env:PYTHONPATH = $oldPath
    $env:NYXX_CWD   = $oldCwd

    $actionFile = "$HOME/.nyxx/action"
    if (Test-Path $actionFile) {
        $action = (Get-Content $actionFile -Raw).Trim()
        Remove-Item $actionFile
        if ($action -match "^CD:(.*)") {
            Set-Location $Matches[1].Trim()
        } elseif ($action -match "^EXEC:(.*)") {
            Invoke-Expression $Matches[1].Trim()
        } else {
            Write-Host "nyxx: unexpected action: $action"
        }
    }
}
