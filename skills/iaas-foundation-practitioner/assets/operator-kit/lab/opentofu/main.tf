provider "openstack" {
  # The profile is read from the operator-supplied clouds.yaml file.
  cloud = var.openstack_cloud
}

data "openstack_networking_network_v2" "vm" {
  name = var.vm_network_name
}

data "openstack_networking_network_v2" "floating_ip_pool" {
  name     = var.floating_ip_network_name
  external = true
  status   = "ACTIVE"
}

resource "openstack_networking_secgroup_v2" "https" {
  name        = var.security_group_name
  description = "Allow HTTPS from the documentation client range"
}

resource "openstack_networking_secgroup_rule_v2" "https" {
  security_group_id = openstack_networking_secgroup_v2.https.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = var.approved_https_cidr
}

resource "openstack_blockstorage_volume_v3" "data" {
  name              = "${var.vm_name}-data"
  description       = "Persistent data volume for ${var.vm_name}"
  size              = var.volume_size_gib
  volume_type       = var.volume_type
  availability_zone = var.volume_availability_zone

  lifecycle {
    prevent_destroy = true
  }
}

resource "openstack_compute_instance_v2" "web" {
  name              = var.vm_name
  image_id          = var.image_id
  flavor_name       = var.flavor_name
  security_groups   = [openstack_networking_secgroup_v2.https.name]
  availability_zone = var.compute_availability_zone

  network {
    uuid = data.openstack_networking_network_v2.vm.id
  }
}

resource "openstack_compute_volume_attach_v2" "data" {
  instance_id = openstack_compute_instance_v2.web.id
  volume_id   = openstack_blockstorage_volume_v3.data.id
}

resource "openstack_networking_floatingip_v2" "public" {
  pool = data.openstack_networking_network_v2.floating_ip_pool.name
}

resource "openstack_networking_floatingip_associate_v2" "public" {
  floating_ip = openstack_networking_floatingip_v2.public.address
  port_id     = openstack_compute_instance_v2.web.network[0].port
}

output "floating_ip_address" {
  description = "The public address assigned to the VM. Use it for the next HTTPS check."
  value       = openstack_networking_floatingip_v2.public.address
}

output "openstack_cloud" {
  description = "The local clouds.yaml profile used for this deployment."
  value       = var.openstack_cloud
}

output "server_id" {
  description = "The Nova server identifier used for cross-service validation."
  value       = openstack_compute_instance_v2.web.id
}

output "port_id" {
  description = "The Neutron port identifier attached to the VM."
  value       = openstack_compute_instance_v2.web.network[0].port
}

output "security_group_id" {
  description = "The Neutron security-group identifier attached to the VM port."
  value       = openstack_networking_secgroup_v2.https.id
}

output "floating_ip_id" {
  description = "The Neutron floating-IP identifier used for association validation."
  value       = openstack_networking_floatingip_v2.public.id
}

output "volume_id" {
  description = "The Cinder volume identifier for the data volume."
  value       = openstack_blockstorage_volume_v3.data.id
}
