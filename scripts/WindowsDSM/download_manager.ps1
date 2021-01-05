Param
(
    [Parameter(Mandatory = $true)]
    # agent url
    [String]$managerURL
)

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine

$localPath = "C:\Temp"

$managerFile = Split-Path $managerURL -leaf
$output = $localPath+'\'+$managerFile

$start_time = Get-Date

(New-Object System.Net.WebClient).DownloadFile($managerURL, $output)

Write-Output "Time taken: $((Get-Date).Subtract($start_time).Seconds) second(s)"

Write-Host 'DSM download complete.'