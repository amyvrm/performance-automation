variable "access_key" {}

variable "secret_key" {}

variable "region" {
  default = "us-east-1"
}

variable "agent_user" {
  default = "ec2-user"
}

variable "vpc_id" {
  default = "vpc-00cf1001c6535f749"
}

variable "subnet_id" {
  default = "subnet-0e56fc43911a8e78d"
}

variable "security_grp_id" {
  default = "sg-002386483ee32b11f"
}

variable "trender" {
  default = "DSLABS_Automation"
}

variable "performance_auto_machine_ami_id" {
  default = "ami-0767d6800887542a9"
}

variable "instance_type" {
    default = "t2.micro"
}

variable "key_name" {
  default = "dslabs_automation"
}

variable "private_key" {
  default = "dslabs_automation.pem"
}

variable "instance_profile" {
	default = "Regression_Framework_Packer_Role"
}

variable "conn_timeout" {
	default = "5m"
}

variable "manifest_file_path" {}

variable "manifest_file" {}

variable "dsmVersion" {}

variable "stats" {}

variable "graph" {}

variable "dsru_path" {}

variable "jfrog_url" {}

variable "jfrog_token" {}

variable "scenario" {}

variable "random_num" {}

variable "rule_id" {
  default = 0
}