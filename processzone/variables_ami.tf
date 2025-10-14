variable "red_hat_ami"{
	default = "ami-00da411e2377e25a0"
}

variable "dsm_windows_ami"{
#	default = "ami-0c95d38b24a19de18"
	default = "ami-06371c9f2ad704460"
}

variable "dsa_windows_ami"{
#	default = "ami-0c95d38b24a19de18"
#	default = "ami-06371c9f2ad704460"
	default = "ami-051a0421f3df4c021"
}

# data "aws_ami" "rhel8_ami" {
#   most_recent      = true
#   owners           = ["amazon"]

#   filter {
#     name   = "name"
#     values = ["RHEL-8.6.0_HVM*x86_64*GP2"]
#   }

#   filter {
#     name   = "root-device-type"
#     values = ["ebs"]
#   }

#   filter {
#     name   = "virtualization-type"
#     values = ["hvm"]
#   }
#   filter {
#     name   = "architecture"
#     values = ["x86_64"]
#   }
# }

data "aws_ami" "windows_server2019_ami" {
  most_recent      = true
  owners           = ["amazon"]

  filter {
    name   = "name"
    values = ["Windows_Server-2019-English-Full-Base*"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}