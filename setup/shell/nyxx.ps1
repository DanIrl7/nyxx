# The `nyxx` command for PowerShell, as installed to {app}\shell by
# setup_script.iss, which adds a line to your PowerShell profile that
# dot-sources this file. Keeping the function here rather than in the
# profile itself means reinstalling Nyxx updates it.
#
# {app}\shell is deliberately not on PATH: PowerShell would resolve a bare
# `nyxx` to this file ahead of {app}\shims\nyxx.bat, and running it as a
# script (rather than dot-sourcing it) would only define the function.
#
# Python can't change its parent shell's working directory or run a
# command in it directly, so instead of doing that itself, Nyxx writes
# what it wants done to ~/.nyxx/action as "CD:<path>" or "EXEC:<cmd>".
# This function runs Nyxx, then reads that file and acts on it here, in
# the actual interactive shell.
function nyxx {
    # Same place Python resolves ~/.nyxx to on Windows.
    $actionFile = Join-Path $env:USERPROFILE ".nyxx\action"
    # Clear anything an earlier run left behind (e.g. Nyxx.exe started from
    # the Start menu) so only this run's action gets acted on below.
    Remove-Item -LiteralPath $actionFile -ErrorAction SilentlyContinue

    # $PSScriptRoot is this file's folder ({app}\shell), even when the
    # function is called long after the profile dot-sourced it.
    & (Join-Path $PSScriptRoot "..\Nyxx.exe") @args

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
