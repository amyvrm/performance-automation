#Get the PID of the required service with the help of the service name, say, service name.
$ServicePID = (get-wmiobject win32_service | where { $_.name -eq 'service name'}).processID

#Now with this PID, you can kill the service
taskkill /f /pid $ServicePID
Start-Sleep -s 1