resource "aws_instance" "performance_auto_machine" {
    ami = "ami-0aeeebd8d2ab47354"
    instance_type     = var.instance_type
    key_name          = var.key_name
    associate_public_ip_address = "true"
    subnet_id = var.subnet_id
    security_groups = [var.security_grp_id]
    iam_instance_profile = var.instance_profile


    tags = {
        Name = "performance_auto_machine"
        "Trender" = var.trender
        "ValidUntil" = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
		"workingHours" = "IGNORE"
    }

	connection {
			type = "ssh"
			host     = aws_instance.performance_auto_machine.private_ip
			timeout  = var.conn_timeout
			user     = "ec2-user"
			private_key = file(var.private_key)
	}

	# Copies all files and folders in apps/app1 to D:/IIS/webapp1
	provisioner "file" {
    	source      = "src"
    	destination = "/tmp/iac_wd"
  	}

	provisioner "remote-exec" {
		inline = [
			"chmod +x /tmp/environment.sh",
			"sudo sh /tmp/environment.sh"
		]
	}
}
