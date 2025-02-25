Param
(
    [Parameter(Mandatory = $true)]
    # DSM Private IP
    [String]$DSMIP
)

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine

$currPath = $PSScriptRoot

((Get-Content -path $currPath\AIXAgentDeploymentScript -Raw) -replace 'DSM_MACHINE_IP',$DSMIP) | Set-Content -Path $currPath\AIXAgentDeploymentScript.sh
((Get-Content -path $currPath\LinuxAgentDeploymentScript -Raw) -replace 'DSM_MACHINE_IP',$DSMIP) | Set-Content -Path $currPath\LinuxAgentDeploymentScript.sh
((Get-Content -path $currPath\SolarisAgentDeploymentScript -Raw) -replace 'DSM_MACHINE_IP',$DSMIP) | Set-Content -Path $currPath\SolarisAgentDeploymentScript.sh
((Get-Content -path $currPath\WindowsAgentDeploymentScript -Raw) -replace 'DSM_MACHINE_IP',$DSMIP) | Set-Content -Path $currPath\WindowsAgentDeploymentScript.ps1