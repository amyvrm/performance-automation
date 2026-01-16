# ============================================================================
# PARALLELIZATION: Script Generation (Independent of Provisioning)
# ============================================================================
# This resource generates deployment scripts immediately after RHEL instances exist.
# It does NOT wait for RHEL DSM provisioning to complete.
# 
# Execution Timeline:
# - aws_instance.rhel_dsm: Create instances (2 min)
# - edit_user_data_script: Generate scripts (30 sec) [PARALLEL with DSM provisioning]
# - provision-agent-*: Windows provisioning starts (once scripts ready)
# 
# Benefit: Saves 20-30 minutes by parallelizing DSM provisioning with Windows setup
# ============================================================================

resource "null_resource" "edit_user_data_script" {
    # Ensure the script is executable
    provisioner "local-exec" {
        command = "chmod +x scripts/AgentDeploymentScript/generateAllAgentDeploymentScript.sh"
    }

    # Run the script for each rhel_dsm instance
    # Only waits for instance resources to exist (have private_ip values)
    # Does NOT wait for DSM provisioning to complete (runs in parallel)
    provisioner "local-exec" {
        command = join(" && ", [
            for ip in aws_instance.rhel_dsm[*].private_ip :
            "/bin/bash scripts/AgentDeploymentScript/generateAllAgentDeploymentScript.sh ${ip}"
        ])
    }

    # Dependency: Only instances need to exist, not provisioning to complete
    depends_on = [
        aws_instance.rhel_dsm
    ]
}

# Safety buffer to ensure instances are fully booted before Windows provisioning starts
# This allows RHEL DSM provisioning to continue while Windows instances boot
resource "time_sleep" "wait_for_instance_readiness" {
    depends_on = [
        null_resource.edit_user_data_script
    ]
    
    # 15s total: ~5s for networking + ~10s for WinRM readiness
    # RHEL DSM provisioning continues in parallel during this time
    create_duration = "15s"
}