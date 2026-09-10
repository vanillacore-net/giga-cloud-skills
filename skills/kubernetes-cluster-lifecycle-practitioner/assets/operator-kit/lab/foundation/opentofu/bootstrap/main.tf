data "openstack_networking_network_v2" "external" {
  name = var.external_network_name
}

locals {
  common_metadata = {
    "managed-by"      = "opentofu"
    "chapter"         = "4"
    "ownership-token" = var.ownership_token
  }
}

resource "openstack_networking_network_v2" "management" {
  name           = "${var.name_prefix}-network"
  admin_state_up = true
}

resource "openstack_networking_subnet_v2" "management" {
  name            = "${var.name_prefix}-subnet"
  network_id      = openstack_networking_network_v2.management.id
  cidr            = var.management_cidr
  ip_version      = 4
  enable_dhcp     = true
  dns_nameservers = var.dns_nameservers
}

resource "openstack_networking_router_v2" "management" {
  name                = "${var.name_prefix}-router"
  external_network_id = data.openstack_networking_network_v2.external.id
}

resource "openstack_networking_router_interface_v2" "management" {
  router_id = openstack_networking_router_v2.management.id
  subnet_id = openstack_networking_subnet_v2.management.id
}

resource "openstack_compute_keypair_v2" "management" {
  name       = "${var.name_prefix}-key"
  public_key = var.ssh_public_key
}

resource "openstack_networking_secgroup_v2" "gateway" {
  name        = "${var.name_prefix}-gateway"
  description = "Restricted administration entry for the Chapter 4 foundation"
}

resource "openstack_networking_secgroup_rule_v2" "gateway_ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.admin_source_cidr
  security_group_id = openstack_networking_secgroup_v2.gateway.id
}

resource "openstack_networking_secgroup_rule_v2" "gateway_internal" {
  direction         = "ingress"
  ethertype         = "IPv4"
  remote_ip_prefix  = var.management_cidr
  security_group_id = openstack_networking_secgroup_v2.gateway.id
}

resource "openstack_networking_secgroup_v2" "seed" {
  name        = "${var.name_prefix}-seed"
  description = "Private seed API and administration from the management subnet"
}

resource "openstack_networking_secgroup_rule_v2" "seed_internal" {
  direction         = "ingress"
  ethertype         = "IPv4"
  remote_ip_prefix  = var.management_cidr
  security_group_id = openstack_networking_secgroup_v2.seed.id
}

resource "openstack_networking_port_v2" "gateway" {
  name               = "${var.name_prefix}-gateway"
  network_id         = openstack_networking_network_v2.management.id
  admin_state_up     = true
  security_group_ids = [openstack_networking_secgroup_v2.gateway.id]

  fixed_ip {
    subnet_id  = openstack_networking_subnet_v2.management.id
    ip_address = var.gateway_private_ip
  }
}

resource "openstack_networking_port_v2" "seed" {
  name               = "${var.name_prefix}-seed"
  network_id         = openstack_networking_network_v2.management.id
  admin_state_up     = true
  security_group_ids = [openstack_networking_secgroup_v2.seed.id]

  fixed_ip {
    subnet_id  = openstack_networking_subnet_v2.management.id
    ip_address = var.seed_private_ip
  }
}

resource "openstack_compute_instance_v2" "gateway" {
  name              = "${var.name_prefix}-gateway"
  image_id          = var.base_image_id
  flavor_id         = var.gateway_flavor_id
  key_pair          = openstack_compute_keypair_v2.management.name
  availability_zone = var.compute_availability_zone
  metadata          = local.common_metadata

  network {
    port = openstack_networking_port_v2.gateway.id
  }

  user_data = file("${path.module}/cloud-init.yaml")

  depends_on = [openstack_networking_router_interface_v2.management]
}

resource "openstack_compute_instance_v2" "seed" {
  name              = "${var.name_prefix}-seed"
  image_id          = var.base_image_id
  flavor_id         = var.seed_flavor_id
  key_pair          = openstack_compute_keypair_v2.management.name
  availability_zone = var.compute_availability_zone
  metadata          = local.common_metadata

  network {
    port = openstack_networking_port_v2.seed.id
  }

  user_data = file("${path.module}/cloud-init.yaml")

  depends_on = [openstack_networking_router_interface_v2.management]
}

resource "openstack_networking_floatingip_v2" "gateway" {
  pool = var.external_network_name
}

resource "openstack_networking_floatingip_associate_v2" "gateway" {
  floating_ip = openstack_networking_floatingip_v2.gateway.address
  port_id     = openstack_networking_port_v2.gateway.id
}
