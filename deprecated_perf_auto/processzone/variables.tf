variable  "script_file_path" {
  default = "./scripts"
}

variable "ssh_key_name" {
	default = "dslabs_automation"
}

variable "ssh_key" {
	default = "dslabs_automation.pem"
}

variable "pkg_path" {
  default = "./Temp"
}

variable "auth_file_path" {
  default = "./terraformAuthenticate"
}

variable "dsm-user" {
	default = "supermasteradmin"
}

variable "dsm-password" {
	default = "OrangePlant#1980"
}

variable "dsm_license" {}

variable "dsm_redhat_url" {}

variable "dsm_windows_url" {
	default = "https://files.trendmicro.com/products/deepsecurity/en/12.0/Manager-Windows-12.0.458.x64.exe"
}

variable "agent_windows_object_url" {
	default = "https://files.trendmicro.com/products/deepsecurity/en/12.0/Agent-Windows-12.0.0-1090.x86_64.zip"
}

variable "agent_amazon1_object_url" {
	default = "https://files.trendmicro.com/products/deepsecurity/en/12.0/Agent-amzn1-12.0.0-1090.x86_64.zip"
}

variable "agent_amazon2_object_url" {
	default = "https://files.trendmicro.com/products/deepsecurity/en/12.0/Agent-amzn2-12.0.0-1090.x86_64.zip"
}

variable "all_agent_urls" {
	default = "https://files.trendmicro.com/products/deepsecurity/en/12.0/Agent-Windows-12.0.0-1090.x86_64.zip~~https://files.trendmicro.com/products/deepsecurity/en/12.0/Agent-amzn1-12.0.0-1090.x86_64.zip~~https://files.trendmicro.com/products/deepsecurity/en/12.0/Agent-amzn2-12.0.0-1090.x86_64.zip"
}

variable "random_num" {
	default = "123"
}





