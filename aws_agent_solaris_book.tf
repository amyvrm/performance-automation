resource "aws_instance" "dsa_solaris_machine" {
	
	ami = "${var.dsa_solaris_ami}"
	instance_type = "${var.dsa_instance_type}"
	key_name = "${var.terraform_user}"
	associate_public_ip_address = "true"
	subnet_id = "${var.subnet_id}"
	security_groups = ["${aws_security_group.allow-winrm-ips.id}"]
	iam_instance_profile = "${var.instance_profile}"
	
	
	tags = {
		Name = "${local.dsa_solaris_machine_name}"
		"Trender" = "${var.tag_trender}"
		"Automation" = "${var.tag_automation}"
		"ValidUntil" = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
	}
	
	depends_on = [
		null_resource.edit_user_data_script
		
	]
	
	connection {
		type = "ssh"
		host     = "${self.public_ip}"
		timeout  = "${var.conn_timeout}"
		user     = "ec2-user"
		private_key = "${file("${var.auth_file_path}/${var.terraform_user}.pem")}"
	}
	
	provisioner "file" {
		source      = "${var.script_file_path}/AgentDeploymentScript/SolarisAgentDeploymentScript.sh"
		destination = "/tmp/SolarisAgentDeploymentScript.sh"
	}
	
	provisioner "remote-exec"  {
		inline = [
					"chmod +x /tmp/SolarisAgentDeploymentScript.sh",
					"sudo sh /tmp/SolarisAgentDeploymentScript.sh"
				]
	}
	
	/*
	lifecycle {
		ignore_changes = [user_data]
	}
	*/
}

output "dsa-solaris-id" {
  value = "${aws_instance.dsa_solaris_machine.id}"
}