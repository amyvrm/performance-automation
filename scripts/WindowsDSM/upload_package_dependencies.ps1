#Set-ExecutionPolicy AllSigned
Set-ExecutionPolicy Bypass -Scope Process -Force;[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
Start-Sleep -s 5
choco install python --version=3.7.4 --force --no-progress -y
Start-Sleep -s 5

Write-Host 'Python Installed.'
