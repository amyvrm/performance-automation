resource "null_resource" "edit_user_data_script" {
    # Ensure the script is executable
    provisioner "local-exec" {
        command = "chmod +x scripts/AgentDeploymentScript/generateAllAgentDeploymentScript.sh"
    }

    # Run the script for each rhel_dsm instance
    provisioner "local-exec" {
        command = join(" && ", [
            for ip in aws_instance.rhel_dsm[*].private_ip :
            "/bin/bash scripts/AgentDeploymentScript/generateAllAgentDeploymentScript.sh ${ip}"
        ])
    }

    # Ensure this resource depends on all rhel_dsm instances
    depends_on = [
        aws_instance.rhel_dsm
    ]
}