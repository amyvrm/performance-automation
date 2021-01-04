variable "access_key" {}

variable "secret_key" {}

variable "common_region" {
  default = "ca-central-1"
}


variable "terraform_user" {
  description = "Pem file to authenticate into system"
  default = "TerraformDemo"
}


variable "subnet_id" {
	default = "subnet-3a7a9653"
}

variable "vpc_id" {
	default = "vpc-10de3179"
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
	default = "2m"
}

variable "conn_user" {
	default = "Administrator"
}

variable "volume_size" {
	default = "20"
}

variable "s3_bucket" {
	default = "regression-testing-jenkins"
}

variable "object_key" {
	default = "staging_mttr_artifacts"
}





