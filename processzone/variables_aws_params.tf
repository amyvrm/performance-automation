variable "access_key" {}

variable "secret_key" {}

variable "common_region" {
  default = "us-east-1"
}

variable "terraform_user" {
  description = "Pem file to authenticate into system"
  default = "dslabs_automation"
}

variable "terraform-vpc" {
  default = "terraform-vpc"
}

#variable "subnet_id" {
#	default = "subnet-3a7a9653"
#}
#
#variable "vpc_id" {
#	default = "vpc-10de3179"
#}

variable "subnet_id" {
	default = "subnet-0e56fc43911a8e78d"
}

variable "vpc_id" {
	default = "vpc-00cf1001c6535f749"
}

variable "dsm_instance_type" {
	default = "t2.large"
}

//variable "dsa_instance_type" {
//	default = "t2.large"
//}

variable "dsa_instance_type" {
	default = "c5.large"
}

variable "instance_profile" {
	default = "Regression_Framework_Packer_Role"
}


variable "tag_trender" {
	default = "DSLabs_Automation"
}

variable "tag_automation" {
	default = "Perf_Automation"
}

variable "conn_timeout" {
	default = "5m"
}

variable "conn_user" {
	default = "Administrator"
}

variable "volume_size" {
	default = "20"
}

variable "wfh_sg" {
	default = "sg-002386483ee32b11f"
}
