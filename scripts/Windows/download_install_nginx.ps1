#https://s3.console.aws.amazon.com/s3/buckets/perf-auto-pkg/?region=ap-south-1&tab=overview#

$region = "ap-south-1" # The region associated with your bucket
$bucket = "perf-auto-pkg" # The name of your S3 Bucket
# The folder in your bucket to copy, including trailing slash. Leave blank to copy the entire bucket
$keyPrefix = "perf_auto_package/"
$localPath = "C:\Temp" # The local file path where files should be copied
#$keyPrefix = "https://perf-auto-pkg.s3.ap-south-1.amazonaws.com/PCATTCP.zip"
$objects = Get-S3Object -BucketName $bucket -KeyPrefix $keyPrefix -Region $region

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

# The local file path where files will be extracted
$extractedArtifacts = "C:\DSA-Setup"

#create directory path if it does not exist
New-Item -ItemType Directory -Force -Path $extractedArtifacts

# Expand the archived artifacts in regression test directory
Get-ChildItem $localPath -Filter *.zip | Expand-Archive -DestinationPath $extractedArtifacts -Force

Start-Process $extractedArtifacts"\Agent*.msi" /qn -Wait
Write-Host 'DSA Installed'
