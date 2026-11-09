terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0"
    }
  }
}

provider "oci" {
  region              = var.region
  auth                = var.oci_auth
  config_file_profile = var.oci_auth == "ApiKey" ? var.config_file_profile : null
}

module "networking" {
  count          = var.subnet_id == "" ? 1 : 0
  source         = "../../modules/networking"
  compartment_id = var.compartment_id
  admin_cidr     = var.admin_cidr
}

module "compute" {
  source              = "../../modules/compute"
  compartment_id      = var.compartment_id
  availability_domain = var.availability_domain
  image_id            = var.image_id
  subnet_id           = var.subnet_id != "" ? var.subnet_id : module.networking[0].subnet_id
  ssh_public_key      = var.ssh_public_key
  ocpus               = var.ocpus
  memory_in_gbs       = var.memory_in_gbs
  user_data           = var.user_data
}

module "database" {
  count          = var.create_database ? 1 : 0
  source         = "../../modules/database"
  compartment_id = var.compartment_id
  admin_password = var.admin_password
}
