resource "aws_instance" "dsa_centos8_machine" {
	
	ami = "${var.dsa_centos8_ami}"
	instance_type = "${var.dsa_instance_type}"
	key_name = "${var.terraform_user}"
	associate_public_ip_address = "true"
	subnet_id = "${var.subnet_id}"
	security_groups = ["${aws_security_group.allow-winrm-ips.id}"]
	iam_instance_profile = "${var.instance_profile}"
	
	
	tags = {
		Name = "${local.dsa_centos8_machine_name}"
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
		user     = "centos"
		private_key = "${file("${var.auth_file_path}/${var.terraform_user}.pem")}"
	}
	
	provisioner "file" {
		source      = "${var.script_file_path}/AgentDeploymentScript/LinuxAgentDeploymentScript.sh"
		destination = "/tmp/LinuxAgentDeploymentScript.sh"
	}
	
	provisioner "remote-exec"  {
		inline = [
					"chmod +x /tmp/LinuxAgentDeploymentScript.sh",
					"sudo sh /tmp/LinuxAgentDeploymentScript.sh"
				]
	}
	
	/*
	lifecycle {
		ignore_changes = [user_data]
	}
	*/
}

output "dsa-centos8-id" {
  value = "${aws_instance.dsa_centos8_machine.id}"
}
