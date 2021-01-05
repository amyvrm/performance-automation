locals {
	agent_windows_filename = "${basename(var.agent_windows_object_url)}"
	agent_amazon1_filename = "${basename(var.agent_amazon1_object_url)}"
	agent_amazon2_filename = "${basename(var.agent_amazon2_object_url)}"
}

/*
resource "null_resource" "download-agent-artifact" {
	provisioner "local-exec" {
		command = "wget ${var.agent_windows_object_url} -O ${local.agent_windows_filename}"
	}
}
*/

/*use below to test in windows*/

/*
resource "null_resource" "download_windows_agent_artifact" {
	provisioner "local-exec" {
		command = "Invoke-WebRequest ${var.agent_windows_object_url} -OutFile ${local.agent_windows_filename}"
		interpreter = ["PowerShell", "-Command"]
	}
}



resource "aws_s3_bucket_object" "windows_agent_upload" {
	bucket = "${var.s3_bucket}"
	key    = "${var.object_key}/${local.agent_windows_filename}"
	source = "${local.agent_windows_filename}"
	
	depends_on = [
		null_resource.download_windows_agent_artifact
	]
}



resource "null_resource" "download_amazon1_agent_artifact" {
	provisioner "local-exec" {
		command = "Invoke-WebRequest ${var.agent_amazon1_object_url} -OutFile ${local.agent_amazon1_filename}"
		interpreter = ["PowerShell", "-Command"]
	}
}

resource "aws_s3_bucket_object" "amazon1_agent_upload" {
	bucket = "${var.s3_bucket}"
	key    = "${var.object_key}/${local.agent_amazon1_filename}"
	source = "${local.agent_amazon1_filename}"
	
	depends_on = [
		null_resource.download_amazon1_agent_artifact
	]
}
*/

/*
resource "null_resource" "download_amazon2_agent_artifact" {
	provisioner "local-exec" {
		command = "Invoke-WebRequest ${var.agent_amazon2_object_url} -OutFile ${local.agent_amazon2_filename}"
		interpreter = ["PowerShell", "-Command"]
	}
}

resource "aws_s3_bucket_object" "amazon2_agent_upload" {
	bucket = "${var.s3_bucket}"
	key    = "${var.object_key}/${local.agent_amazon2_filename}"
	source = "${local.agent_amazon2_filename}"
	
	depends_on = [
		null_resource.download_amazon2_agent_artifact
	]
}
*/