# Phase 2b: Parallel File Organization Script
# Purpose: Reorganizes staged files from Terraform provisioners using parallel PowerShell jobs
# Expected savings: 15-50s per Windows instance vs sequential copy
# Author: Performance Automation Team
# Date: 2026-01-16

$ProgressPreference = 'SilentlyContinue'
$ErrorActionPreference = 'Stop'

Write-Host "[Phase 2b] Starting parallel file organization..."
$startTime = Get-Date

# Ensure destination directories exist
New-Item -ItemType Directory -Force -Path "C:\temp" | Out-Null

# Copy all files in parallel using background jobs
$jobs = @()
$jobs += Start-Job -ScriptBlock { Copy-Item -Path "C:\temp\tools\*" -Destination "C:\temp\" -Recurse -Force }
$jobs += Start-Job -ScriptBlock { Copy-Item -Path "C:\temp\packages\*" -Destination "C:\temp\" -Recurse -Force }
$jobs += Start-Job -ScriptBlock { Copy-Item -Path "C:\temp\scripts\WindowsAgentDeploymentScript.ps1" -Destination "C:\temp\WindowsAgentDeploymentScript.ps1" -Force }

# Wait for all jobs to complete and check for errors
$jobs | Wait-Job | ForEach-Object {
    if ($_.State -eq 'Failed') {
        Receive-Job $_
        throw "Parallel copy job failed: $($_.Name)"
    }
    Receive-Job $_
} | Out-Null

# Cleanup jobs
$jobs | Remove-Job -Force

$duration = (Get-Date) - $startTime
Write-Host "✓ Parallel file organization complete in $([math]::Round($duration.TotalSeconds, 2))s"

# Verify critical files exist
$requiredFiles = @(
    "C:\temp\WindowsAgentDeploymentScript.ps1",
    "C:\temp\InstallAllDependencies.ps1"
)
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        throw "Required file missing after copy: $file"
    }
}
Write-Host "✓ File integrity verified"

# Return success
exit 0
