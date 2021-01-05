Param
(
    [Parameter(Mandatory = $true)]
    # Manager url
    [String]$managerURL
)

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine

$managerFile = Split-Path $managerURL -leaf

cd C:\Temp
.\update_propertyfile.ps1
.\download_manager.ps1 -managerURL $managerURL
cmd.exe /c $managerFile -q -console -varfile DSMProperties.properties
.\initialize_dsm.ps1
Start-Sleep -s 5
cd C:\Temp
.\upload_package_dependencies.ps1


Write-Host 'DSM Installed and configured'