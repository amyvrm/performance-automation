output "dsm-public-ip" {
  value = "${aws_instance.rhel_dsm.public_ip}"
}

output "dsm-public-dns" {
  value = "${aws_instance.rhel_dsm.public_dns}"
}

output "dsm-private-ip" {
  value = "${aws_instance.rhel_dsm.private_ip}"
}

output "dsm-private-dns" {
  value = "${aws_instance.rhel_dsm.private_dns}"
}

output "dsm-primary-nic-id" {
  value = "${aws_instance.rhel_dsm.primary_network_interface_id}"
}

output "dsm-security-groups" {
  value = "${aws_instance.rhel_dsm.security_groups}"
}

output "dsm-login-url" {
  value = "https://${aws_instance.rhel_dsm.public_dns}:4119"
}

output "dsm-login-user" {
  value = "${var.dsm-user}"
}

output "dsm-login-password" {
  value = "${var.dsm-password}"
}

output "pem-file" {
  value = "${var.auth_file_path}/${var.terraform_user}.pem"
}

output "pkg-path" {
	value = "C:\\temp\\"
}

output "region" {
  value = "${var.common_region}"
}