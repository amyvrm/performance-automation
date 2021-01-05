Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine
cd C:\Temp

cmd.exe /c "pip install zeep"
Start-Sleep -s 5

cmd.exe /c "pip install awscli"
Start-Sleep -s 5

Write-Host 'Python and aws dependencies installed.'
Start-Sleep -s 2

.\download_agents_s3.ps1

Write-Host 'Agent packages downloaded.'