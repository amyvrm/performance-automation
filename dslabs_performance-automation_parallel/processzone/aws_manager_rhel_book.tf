resource "aws_instance" "dsm_machine" {
	
	ami = "${var.red_hat_ami}"
	instance_type = "${var.dsm_instance_type}"
	key_name = "${var.terraform_user}"
	associate_public_ip_address = "true"
	subnet_id = "${var.subnet_id}"
	security_groups = ["${aws_security_group.allow-winrm-ips.id}"]
	iam_instance_profile = "${var.instance_profile}"
	
	tags = {
			Name = "${local.dsm_machine_name}"
			"Trender" = "${var.tag_trender}"
			"Automation" = "${var.tag_automation}"
			"ValidUntil" = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
//			"workingHours" = "00:00-23:00 America/Toronto MON-FRI"
//			"ValidUntil" = "2020-12-21"
//			"Automation" = "Performance Automation"
			"workingHours" = "IGNORE"
	}
	
	connection {
		type = "ssh"
		host     = "${self.public_ip}"
		timeout  = "${var.conn_timeout}"
		user     = "ec2-user"
		private_key = "${file("${var.auth_file_path}/${var.terraform_user}.pem")}"
	}
	
	provisioner "file" {
		source      = "${var.script_file_path}/RedHat/"
		destination = "/tmp"
	}
	
	
	provisioner "remote-exec"  {
		inline = [
					"chmod +x /tmp/setupDSMInstall.sh",
					"chmod +x /tmp/generatePropertiesDSM.sh",
					"chmod +x /tmp/restartDSM.sh",
					"chmod +x /tmp/setupPython3.7.sh",
					"chmod +x /tmp/downloadAgents.sh",
					"chmod +x /tmp/uploadDSAToDSM.py",
					"sudo sh /tmp/setupDSMInstall.sh ${var.dsm_redhat_url} ${var.dsm_license}",
					"sudo sh /tmp/setupPython3.7.sh",
					"sh /tmp/downloadAgents.sh ${var.all_agent_urls}"
				]
	}
  
  root_block_device {
    volume_size = "${var.volume_size}"
  }
  
  
}

output "dsm-rhel-id" {
  value = "${aws_instance.dsm_machine.id}"
}
