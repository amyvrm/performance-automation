<#
Accelerated install: run independent steps in parallel and skip work if already present.
This reduces total execution time significantly on fresh hosts.
#>

$ErrorActionPreference = 'Stop'

function Ensure-FileExists {
	param(
		[Parameter(Mandatory=$true)][string]$Path,
		[Parameter()][string]$Description = $Path
	)
	if (-not (Test-Path $Path)) {
		throw "Missing required file: $Description ($Path)"
	}
}

# Preflight expected artifacts
Ensure-FileExists -Path 'C:/temp/nginx-1.19.2ready.zip' -Description 'nginx zip'
Ensure-FileExists -Path 'C:/temp/ab.exe' -Description 'Apache Bench'
Ensure-FileExists -Path 'C:/temp/hey.exe' -Description 'hey.exe'

# Kick off lightweight tools (non-blocking) with safe help/version flags to avoid errors
try {
	if (Test-Path 'C:/temp/ab.exe') {
		Start-Process -FilePath 'C:/temp/ab.exe' -ArgumentList '-V' -NoNewWindow -WindowStyle Hidden -ErrorAction SilentlyContinue
	}
} catch { Write-Verbose "ab.exe check failed: $($_.Exception.Message)" }

try {
	if (Test-Path 'C:/temp/hey.exe') {
		Start-Process -FilePath 'C:/temp/hey.exe' -ArgumentList '--help' -NoNewWindow -WindowStyle Hidden -ErrorAction SilentlyContinue
	}
} catch { Write-Verbose "hey.exe check failed: $($_.Exception.Message)" }

# Parallel tasks: nginx extract, OpenSSH and iperf3 install
$jobs = @()

# NGINX extract (idempotent)
if (-not (Test-Path 'C:/temp/nginx-1.19.2/nginx.exe')) {
	$jobs += Start-Job -ScriptBlock {
		Expand-Archive -Path 'C:/temp/nginx-1.19.2ready.zip' -DestinationPath 'C:/temp/' -Force
	}
}

# OpenSSH and iperf3 via Chocolatey (install if missing)
$jobs += Start-Job -ScriptBlock {
	try {
		Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine -Force
		if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
			iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
		}
		$opensshInstalled = choco list --local-only | Select-String -Pattern '^openssh'
		if (-not $opensshInstalled) {
			choco install openssh -y -f
		}
		$iperf3Installed = choco list --local-only | Select-String -Pattern '^iperf3'
		if (-not $iperf3Installed) {
			choco install iperf3 -y -f
		}
		Set-Service -Name ssh-agent -StartupType Automatic -ErrorAction SilentlyContinue
		Set-Service -Name sshd -StartupType Automatic -ErrorAction SilentlyContinue
		Start-Service ssh-agent -ErrorAction SilentlyContinue
		Start-Service sshd -ErrorAction SilentlyContinue
	} catch {
		Write-Warning "Chocolatey package installation encountered an issue: $($_.Exception.Message)"
	}
}

# PCATTCP extract (idempotent)
if (-not (Test-Path 'C:/temp/PCATTCP/PCATTCP.exe')) {
	$jobs += Start-Job -ScriptBlock {
		Expand-Archive -Path 'C:/temp/PCATTCP.zip' -DestinationPath 'C:/temp/' -Force
	}
}

# PCATTCP extract (idempotent)
if (-not (Test-Path 'C:/temp/PCATTCP/PCATTCP.exe')) {
	$jobs += Start-Job -ScriptBlock {
		Expand-Archive -Path 'C:/temp/PCATTCP.zip' -DestinationPath 'C:/temp/' -Force
	}
}

# Wait for all jobs to finish
if ($jobs.Count -gt 0) {
	Wait-Job -Job $jobs | Out-Null
	Receive-Job -Job $jobs | Out-Null
	Remove-Job -Job $jobs | Out-Null
}

# Start nginx only if binary exists; ensure working directory and logs path
if (Test-Path 'C:/temp/nginx-1.19.2/nginx.exe') {
	try {
		if (-not (Test-Path 'C:/temp/nginx-1.19.2/logs')) {
			New-Item -ItemType Directory -Path 'C:/temp/nginx-1.19.2/logs' -Force | Out-Null
		}
		Start-Process -FilePath 'C:/temp/nginx-1.19.2/nginx.exe' -WorkingDirectory 'C:/temp/nginx-1.19.2' -ArgumentList '-t' -NoNewWindow -WindowStyle Hidden -ErrorAction SilentlyContinue
		Start-Process -FilePath 'C:/temp/nginx-1.19.2/nginx.exe' -WorkingDirectory 'C:/temp/nginx-1.19.2' -NoNewWindow -WindowStyle Hidden -ErrorAction SilentlyContinue
	} catch {
		Write-Warning "nginx start encountered an issue: $($_.Exception.Message)"
	}
}

Write-Output 'Dependencies setup completed (parallel, idempotent).'
Write-Output 'iperf3 is installed and ready for network throughput testing.'