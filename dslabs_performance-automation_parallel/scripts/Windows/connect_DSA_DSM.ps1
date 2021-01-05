Param
(
    [Parameter(Mandatory = $true)]
    # DSM Public DNS
    [String]$PublicDNS
	#,
	# DSA Public DNS
    #[String]$PublicDNS_DSA
)
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine
$Path = "C:\Program Files\Trend Micro\Deep Security Agent"
$dsa_connect_string = "dsm://"+$PublicDNS+":4120/"
cd $Path
cmd.exe /c dsa_control -r
cmd.exe /c dsa_control -a $dsa_connect_string
#cmd.exe /c "dsa_control.cmd -a "$dsa_connect_string" hostname:"$PublicDNS_DSA
Write-Host "DSA connected with DSM"
Write-Host "######################################################"