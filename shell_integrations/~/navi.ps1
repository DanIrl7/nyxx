
function navi {
    $projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
    $pythonExecutable = (Join-Path $projectRoot ".venv\Scripts\python.exe")

    if (-not (Test-Path $pythonExecutable)) {
        $pythonExecutable = "python.exe"
    }

    $oldPath = $env:PYTHONPATH
    $env:PYTHONPATH = $projectRoot

    # Interactive CLI subcommands (navi jump add / navi memo add) need the
    # terminal for Read-Host/input() prompts, so run them directly.
    if (($args[0] -eq 'jump' -and $args[1] -eq 'add') -or
        ($args[0] -eq 'memo' -and $args[1] -eq 'add')) {
        & $pythonExecutable -m src.navii.main @args
        $env:PYTHONPATH = $oldPath
        return
    }

    # TUI + lookup commands: capture output, then act on the prefix.
    $output = & $pythonExecutable -m src.navii.main @args
    $env:PYTHONPATH = $oldPath

    if ($output) {
        if ($output -match '^CD:(.*)$') {
            Set-Location $Matches[1]
        } elseif ($output -match '^EXEC:(.*)$') {
            Invoke-Expression $Matches[1]
        } else {
            Set-Location $output
        }
    }
}