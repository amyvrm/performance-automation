Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine

Write-Output "Disabling Windows Defender....."
Set-MpPreference -DisableRealtimeMonitoring $true
Write-Output "Windows Defender disabled."

<#
Write-Output "Disabling Firewall....."
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultInboundAction Allow -DefaultOutboundAction Allow
Write-Output "Firewall disabled."
#>

# The region associated with your bucket e.g. eu-west-1, us-east-1 etc. (see http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-regions)
$region = "ca-central-1"
# The name of your S3 Bucket
$bucket = "regression-testing-jenkins"
# The folder in your bucket to copy, including trailing slash. Leave blank to copy the entire bucket
$keyPrefix = "staging_mttr_artifacts/"
# The local file path where files should be copied
$localPath = "C:\Temp"

New-Item -ItemType Directory -Force -Path $localPath

# Fetch all zip files in the folder
$objects = Get-S3Object -BucketName $bucket -KeyPrefix $keyPrefix -Region $region

# Download all files
foreach($object in $objects) {
	$localFileName = $object.Key -replace $keyPrefix, ''
	if ($localFileName -ne '') {
		$localFilePath = Join-Path $localPath $localFileName
		Copy-S3Object -BucketName $bucket -Key $object.Key -LocalFile $localFilePath -Region $region
	}
}

<#
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine) + ";C:\Temp\",
    [EnvironmentVariableTarget]::Machine)

Write-Host "Ratt tool setup complete"
#>

# The local file path where files will be extracted
$extractedArtifacts = "C:\DSA-Setup"

#create directory path if it does not exist
New-Item -ItemType Directory -Force -Path $extractedArtifacts

# Expand the archived artifacts in regression test directory
Get-ChildItem $localPath -Filter *.zip | Expand-Archive -DestinationPath $extractedArtifacts -Force

Start-Process $extractedArtifacts"\Agent*.msi" /qn -Wait
Write-Host 'DSA Installed'


<#
# Delete zipped artifact folder
#Remove-Item -Recurse -Force $localPath
#>