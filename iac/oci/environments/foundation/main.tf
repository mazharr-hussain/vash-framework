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

# Free-tier guardrails (asked in onboarding): a quota policy that zeroes paid families and allows only the
# Always Free amounts (OCI refuses anything beyond it), and a monthly budget that e-mails at the first spend
# and when spend is forecast (it only warns; OCI has no hard spending cap).
module "quota" {
  count             = length(var.quota_statements) > 0 ? 1 : 0
  source            = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/governance/quota-policy?ref=v2026.2.2"
  tenancy_ocid      = var.tenancy_ocid
  quota_name        = "vash-free-tier"
  quota_description = "VASH: only Always Free amounts can be created"
  quota_statements  = var.quota_statements
  freeform_tags     = {}
}

module "budget" {
  count             = var.budget_email != "" ? 1 : 0
  source            = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/costmanagement/budget?ref=v2026.2.2"
  compartment_id    = var.tenancy_ocid
  amount            = var.budget_amount
  reset_period      = "MONTHLY"
  display_name      = "vash-free-tier"
  description       = "VASH: e-mail as soon as anything costs money"
  target_type       = "COMPARTMENT"
  targets           = [var.tenancy_ocid]
  budget_start_date = null
  budget_end_date   = null
  freeform_tags     = {}
}

module "budget_alert" {
  for_each       = var.budget_email != "" ? { actual = "ACTUAL", forecast = "FORECAST" } : {}
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/costmanagement/budget-alert-rule?ref=v2026.2.2"
  budget_id      = module.budget[0].budget_tf_id
  type           = each.value
  threshold_type = "PERCENTAGE"
  threshold      = each.key == "actual" ? "1" : "100"
  display_name   = "vash-${each.key}-spend"
  description    = each.key == "actual" ? "Something has started to cost money" : "This month is forecast to cost money"
  message        = "VASH free-tier guardrail: the tenancy is spending money. Check Billing, Cost Analysis."
  recipients     = var.budget_email
  freeform_tags  = {}
}
