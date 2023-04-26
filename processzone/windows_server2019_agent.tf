resource "aws_instance" "windows_server2019_agent" {

	ami                         = data.aws_ami.windows_server2019_ami.id
	instance_type               = var.dsa_instance_type
	key_name                    = var.ssh_key_name
	associate_public_ip_address = "true"
	subnet_id 					= var.subnet_id
	security_groups 			= [var.wfh_sg]
	iam_instance_profile        = var.instance_profile
	get_password_data           = "true"
	user_data                   = file("SetUp-WinRM.txt")
	network_interface_id = "eni-0cca04f65c9240f78"

	tags = {
		Name           = "${var.tag_dsa_windows_name}_${var.random_num}"
		"Trender"      = var.tag_trender
		"Automation"   = var.tag_automation
		"ValidUntil"   = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
		"workingHours" = "IGNORE"
	}
}

resource "null_resource" "provision-agent" {
	connection {
			type     = "winrm"
			host     = aws_instance.windows_server2019_agent.private_ip
			timeout  = var.conn_timeout
			user     = "Administrator"
			password = rsadecrypt(aws_instance.windows_server2019_agent.password_data, file(var.ssh_key))
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

	provisioner "file" {
		source      = "scripts/AgentDeploymentScript/WindowsAgentDeploymentScript.ps1"
		destination = "C:/temp/WindowsAgentDeploymentScript.ps1"
	}

	provisioner "remote-exec"  {
		inline = [
					"powershell.exe -File C:\\temp\\WindowsAgentDeploymentScript.ps1 ${aws_instance.windows_server2019_agent.private_ip}",
					"powershell.exe -File C:\\temp\\install_pcattcp.ps1",
					"powershell.exe -File C:\\temp\\install_nginx.ps1",
					"powershell.exe -File C:\\temp\\install_openssh.ps1",
					"powershell.exe -File C:\\temp\\install_ab.ps1",
				]
	}
	depends_on = [
		null_resource.edit_user_data_script
	]
}

output "dsa-windows-id" {
	value = "${aws_instance.windows_server2019_agent.id}"
}
output "dsa-public-ip" {
	value = "${aws_instance.windows_server2019_agent.public_ip}"
}
output "dsa-user" {
	value = "Administrator"
}
