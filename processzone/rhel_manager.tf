resource "aws_instance" "rhel_dsm" {
  count                        = var.instance_count + 1
  ami                          = var.red_hat_ami
  instance_type                = var.dsm_instance_type
  key_name                     = var.ssh_key_name
  associate_public_ip_address  = "true"
  subnet_id                    = var.subnet_id
  security_groups              = [var.wfh_sg]
  iam_instance_profile         = var.instance_profile

  tags = {
    Name           = "${var.tag_dsm_name}_${var.random_num}_${count.index}"
    "Trender"      = var.tag_trender
    "Automation"   = var.tag_automation
    "ValidUntil"   = formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))
    "workingHours" = "IGNORE"
  }

  # Use self references to avoid dependency cycles
  connection {
    type        = "ssh"
    host        = self.private_ip
    timeout     = var.conn_timeout
    user        = "ec2-user"
    private_key = file(var.ssh_key)
  }

  provisioner "file" {
    source      = "scripts/RedHat/"
    destination = "/tmp"
  }

  provisioner "remote-exec" {
    inline = [
      # Fast chmod for all scripts in one go
      "chmod +x /tmp/setupDSMInstall.sh /tmp/generatePropertiesDSM.sh /tmp/restartDSM.sh /tmp/setupPython3.6.sh /tmp/downloadAgents.sh /tmp/uploadDSAToDSM.py",
      "sudo sh /tmp/setupDSMInstall.sh ${var.dsm_redhat_url} ${var.dsm_license}",
      "sh /tmp/downloadAgents.sh ${var.all_agent_urls}",
        "echo 'Waiting for DSM web service to be ready...' && for i in {1..60}; do if curl -sf https://localhost:4119/webservice/Manager?WSDL > /dev/null 2>&1; then echo '✓ DSM web service ready on attempt $i'; exit 0; fi; if [ $((i % 6)) -eq 0 ]; then echo \"Attempt $i/60 - DSM not ready yet...\"; fi; sleep 5; done && echo '✓ DSM ready' || echo '⚠️ DSM health check timed out - continuing anyway'"
    ]
  }

  root_block_device {
    volume_size = var.volume_size
  }
}