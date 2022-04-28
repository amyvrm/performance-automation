resource "null_resource" "edit_user_data_script" {
	/*provisioner "local-exec" {
		command = "${var.script_file_path}/AgentDeploymentScript/generate_agent_script_files.ps1 -DSMIP ${aws_instance.dsm_machine.private_ip}"
		interpreter = ["PowerShell", "-Command"]
	}*/
	
	provisioner "local-exec" {
		command = "chmod +x AgentDeploymentScript/generateAllAgentDeploymentScript.sh"
	}
	
	provisioner "local-exec" {
		command = "/bin/bash AgentDeploymentScript/generateAllAgentDeploymentScript.sh ${aws_instance.rhel_dsm.private_ip}"
	}
	

	depends_on = [
		aws_instance.rhel_dsm
	]
}

/*
/bin/bash ${var.script_file_path}/AgentDeploymentScript/generateAllAgentDeploymentScript.sh
command = "${var.script_file_path}/AgentDeploymentScript/generate_agent_script_files.ps1 -DSMIP ${aws_instance.dsm_machine.private_ip}"
command = "${var.script_file_path}/AgentDeploymentScript/generate_agent_script_files.ps1 -DSMIP ${var.tag_dsm_name}"
*/