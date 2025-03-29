resource "aws_instance" "performance_auto_machine" {
	ami                         = var.performance_auto_machine_ami_id
	instance_type               = var.instance_type
	key_name                    = var.key_name
	associate_public_ip_address = true
	subnet_id                   = var.subnet_id
	security_groups             = [var.security_grp_id]
	iam_instance_profile        = var.instance_profile

	tags = {
		Name           = "performance_auto_machine_${var.random_num}"
		Trender        = var.trender
		ValidUntil     = formatdate("YYYY-MM-DD", timeadd(timestamp(), "48h"))
		workingHours   = "IGNORE"
	}
}

resource "null_resource" "run_automation" {
	triggers = {
		always_run = timestamp()
	}

	connection {
		type        = "ssh"
		host        = aws_instance.performance_auto_machine.private_ip
		timeout     = var.conn_timeout
		user        = "ubuntu"
		private_key = file(var.private_key)
	}

	provisioner "file" {
		source      = "src"
		destination = "/tmp/src"
	}

	provisioner "file" {
		source      = var.manifest_file_path
		destination = "/tmp/${var.manifest_file}"
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
			"chmod +x /tmp/src/perform_scenario.py",
			"chmod +x /tmp/src/team_msg.py",
			"cd /tmp/",
			"echo python3 /tmp/src/perform_scenario.py --access_key ${var.access_key} --secret_key ${var.secret_key} --manifest_file ${var.manifest_file} --dsm_version ${var.dsmVersion} --stats ${var.stats} --graph ${var.graph} --path ${var.dsru_path} --jfrog_url ${var.jfrog_url} --jfrog_token ${var.jfrog_token} --scenario ${var.scenario} --rule_id ${var.rule_id} --individual_rule_test ${var.individual_rule_test}> cmd.txt",
			"python3 /tmp/src/perform_scenario.py --access_key ${var.access_key} --secret_key ${var.secret_key} --manifest_file ${var.manifest_file} --dsm_version ${var.dsmVersion} --stats ${var.stats} --graph ${var.graph} --path ${var.dsru_path} --jfrog_url ${var.jfrog_url} --jfrog_token ${var.jfrog_token} --scenario ${var.scenario} --rule_id ${var.rule_id} --individual_rule_test ${var.individual_rule_test}",
		]
	}

	depends_on = [aws_instance.performance_auto_machine]
}

output "performance_auto_machine_id" {
	value = aws_instance.performance_auto_machine.id
}