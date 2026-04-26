# Wrapper run by Windows Task Scheduler every Sunday at 09:00 local.
# - Loads the Supabase service-role key from a file outside the repo.
# - Runs backup-supabase.py.
# - Copies the new timestamped dump folder to OneDrive for off-laptop safety.
# - Appends every run (success or failure) to backups\scheduled-runs.log.

$ErrorActionPreference = "Stop"

$repoRoot   = "C:\Users\zande\Documents\AI Workspace\Analyzing Islam"
$keyFile    = "$env:USERPROFILE\.supabase-service-role"
$python     = "C:\Python313\python.exe"
$logFile    = Join-Path $repoRoot "backups\scheduled-runs.log"
$onedriveDest = "C:\Users\zande\OneDrive\AnalyzingIslam-Backups"

function Write-Log($message) {
    $stamp = (Get-Date).ToString("u")
    $line  = "[$stamp] $message"
    Write-Host $line
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

# Ensure log dir exists before first write.
$null = New-Item -ItemType Directory -Force -Path (Split-Path $logFile -Parent)

try {
    if (-not (Test-Path $keyFile)) {
        throw "Key file not found at $keyFile. Create it with the service_role key on one line."
    }

    $key = (Get-Content -Path $keyFile -Raw -Encoding UTF8).Trim()
    if ([string]::IsNullOrWhiteSpace($key)) {
        throw "Key file at $keyFile is empty."
    }

    Write-Log "Run started."
    Set-Location -Path $repoRoot
    $env:SUPABASE_SERVICE_ROLE = $key

    # Snapshot existing backup folders so we can find the new one.
    $beforeDirs = @{}
    if (Test-Path "$repoRoot\backups") {
        Get-ChildItem -Path "$repoRoot\backups" -Directory | ForEach-Object { $beforeDirs[$_.Name] = $true }
    }

    & $python "backup-supabase.py" 2>&1 | ForEach-Object { Write-Log "  $_" }
    if ($LASTEXITCODE -ne 0) {
        throw "backup-supabase.py exited with code $LASTEXITCODE"
    }

    # Find the newly-created dump folder (the one that wasn't there before).
    $newDump = Get-ChildItem -Path "$repoRoot\backups" -Directory |
        Where-Object { -not $beforeDirs.ContainsKey($_.Name) } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($null -eq $newDump) {
        throw "Backup script reported success but no new dump folder was found."
    }

    # Mirror to OneDrive.
    $null = New-Item -ItemType Directory -Force -Path $onedriveDest
    $dest = Join-Path $onedriveDest $newDump.Name
    Copy-Item -Path $newDump.FullName -Destination $dest -Recurse -Force
    Write-Log "Copied dump to OneDrive: $dest"

    # Optional housekeeping: keep last 12 local dumps. OneDrive retains all.
    $allLocal = Get-ChildItem -Path "$repoRoot\backups" -Directory | Sort-Object LastWriteTime -Descending
    if ($allLocal.Count -gt 12) {
        $allLocal | Select-Object -Skip 12 | ForEach-Object {
            Remove-Item -Path $_.FullName -Recurse -Force
            Write-Log "Pruned old local dump: $($_.Name)"
        }
    }

    Write-Log "Run finished OK."
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
finally {
    $env:SUPABASE_SERVICE_ROLE = $null
}
