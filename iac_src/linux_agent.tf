resource "aws_instance" "performance_auto_machine" {
	# ubuntu 22.04
#	ami = "ami-09d56f8956ab235b3"
	# ubuntu 20.04
	ami                         = "ami-0c4f7023847b90238"
	instance_type               = var.instance_type
	key_name                    = var.key_name
	associate_public_ip_address = "true"
	subnet_id                   = var.subnet_id
	security_groups             = [var.security_grp_id]
	iam_instance_profile        = var.instance_profile


	tags = {
		Name           = "performance_auto_machine_${var.random_num}"
		"Trender"      = var.trender
		"ValidUntil"   = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
		"workingHours" = "IGNORE"
	}
}

resource "null_resource" "run_automation" {
	connection {
			type = "ssh"
			host     = aws_instance.performance_auto_machine.private_ip
			timeout  = var.conn_timeout
			user     = "ubuntu"
			private_key = file(var.private_key)
	}

	# Copies all files and folders in apps/app1 to D:/IIS/webapp1
	provisioner "file" {
    	source      = "src"
    	destination = "/tmp/src"
  	}
	provisioner "file" {
    	source      = var.machine_file
    	destination = var.local_manifest_file
  	}
	provisioner "file" {
    	source      = "templates"
    	destination = "/tmp/templates"
  	}
	provisioner "file" {
    	source      = "update-packages"
    	destination = "/tmp/update-packages"
  	}
	provisioner "file" {
		source      = "dslabs_automation.pem"
    	destination = "/tmp/dslabs_automation.pem"
	}
	provisioner "remote-exec" {
		inline = [
			"chmod +x /tmp/src/environment.sh",
			"chmod +x src/perform_scenario.py",
			"chmod +x src/team_msg.py",
			"sudo /bin/bash /tmp/src/environment.sh",
			"cd /tmp/",
#			"python3 src/perform_scenario.py --access_key ${var.access_key} --secret_key ${var.secret_key} --machine_info ${var.local_manifest_file} --dsm_version ${var.dsmVersion} --stats ${var.stats} --graph ${var.graph} --path ${var.dsru_path} --nexus_url ${var.nexus_url} --nexus_uname ${var.nexus_user} --nexus_pwd ${var.nexus_pass} --scenario ${var.scenario} --webhook ${var.webhook} --jenkins_url ${var.jenkins_url} --build_user ${var.build_user}",
			"python3 src/perform_scenario.py --access_key ${var.access_key} --secret_key ${var.secret_key} --machine_info ${var.local_manifest_file} --dsm_version ${var.dsmVersion} --stats ${var.stats} --graph ${var.graph} --path ${var.dsru_path} --nexus_url ${var.nexus_url} --nexus_uname ${var.nexus_user} --nexus_pwd ${var.nexus_pass} --scenario ${var.scenario} --pipeline_num ${var.pipeline_num}",
			"python3 src/team_msg.py --scenario ${var.scenario} --webhook ${var.webhook} --jenkins_url ${var.jenkins_url} --build_user ${var.build_user} --stats ${var.stats} --graph ${var.graph} --nexus_url ${var.nexus_url} --pipeline_num ${var.pipeline_num}",
		]
	}
	depends_on = [aws_instance.performance_auto_machine]
}
