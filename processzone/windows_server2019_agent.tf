resource "aws_instance" "windows_server2019_agent" {
	count                       = var.instance_count + 1
	ami                         = data.aws_ami.windows_server2019_ami.id
	instance_type               = var.dsa_instance_type
	key_name                    = var.ssh_key_name
	associate_public_ip_address = "true"
	subnet_id 					= var.subnet_id
	security_groups 			= [var.wfh_sg]
	iam_instance_profile        = var.instance_profile
	get_password_data           = "true"
	user_data                   = file("SetUp-WinRM.txt")

	tags = {
		Name           = "${var.tag_dsa_windows_name}_${var.random_num}_${count.index}"
		"Trender"      = var.tag_trender
		"Automation"   = var.tag_automation
		"ValidUntil"   = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
		"workingHours" = "IGNORE"
	}
}

resource "null_resource" "provision-agent" {
	triggers = {
    	always_run = "${timestamp()}"
  	}
	count = var.instance_count + 1
	connection {
			type     = "winrm"
			host     = aws_instance.windows_server2019_agent[count.index].private_ip
			timeout  = var.conn_timeout
			user     = "Administrator"
			password = rsadecrypt(aws_instance.windows_server2019_agent[count.index].password_data, file(var.ssh_key))
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
					"powershell.exe -File C:\\temp\\WindowsAgentDeploymentScript.ps1 ${aws_instance.windows_server2019_agent[count.index].private_ip}",
					"powershell.exe -File C:\\temp\\InstallAllDependencies.ps1",
					# "powershell.exe -File C:\\temp\\install_nginx.ps1",
					# "powershell.exe -File C:\\temp\\install_openssh.ps1",
					# "powershell.exe -File C:\\temp\\install_ab.ps1",
				]
	}

	# Dependency chain for parallelization:
	# - Scripts must be generated first (edit_user_data_script)
	# - Instances must be ready (time_sleep.wait_for_instance_readiness)
	# - These run in parallel with RHEL DSM provisioning
	depends_on = [
		time_sleep.wait_for_instance_readiness
	]
}