Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
Start-Sleep -s 5
choco install openssh -y -f
#choco install openssh --version=0.0.19.0 --force --no-progress -y
Start-Sleep -s 5
Set-Service -Name ssh-agent -StartupType Automatic
Set-Service -Name sshd -StartupType Automatic
Start-Service ssh-agent
Start-Service sshd
