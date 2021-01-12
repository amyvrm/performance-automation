resource "aws_instance" "dsa_windows_machine" {
	
	ami = "${var.dsa_windows_ami}"
	instance_type = "${var.dsa_instance_type}"
	key_name = "${var.terraform_user}"
	associate_public_ip_address = "true"
	subnet_id = "${var.subnet_id}"
	security_groups = ["${aws_security_group.allow-winrm-ips.id}"]
	iam_instance_profile = "${var.instance_profile}"
	get_password_data = "true"
	user_data = "${file("${var.script_file_path}/Windows/SetUp-WinRM.txt")}"

	tags = {
				Name = "${local.dsa_windows_machine_name}"
				"Trender" = "${var.tag_trender}"
				"Automation" = "${var.tag_automation}"
				"ValidUntil" = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
//				"workingHours" = "00:00-23:00 America/Toronto MON-FRI"
//				"ValidUntil" = "2020-12-21"
//				"Automation" = "Performance Automation"
				"workingHours" = "IGNORE"
		   }
	
	depends_on = [
		null_resource.edit_user_data_script
		
	]
	
	connection {
			type = "winrm"
			host     = "${aws_instance.dsa_windows_machine.public_ip}"
			timeout  = "${var.conn_timeout}"
			user     = "${var.conn_user}"
			password =  "${rsadecrypt(aws_instance.dsa_windows_machine.password_data,file("${var.auth_file_path}/${var.terraform_user}.pem"))}"
			insecure = "true"	
		}
	
	provisioner "file" {
		source      = "${var.script_file_path}/AgentDeploymentScript/WindowsAgentDeploymentScript.ps1"
		destination = "C:/temp/WindowsAgentDeploymentScript.ps1"
	}
	provisioner "file" {
		source      = "${var.pkg_path}/PCATTCP.zip"
		destination = "C:/temp/PCATTCP.zip"
	}
	provisioner "file" {
		source      = "${var.script_file_path}//Windows/install_pcattcp.ps1"
		destination = "C:/temp/install_pcattcp.ps1"
	}

	provisioner "file" {
		source      = "${var.pkg_path}/nginx-1.19.2ready.zip"
		destination = "C:/temp/nginx-1.19.2ready.zip"
	}
	provisioner "file" {
		source      = "${var.script_file_path}//Windows/install_nginx.ps1"
		destination = "C:/temp/install_nginx.ps1"
	}

	provisioner "file" {
		source      = "${var.script_file_path}//Windows///install_openssh.ps1"
		destination = "C:/temp/install_openssh.ps1"
	}

	provisioner "file" {
		source      = "${var.pkg_path}/ab.exe"
		destination = "C:/temp/ab.exe"
	}
	provisioner "file" {
		source      = "${var.script_file_path}//Windows/install_ab.ps1"
		destination = "C:/temp/install_ab.ps1"
	}
	
	provisioner "remote-exec"  {
		inline = [
					"powershell.exe -File C:\\temp\\WindowsAgentDeploymentScript.ps1",
					"powershell.exe -File C:\\temp\\install_pcattcp.ps1",
					"powershell.exe -File C:\\temp\\install_nginx.ps1",
					"powershell.exe -File C:\\temp\\install_openssh.ps1",
					"powershell.exe -File C:\\temp\\install_ab.ps1",
				]
	}
}

output "dsa-windows-id" {
	value = "${aws_instance.dsa_windows_machine.id}"
}
output "dsa-public-ip" {
	value = "${aws_instance.dsa_windows_machine.public_ip}"
}
output "dsa-user" {
	value = "${var.conn_user}"
}
