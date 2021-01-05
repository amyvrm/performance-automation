resource "aws_instance" "dsa_cloudlinux7_machine" {
	
	ami = "${var.dsa_cloudlinux7_ami}"
	instance_type = "${var.dsa_instance_type}"
	key_name = "${var.terraform_user}"
	associate_public_ip_address = "true"
	subnet_id = "${var.subnet_id}"
	security_groups = ["${aws_security_group.allow-winrm-ips.id}"]
	iam_instance_profile = "${var.instance_profile}"
	
	
	tags = {
		Name = "${local.dsa_cloudlinux7_machine_name}"
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
		source      = "${var.script_file_path}/AgentDeploymentScript/LinuxAgentDeploymentScript.sh"
		destination = "/tmp/LinuxAgentDeploymentScript.sh"
	}
	
	provisioner "remote-exec"  {
		inline = [
					"chmod +x /tmp/LinuxAgentDeploymentScript.sh",
					"sudo /bin/bash /tmp/LinuxAgentDeploymentScript.sh"
				]
	}
	
	/*
	lifecycle {
		ignore_changes = [user_data]
	}
	*/
}

resource "aws_ami_launch_permission" "dsa_cloudlinux7_machine" {
  image_id   = "${var.dsa_cloudlinux7_ami}"
  account_id = "573228283705"
}

output "dsa-cloudlinux7-id" {
  value = "${aws_instance.dsa_cloudlinux7_machine.id}"
}
