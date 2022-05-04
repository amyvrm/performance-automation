resource "aws_instance" "rhel_dsm" {
	
	ami = var.red_hat_ami
	instance_type = var.dsm_instance_type
	key_name = var.ssh_key_name
	associate_public_ip_address = "true"
	subnet_id = var.subnet_id
	security_groups = [var.wfh_sg]
	iam_instance_profile = var.instance_profile
	
	tags = {
			Name           = var.tag_dsm_name
			"Trender"      = var.tag_trender
			"Automation"   = var.tag_automation
			"ValidUntil"   = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
			"workingHours" = "IGNORE"
	}
	
	connection {
		type        = "ssh"
		host        = aws_instance.rhel_dsm.private_ip
		timeout     = var.conn_timeout
		user        = "ec2-user"
		private_key = file(var.ssh_key)
	}

	provisioner "file" {
		source      = "scripts/RedHat/"
		destination = "/tmp"
	}
	provisioner "remote-exec"  {
		inline = [
					"chmod +x /tmp/setupDSMInstall.sh",
					"chmod +x /tmp/generatePropertiesDSM.sh",
					"chmod +x /tmp/restartDSM.sh",
					"chmod +x /tmp/setupPython3.6.sh",
					"chmod +x /tmp/downloadAgents.sh",
					"chmod +x /tmp/uploadDSAToDSM.py",
					"sudo sh /tmp/setupDSMInstall.sh ${var.dsm_redhat_url} ${var.dsm_license}",
					"sudo sh /tmp/setupPython3.6.sh",
					"sh /tmp/downloadAgents.sh ${var.all_agent_urls}"
				]
	}
  
	root_block_device {
		volume_size = var.volume_size
	}
}

output "dsm-rhel-id" {
	value = aws_instance.rhel_dsm.id
}
