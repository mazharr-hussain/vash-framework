terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0"
    }
  }
}

provider "oci" {
  config_file_profile = "DEFAULT"
}

module "networking" {
  source         = "../../modules/networking"
  compartment_id = var.compartment_id
  admin_cidr     = var.admin_cidr
}

module "compute" {
  source              = "../../modules/compute"
  compartment_id      = var.compartment_id
  availability_domain = var.availability_domain
  image_id            = var.image_id
  subnet_id           = module.networking.subnet_id
  ssh_public_key      = var.ssh_public_key
}

module "database" {
  source         = "../../modules/database"
  compartment_id = var.compartment_id
  admin_password = var.admin_password
}
