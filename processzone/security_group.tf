data "http" "myip" {
  url = "http://ipv4.icanhazip.com"
}

resource "aws_security_group" "allow-winrm-ips" {
	
	vpc_id = "${var.vpc_id}"
    name = "${local.security_group_name}"
    description = "security group that allows specific DSLabs IPs and winrm and all egress traffic"
	
	tags = {
		"Trender" = "${var.tag_trender}"
		"Automation" = "${var.tag_automation}"
	}
	
	
	#Outbound
	egress {
        # Outbound traffic is set to all
        from_port       = 0
        to_port         = 0
        protocol        = "-1"
        cidr_blocks     = ["0.0.0.0/0"]
    }
	
	#Inbound
	#Access IP 1
	ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["170.199.237.194/32"]
    }
	
	#Access IP 2
	ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["106.51.243.96/32"]
    }
	
	#Access IP 3
	ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["67.70.253.226/32"]
    }
	
	#Access IP 4
	ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["182.72.141.226/32"]
    }
	
	#Access IP 5
	ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["207.107.79.154/32"]
    }
	
	#Access IP 6
	ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["204.209.176.210/32"]
    }
	
	#Access IP 7
	ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["${chomp(data.http.myip.body)}/32"]
    }

    # WinRM - Port 5985 
    ingress {
        from_port = 5985
        to_port = 5985
        protocol = "tcp"
        cidr_blocks = ["${chomp(data.http.myip.body)}/32"]
    }

    # WinRM - Port 5986 
    ingress {
        from_port = 5986
        to_port = 5986
        protocol = "tcp"
        cidr_blocks = ["${chomp(data.http.myip.body)}/32"]
    }

	# SSH - Port 22 
	ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["${chomp(data.http.myip.body)}/32"]
    }
	
	#Self Security group to access instances
	ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        self = "true"
    }
  
}

output "sg-id" {
  value = "${aws_security_group.allow-winrm-ips.id}"
}
    