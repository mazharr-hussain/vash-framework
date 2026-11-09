# Tenancy foundation for VASH: compartments, vaults and keys.
# Everything here is built with Oracle's CD3 Automation Toolkit modules (oracle-devrel/cd3-automation-toolkit,
# UPL-1.0), pinned to release v2026.2.2, the same release as the always-free environment.
# Onboarding adds entries to the maps in terraform.tfvars.json and applies again; what exists stays as it is.
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
  ignore_defined_tags = ["Oracle-Tags.CreatedBy", "Oracle-Tags.CreatedOn"]
}

module "compartment" {
  for_each                = var.compartments
  source                  = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/identity/iam-compartment?ref=v2026.2.2"
  tenancy_ocid            = var.tenancy_ocid
  compartment_name        = each.key
  compartment_description = each.value
  enable_delete           = false # a compartment is never removed by terraform destroy
}

module "vault" {
  for_each       = var.vaults
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/security/vault?ref=v2026.2.2"
  compartment_id = each.value.compartment_id
  display_name   = each.key
  vault_type     = "DEFAULT" # virtual vault: the free one
  replica_region = null
}

module "key" {
  for_each            = var.keys
  source              = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/security/key?ref=v2026.2.2"
  compartment_id      = each.value.compartment_id
  display_name        = each.key
  management_endpoint = each.value.management_endpoint
  algorithm           = "AES"
  length              = 32 # AES-256
  protection_mode     = "HSM"
}
