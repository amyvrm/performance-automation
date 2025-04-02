output "dsm-login-user" {
  value = "${var.dsm-user}"
}

output "dsm-login-password" {
  value = "${var.dsm-password}"
}

output "pem-file" {
  value = "${var.ssh_key}"
}

output "pkg-path" {
	value = "C:\\temp\\"
}

output "region" {
  value = "${var.common_region}"
}

output "dsm-rhel-ids" {
  value = { for i, instance in aws_instance.rhel_dsm : "dsm-rhel-id-${i}" => instance.id }
}

output "dsm-private-ips" {
  value = { for i, instance in aws_instance.rhel_dsm : "dsm-private-ip-${i}" => instance.private_ip }
}

output "dsm-public-ips" {
  value = { for i, instance in aws_instance.rhel_dsm : "dsm-public-ip-${i}" => instance.public_ip }
}

output "dsa-windows-id" {
  value = length(aws_instance.windows_server2019_agent) > 0 ? aws_instance.windows_server2019_agent[0].id : null
}

output "dsa-public-ip" {
  value = length(aws_instance.windows_server2019_agent) > 0 ? aws_instance.windows_server2019_agent[0].public_ip : null
}

output "dsa-windows-agent-id-2" {
  value = length(aws_instance.windows_server2019_agent) > 1 ? aws_instance.windows_server2019_agent[1].id : null
}

output "dsa-public-agent-ip-2" {
  value = length(aws_instance.windows_server2019_agent) > 1 ? aws_instance.windows_server2019_agent[1].public_ip : null
}

output "dsa-windows_agent-ids" {
  value = { for i, instance in aws_instance.windows_server2019_agent : "dsa-windows_agent-id-${i}" => instance.id }
}

output "dsa-public_agent-ips" {
  value = { for i, instance in aws_instance.windows_server2019_agent : "dsa-public_agent-ip-${i}" => instance.public_ip }
}

output "dsa-private_agent-ips" {
  value = { for i, instance in aws_instance.windows_server2019_agent : "dsa-private_agent-ip-${i}" => instance.private_ip }
}

output "dsa-user" {
	value = "Administrator"
}

# Separate Output Blocks for Each Instance
output "dsa-windows-ids" {
  value = { for i, instance in aws_instance.windows_server2019 : "dsa-windows-id-${i}" => instance.id }
}

output "dsa-public-ips" {
  value = { for i, instance in aws_instance.windows_server2019 : "dsa-public-ip-${i}" => instance.public_ip }
}

output "dsa-private-ips" {
  value = { for i, instance in aws_instance.windows_server2019 : "dsa-private-ip-${i}" => instance.private_ip }
}

output "dsa-user-2" {
	value = "Administrator"
}

# Separate Output Blocks for Each Instance
output "dsa-windows-id-2" {
  value = length(aws_instance.windows_server2019) > 0 ? aws_instance.windows_server2019[0].id : null
}

output "dsa-public-ip-2" {
  value = length(aws_instance.windows_server2019) > 0 ? aws_instance.windows_server2019[0].public_ip : null
}

output "dsa-windows-id-2-2" {
  value = length(aws_instance.windows_server2019) > 1 ? aws_instance.windows_server2019[1].id : null
}

output "dsa-public-ip-2-2" {
  value = length(aws_instance.windows_server2019) > 1 ? aws_instance.windows_server2019[1].public_ip : null
}