Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine

$IPAddress = Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object {$_.Ipaddress.length -gt 1} 
$finalIP=$IPAddress.ipaddress[0]
$finalIP

((Get-Content -path C:\Temp\DSMProperties.properties -Raw) -replace 'MACHINE_IP',$finalIP) | Set-Content -Path C:\Temp\DSMProperties.properties