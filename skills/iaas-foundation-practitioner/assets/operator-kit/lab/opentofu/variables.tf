variable "openstack_cloud" {
  description = "Profile name in the operator-supplied clouds.yaml file."
  type        = string
}

variable "vm_name" {
  description = "Name for the virtual machine and the derived data volume."
  type        = string
  default     = "web-01"
}

variable "security_group_name" {
  description = "Name of the security group used by the worked example."
  type        = string
  default     = "web-https"
}

variable "image_id" {
  description = "Immutable identifier of the approved boot image, supplied by the image owner."
  type        = string
}

variable "flavor_name" {
  description = "Flavor that supplies the VM's virtual CPU and memory."
  type        = string
}

variable "vm_network_name" {
  description = "Project network to which the VM is connected."
  type        = string
}

variable "floating_ip_network_name" {
  description = "Operator-provided network from which a floating IP is allocated."
  type        = string
}

variable "approved_https_cidr" {
  description = "Approved IPv4 source range for TCP port 443, supplied by the service and network owners."
  type        = string
}

variable "volume_type" {
  description = "Cinder volume type approved for the service data."
  type        = string
}

variable "volume_size_gib" {
  description = "Size of the separate service-data volume, in GiB."
  type        = number
  default     = 1

  validation {
    condition     = var.volume_size_gib > 0
    error_message = "volume_size_gib must be greater than zero."
  }
}

variable "compute_availability_zone" {
  description = "Nova availability zone selected for the virtual machine."
  type        = string
}

variable "volume_availability_zone" {
  description = "Cinder availability zone selected for the data volume."
  type        = string
}
