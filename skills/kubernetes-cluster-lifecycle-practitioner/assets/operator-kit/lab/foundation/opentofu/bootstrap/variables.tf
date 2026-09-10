variable "cloud_name" {
  description = "Name of the reviewed clouds.yaml profile."
  type        = string
}

variable "region" {
  description = "OpenStack region that contains the approved networks and compute capacity."
  type        = string
  default     = "RegionOne"
}

variable "name_prefix" {
  description = "Prefix used on every resource owned by this learning environment."
  type        = string
  default     = "c4-management"
}

variable "ownership_token" {
  description = "Non-secret label used to distinguish this environment from unrelated resources."
  type        = string
}

variable "external_network_name" {
  description = "Existing provider network used by the router and gateway floating IP."
  type        = string
}

variable "base_image_id" {
  description = "UUID of the approved general cloud image for the gateway and seed VM."
  type        = string
}

variable "gateway_flavor_id" {
  description = "UUID of the reviewed gateway flavor."
  type        = string
}

variable "seed_flavor_id" {
  description = "UUID of the reviewed seed flavor."
  type        = string
}

variable "compute_availability_zone" {
  description = "Explicit Nova availability zone selected during discovery."
  type        = string
}

variable "ssh_public_key" {
  description = "Public SSH key material. Never provide a private key here."
  type        = string
}

variable "admin_source_cidr" {
  description = "Public source CIDR allowed to reach the gateway over SSH."
  type        = string
}

variable "management_cidr" {
  description = "Private subnet for the gateway, seed and management API."
  type        = string
  default     = "10.42.0.0/24"
}

variable "gateway_private_ip" {
  description = "Fixed management-subnet address of the protected jump host."
  type        = string
  default     = "10.42.0.10"
}

variable "seed_private_ip" {
  description = "Fixed management-subnet address of the seed control-plane node."
  type        = string
  default     = "10.42.0.20"
}

variable "dns_nameservers" {
  description = "DNS resolvers reachable from the management subnet."
  type        = list(string)
}
