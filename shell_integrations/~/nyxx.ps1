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

    if (($args[0] -eq 'jump' -and $args[1] -eq 'add') -or
        ($args[0] -eq 'memo' -and $args[1] -eq 'add')) {
        & $pythonExecutable -m src.nyxx.main @args
        $env:PYTHONPATH = $oldPath
        $env:NYXX_CWD   = $oldCwd
        return
    }

    $output = & $pythonExecutable -m src.nyxx.main @args 2>$null
    $env:PYTHONPATH = $oldPath
    $env:NYXX_CWD   = $oldCwd

    if (-not $output) { return }

    if ($output -like "CD:*") {
        Set-Location $output.Substring(3)
        return
    }

    if ($output -like "EXEC:*") {
        Invoke-Expression $output.Substring(5)
        return
    }

    Write-Host "nyxx: unexpected output: $output"
}