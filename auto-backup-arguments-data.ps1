# Auto-backup wrapper run by Windows Task Scheduler every 30 minutes.
# - If arguments-data/ has uncommitted changes (modified OR untracked files),
#   commit them with a timestamped "auto-backup" message and push to origin.
# - Otherwise: do nothing (no empty commits, no noise).
# - Logs every run to backups\auto-arguments-data.log.
#
# Why: arguments-data/ is hand-authored and the only copy lives on this
# laptop until pushed. Closing the "I forgot to commit" window from days
# to 30 minutes makes a laptop crash a 30-minute setback, not a total loss.
#
# Notes:
# - Only stages arguments-data/. Other in-progress files in the repo are
#   never touched.
# - If git push fails (offline, conflict, auth expired), the script logs
#   the error and exits non-zero so the next run can pick up where it left
#   off. It never force-pushes.

$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\zande\Documents\AI Workspace\Analyzing Islam"
$logFile  = Join-Path $repoRoot "backups\auto-arguments-data.log"
$git      = "git"

function Write-Log($message) {
    $stamp = (Get-Date).ToString("u")
    $line  = "[$stamp] $message"
    Write-Host $line
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

$null = New-Item -ItemType Directory -Force -Path (Split-Path $logFile -Parent)

try {
    Set-Location -Path $repoRoot

    # Anything under arguments-data/ that's modified, staged, or untracked.
    $changes = & $git status --porcelain -- "arguments-data" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed: $changes"
    }
    if ([string]::IsNullOrWhiteSpace($changes)) {
        # Quiet success -only log every 6 hours to avoid log spam.
        if (-not (Test-Path $logFile) -or
            ((Get-Date) - (Get-Item $logFile).LastWriteTime).TotalHours -ge 6) {
            Write-Log "No arguments-data changes."
        }
        exit 0
    }

    Write-Log "Detected changes:`n$changes"

    & $git add -- "arguments-data" 2>&1 | ForEach-Object { Write-Log "  add: $_" }
    if ($LASTEXITCODE -ne 0) { throw "git add failed (exit $LASTEXITCODE)" }

    # Re-check after add -if everything resolved to "no diff" (e.g.,
    # whitespace-only with autocrlf), bail without an empty commit.
    $staged = & $git diff --cached --name-only -- "arguments-data" 2>&1
    if ([string]::IsNullOrWhiteSpace($staged)) {
        Write-Log "Nothing to commit after staging (probably line-ending normalisation)."
        exit 0
    }

    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm")
    $msg = "auto-backup: arguments-data snapshot $stamp"

    & $git commit -m $msg 2>&1 | ForEach-Object { Write-Log "  commit: $_" }
    if ($LASTEXITCODE -ne 0) { throw "git commit failed (exit $LASTEXITCODE)" }

    & $git push origin HEAD 2>&1 | ForEach-Object { Write-Log "  push: $_" }
    if ($LASTEXITCODE -ne 0) { throw "git push failed (exit $LASTEXITCODE) - will retry next run" }

    Write-Log "OK: pushed snapshot."
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
