variable "access_key" {}

variable "secret_key" {}

variable "region" {
  default = "us-east-1"
}

variable "agent_user" {
  default = "ec2-user"
}

variable "vpc_id" {
  default = "vpc-0472282ae61921e7b"
}

variable "subnet_id" {
  default = "subnet-00036005c63136c0f"
}

variable "security_grp_id" {
  default = "sg-032ea4e43f5ecf1a4"
}

variable "trender" {
  default = "DSLABS_Automation"
}

variable "instance_type" {
    default = "t2.micro"
}

variable "key_name" {
  default = "dslabs_automation"
}

variable "private_key" {
  default = "terraformAuthenticate/dslabs_automation.pem"
}

variable "instance_profile" {
	default = "Regression_Framework_Packer_Role"
}

variable "conn_timeout" {
	default = "5m"
}