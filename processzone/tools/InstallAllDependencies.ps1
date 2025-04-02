# Run initial processes
Start-Process -FilePath "C:/temp/ab.exe" -NoNewWindow
Start-Process -FilePath "C:/temp/hey.exe" -NoNewWindow
Start-Sleep -Seconds 2

# Extract and start NGINX
Expand-Archive -Path "C:/temp/nginx-1.19.2ready.zip" -DestinationPath "C:/temp/"
Start-Process -FilePath "C:/temp/nginx-1.19.2/nginx.exe" -NoNewWindow -Wait

# Install Chocolatey and OpenSSH
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
choco install openssh -y -f
Set-Service -Name ssh-agent -StartupType Automatic
Set-Service -Name sshd -StartupType Automatic
Start-Service ssh-agent
Start-Service sshd

# Extract and run PCATTCP
Expand-Archive -Path "C:/temp/PCATTCP.zip" -DestinationPath "C:/temp/"
Start-Process -FilePath "C:/temp/PCATTCP/PCATTCP.exe" -NoNewWindow -Wait