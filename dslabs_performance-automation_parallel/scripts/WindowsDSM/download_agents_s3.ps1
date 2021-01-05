Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine

$agentslocalPath = "C:\Temp\AgentPackages"
New-Item -ItemType Directory -Force -Path $agentslocalPath

$start_time = Get-Date

aws s3 sync s3://regression-testing-jenkins/staging_mttr_artifacts $agentslocalPath --exclude "*" --include "*.zip"

Write-Output "Time taken: $((Get-Date).Subtract($start_time).Seconds) second(s)"

Write-Host 'Agents download complete in DSM machine.'