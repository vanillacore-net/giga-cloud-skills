output "gateway_public_ip" {
  description = "Public address of the restricted administration gateway."
  value       = openstack_networking_floatingip_v2.gateway.address
}

output "gateway_private_ip" {
  description = "Private address used by the gateway on the management subnet."
  value       = var.gateway_private_ip
}

output "seed_private_ip" {
  description = "Private address and stable single-node API endpoint of the seed."
  value       = var.seed_private_ip
}

output "management_network_id" {
  description = "Network UUID recorded for later discovery and routing checks."
  value       = openstack_networking_network_v2.management.id
}

output "management_subnet_id" {
  description = "Subnet UUID recorded for later discovery and routing checks."
  value       = openstack_networking_subnet_v2.management.id
}

output "seed_server_id" {
  description = "Stable server UUID used when verifying the OpenTofu resource chain."
  value       = openstack_compute_instance_v2.seed.id
}

output "gateway_security_group_id" {
  description = "Security-group UUID used to verify the reviewed administration-source rule."
  value       = openstack_networking_secgroup_v2.gateway.id
}
