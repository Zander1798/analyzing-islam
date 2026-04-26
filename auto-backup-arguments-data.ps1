# Auto-backup wrapper run by Windows Task Scheduler every 30 minutes.
# - If arguments-data/ has uncommitted changes (modified OR untracked files),
#   commit them with a timestamped "auto-backup" message and push to origin
#   (which is configured to push to BOTH github.com and codeberg.org).
# - Otherwise: do nothing (no empty commits, no noise).
# - Logs every run to backups\auto-arguments-data.log.
#
# Why: arguments-data/ is hand-authored. Closing the "I forgot to commit"
# window from days to 30 minutes makes a laptop crash a 30-minute setback,
# not a total loss.
#
# Notes:
# - Only stages arguments-data/. Other in-progress files in the repo are
#   never touched.
# - If git push fails (offline, conflict, auth expired), the script logs
#   the error and exits non-zero so the next run can pick up where it left
#   off. It never force-pushes.
# - All git invocations route through cmd.exe to merge stderr without
#   triggering PowerShell 5.1's NativeCommandError wrapping (which
#   incorrectly turns harmless LF/CRLF warnings into terminating errors).

$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\zande\Documents\AI Workspace\Analyzing Islam"
$logFile  = Join-Path $repoRoot "backups\auto-arguments-data.log"

function Write-Log($message) {
    $stamp = (Get-Date).ToString("u")
    $line  = "[$stamp] $message"
    Write-Host $line
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

# Run a git command via cmd.exe so stderr merges cleanly into stdout
# without PowerShell wrapping. Returns the combined output as a string;
# sets the script-scope $script:GitExit to the exit code.
function Invoke-Git {
    param([Parameter(Mandatory=$true, ValueFromRemainingArguments=$true)] [string[]]$Args)
    $cmdline = "git " + ($Args -join " ") + " 2>&1"
    $output = & cmd.exe /c $cmdline
    $script:GitExit = $LASTEXITCODE
    return ($output | Out-String).TrimEnd()
}

$null = New-Item -ItemType Directory -Force -Path (Split-Path $logFile -Parent)

try {
    Set-Location -Path $repoRoot

    $status = Invoke-Git status --porcelain -- arguments-data
    if ($script:GitExit -ne 0) { throw "git status failed (exit $script:GitExit): $status" }

    if ([string]::IsNullOrWhiteSpace($status)) {
        if (-not (Test-Path $logFile) -or
            ((Get-Date) - (Get-Item $logFile).LastWriteTime).TotalHours -ge 6) {
            Write-Log "No arguments-data changes."
        }
        exit 0
    }

    Write-Log "Detected changes:"
    foreach ($line in $status -split "`r?`n") { Write-Log "  $line" }

    $addOut = Invoke-Git add -- arguments-data
    if ($script:GitExit -ne 0) { throw "git add failed (exit $script:GitExit): $addOut" }

    $staged = Invoke-Git diff --cached --name-only -- arguments-data
    if ($script:GitExit -ne 0) { throw "git diff --cached failed: $staged" }
    if ([string]::IsNullOrWhiteSpace($staged)) {
        Write-Log "Nothing to commit after staging (probably line-ending normalisation)."
        exit 0
    }

    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm")
    $msg = "auto-backup: arguments-data snapshot $stamp"
    $commitOut = Invoke-Git commit -m "`"$msg`""
    if ($script:GitExit -ne 0) { throw "git commit failed (exit $script:GitExit): $commitOut" }
    foreach ($line in $commitOut -split "`r?`n") { if ($line) { Write-Log "  commit: $line" } }

    $pushOut = Invoke-Git push origin HEAD
    if ($script:GitExit -ne 0) { throw "git push failed (exit $script:GitExit) - will retry next run: $pushOut" }
    foreach ($line in $pushOut -split "`r?`n") { if ($line) { Write-Log "  push: $line" } }

    Write-Log "OK: pushed snapshot to all configured origin URLs."
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
