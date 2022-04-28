resource "aws_instance" "windows_server2019" {
	
	ami = var.dsa_windows_ami
	instance_type = var.dsa_instance_type
	key_name = var.ssh_key_name
	associate_public_ip_address = "true"
	subnet_id = var.subnet_id
	security_groups = [aws_security_group.allow-winrm-ips.id]
	iam_instance_profile = var.instance_profile
	get_password_data = "true"
	user_data = file("SetUp-WinRM.txt")

	
	tags = {
			Name         = "performance_windows_server2019"
			"Trender"    = var.tag_trender
			"Automation" = var.tag_automation
			"ValidUntil" = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
			"workingHours" = "IGNORE"
	}
	
	depends_on = [
		null_resource.edit_user_data_script
		
	]
	
	connection {
			type     = "winrm"
			host     = aws_instance.windows_server2019.public_ip
			timeout  = var.conn_timeout
			user     = "Administrator"
			password = rsadecrypt(aws_instance.windows_server2019.password_data, file(var.ssh_key))
			insecure = "true"
	}

	provisioner "file" {
		source      = "tools/"
		destination = "C:/temp/"
	}

	provisioner "file" {
		source      = "${var.pkg_path}/"
		destination = "C:/temp/"
	}

	provisioner "remote-exec"  {
		inline = [
//					"powershell.exe -File C:\\temp\\WindowsAgentDeploymentScript.ps1",
					"powershell.exe -File C:\\temp\\install_pcattcp.ps1",
					"powershell.exe -File C:\\temp\\install_ab.ps1",
					"powershell.exe -File C:\\temp\\install_openssh.ps1",
					"powershell.exe -File C:\\temp\\install_nginx.ps1",
				]
	}
}

output "dsa-windows-id-2" {
	value = aws_instance.windows_server2019.id
}

output "dsa-public-ip-2" {
	value = aws_instance.windows_server2019.public_ip
}

output "dsa-user-2" {
	value = "Administrator"
}
