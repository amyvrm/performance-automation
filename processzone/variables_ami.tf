variable "red_hat_ami"{
	default = "ami-05816666b3178f208"
}

variable "dsm_windows_ami"{
	default = "ami-02c4947e847caf22c"
}

//ami-088ba3e5460a63e7a
variable "dsa_windows_ami"{
//	default = "ami-00dd0737502449ce1"
	default = "ami-0cdfa905439f4b9ca"
}

variable "dsa_amazon1_ami"{
	default = "ami-00b243003d0e9e258"
}

variable "dsa_amazon2_ami"{
	default = "ami-0f75c2980c6a5851d"
}

variable "dsa_rhel_ami"{
	default = "ami-05816666b3178f208"
}

variable "dsa_ubuntu_ami"{
	default = "ami-0e2df0719252d4491"
}

/*This is not solaris AMI. AWS doesn't support solaris*/
variable "dsa_solaris_ami"{
	default = "ami-0e2df0719252d4491"
}

variable "dsa_cloudlinux8_ami"{
	default = "ami-090dd18bfa6eee0b4"
}

variable "dsa_cloudlinux7_ami"{
	default = "ami-07b6a5ccb6562986b"
}

variable "dsa_oraclelinux7_ami" {
	default = "ami-022601994abf41776"
}

variable "dsa_oraclelinux8_ami" {
	default = "ami-088917326cf5eb50f"
}

variable "dsa_debian9_ami" {
	default = "ami-07b593ac4546dde0a"
}

variable "dsa_debian10_ami" {
	default = "ami-0b53d6096e27f2f48"
}

variable "dsa_centos8_ami" {
	default = "ami-00de8b708897ebaf3"
}

variable "dsa_centos7_ami" {
	default = "ami-04a25c39dc7a8aebb"
}
