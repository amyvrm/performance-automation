#https://s3.console.aws.amazon.com/s3/buckets/perf-auto-pkg/?region=ap-south-1&tab=overview#

# The region associated with your bucket e.g. eu-west-1, us-east-1 etc. (see http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-regions)
$region = "ca-central-1"
# The name of your S3 Bucket
$bucket = "regression-testing-jenkins"
# The folder in your bucket to copy, including trailing slash. Leave blank to copy the entire bucket
$keyPrefix = "staging_mttr_artifacts/"
# The local file path where files should be copied
$localPath = "C:\Temp"