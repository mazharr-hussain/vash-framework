# VASH in one OCI Resource Manager stack: compartments, vault and key, free-tier guardrails, network, VM,
# e-mail topic and the Always Free database, in one terraform graph. Resource Manager runs it in OCI (free), so
# the setup keeps going when the browser or laptop is closed, and terraform builds everything that does not depend
# on something else at the same time (waves: compartments; then vault and key, network and VM; then the
# database password secret and the database).
# Oracle's CD3 Automation Toolkit modules (UPL-1.0) at release v2026.2.2, as in the other environments; the
# vault secret and the database password use the vendors' own providers (CD3 has no secrets module, and its adb
# module has no free-tier option: catalog/search-log.md).
# Something that already exists (a compartment, the vault, the key, a subnet) is passed by its OCID and only
# referenced, never changed.
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.9"
    }
  }
}

# Resource Manager signs in as the user who runs the job: no auth settings here.
provider "oci" {
  region              = var.region
  ignore_defined_tags = ["Oracle-Tags.CreatedBy", "Oracle-Tags.CreatedOn"]
}

locals {
  cd3 = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules"

  new_compartments = { for k, c in var.compartments : k => c if c.id == "" }
  compartment_id   = { for k, c in var.compartments : k => (c.id != "" ? c.id : module.compartment[k].compartment_tf_id) }

  vault_id       = var.vault_id != "" ? var.vault_id : module.vault[0].vault_tf_id
  vault_endpoint = var.vault_id != "" ? var.vault_endpoint : module.vault[0].management_endpoint_tf_id
  key_id         = var.key_id != "" ? var.key_id : module.key[0].key_tf_id

  create_network = var.create_vm && var.subnet_id == ""
  network_key    = var.name_prefix
  no_options     = { tcp = [], udp = [], icmp = [] }
  notify         = var.notify_email != ""
}

# ---- wave 1: compartments under the root ----------------------------------------------------------------------
module "compartment" {
  for_each                = local.new_compartments
  source                  = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/identity/iam-compartment?ref=v2026.2.2"
  tenancy_ocid            = var.tenancy_ocid
  compartment_name        = each.value.name
  compartment_description = each.value.description
  enable_delete           = false # a compartment is never removed by a destroy
}

# IAM shows a new compartment to other services after a short delay (seen live as NotAuthorizedOrNotFound).
resource "time_sleep" "iam" {
  count           = length(local.new_compartments) > 0 ? 1 : 0
  depends_on      = [module.compartment]
  create_duration = "90s"
}

# Free-tier guardrails: a quota policy that allows only the Always Free amounts, and a budget e-mail.
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
  amount            = 1
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

# ---- wave 2a: vault and key (security compartment) ------------------------------------------------------------
module "vault" {
  count          = var.vault_id == "" ? 1 : 0
  depends_on     = [time_sleep.iam]
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/security/vault?ref=v2026.2.2"
  compartment_id = local.compartment_id["security"]
  display_name   = var.vault_name
  vault_type     = "DEFAULT" # virtual vault: the free one
  replica_region = null
}

# A new vault's management address is not in DNS for the first minutes (seen live in Frankfurt).
resource "time_sleep" "vault_dns" {
  count           = var.vault_id == "" ? 1 : 0
  depends_on      = [module.vault]
  create_duration = "300s"
}

module "key" {
  count               = var.key_id == "" ? 1 : 0
  depends_on          = [time_sleep.vault_dns]
  source              = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/security/key?ref=v2026.2.2"
  compartment_id      = local.compartment_id["security"]
  display_name        = var.key_name
  management_endpoint = local.vault_endpoint
  algorithm           = "AES"
  length              = 32 # AES-256
  protection_mode     = "HSM"
}

# ---- wave 2b: network (network compartment) and VM (VASH compartment) -----------------------------------------
module "vcn" {
  count          = local.create_network ? 1 : 0
  depends_on     = [time_sleep.iam]
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/network/vcn?ref=v2026.2.2"
  compartment_id = local.compartment_id["network"]
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "${var.name_prefix}-vcn"
}

module "igw" {
  count          = local.create_network ? 1 : 0
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/network/igw?ref=v2026.2.2"
  compartment_id = local.compartment_id["network"]
  vcn_id         = module.vcn[0].vcn_tf_id
  display_name   = "${var.name_prefix}-igw"
  enabled        = true
}

module "route_table" {
  count          = local.create_network ? 1 : 0
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/network/route-table?ref=v2026.2.2"
  compartment_id = local.compartment_id["network"]
  vcn_id         = module.vcn[0].vcn_tf_id
  display_name   = "${var.name_prefix}-rt"
  key_name       = local.network_key
  igw_id         = { "${var.name_prefix}-igw" = { igw_tf_id = module.igw[0].igw_tf_id } }
  rt_details = {
    (local.network_key) = {
      route_rules_ip  = []
      route_rules_lpg = []
      route_rules_drg = []
      route_rules_ngw = []
      route_rules_sgw = []
      route_rules_igw = [{
        network_entity_id = "${var.name_prefix}-igw"
        description       = "Internet"
        destination       = "0.0.0.0/0"
        destination_type  = "CIDR_BLOCK"
      }]
    }
  }
}

module "security_list" {
  count          = local.create_network ? 1 : 0
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/network/sec-list?ref=v2026.2.2"
  compartment_id = local.compartment_id["network"]
  vcn_id         = module.vcn[0].vcn_tf_id
  display_name   = "${var.name_prefix}-sl"
  key_name       = local.network_key
  seclist_details = {
    (local.network_key) = {
      ingress_sec_rules = [{
        protocol    = "6"
        source      = var.admin_cidr
        source_type = "CIDR_BLOCK"
        description = "SSH from the onboarding shell"
        stateless   = false
        options = {
          tcp = [{
            destination_port_range_min = 22
            destination_port_range_max = 22
            source_port_range_min      = null
            source_port_range_max      = null
          }]
          udp  = []
          icmp = []
        }
      }]
      egress_sec_rules = [{
        protocol         = "all"
        destination      = "0.0.0.0/0"
        destination_type = "CIDR_BLOCK"
        description      = "All outbound"
        stateless        = false
        options          = local.no_options
      }]
    }
  }
}

module "subnet" {
  count                        = local.create_network ? 1 : 0
  source                       = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/network/subnet?ref=v2026.2.2"
  compartment_id               = local.compartment_id["network"]
  vcn_id                       = module.vcn[0].vcn_tf_id
  cidr_block                   = "10.0.0.0/24"
  display_name                 = "${var.name_prefix}-subnet"
  prohibit_public_ip_on_vnic   = false
  route_table_id               = module.route_table[0].route_table_ids
  security_list_ids            = [module.security_list[0].seclist_tf_id]
  vcn_default_security_list_id = module.vcn[0].vcn_default_security_list_id
  custom_security_list_id      = {}
}

module "instance" {
  count               = var.create_vm ? 1 : 0
  depends_on          = [time_sleep.iam]
  source              = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/compute/instance?ref=v2026.2.2"
  compartment_id      = local.compartment_id["app"]
  availability_domain = var.availability_domain
  display_name        = "${var.name_prefix}-runner"
  shape               = var.shape
  ocpu_count          = var.ocpus
  memory_in_gbs       = var.memory_in_gbs
  source_type         = "image"
  source_image_id     = var.image_id
  subnet_id           = local.create_network ? module.subnet[0].subnet_tf_id : var.subnet_id
  assign_public_ip    = true
  ssh_public_keys     = var.ssh_public_key
  cloud_init_script   = var.cloud_init_script # scripts/<name> beside this file, written by onboarding
  plugins_details     = []
  boot_tf_policy      = null
  launch_options      = null
  nsg_ids             = null
}

data "oci_core_vnic_attachments" "runner" {
  count          = var.create_vm ? 1 : 0
  compartment_id = local.compartment_id["app"]
  instance_id    = module.instance[0].instance_tf_id
}

data "oci_core_vnic" "runner" {
  count   = var.create_vm ? 1 : 0
  vnic_id = data.oci_core_vnic_attachments.runner[0].vnic_attachments[0].vnic_id
}

module "notification" {
  count          = local.notify ? 1 : 0
  depends_on     = [time_sleep.iam]
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/managementservices/notification?ref=v2026.2.2"
  compartment_id = local.compartment_id["app"]
  topic_name     = "${var.name_prefix}-notifications"
  description    = "VASH: e-mails about the runner VM"
  subscriptions  = [{ protocol = "EMAIL", endpoint = var.notify_email }]
}

# ---- wave 3: the database password (vault secret) and the Always Free database --------------------------------
# The password is made here and kept only in the vault secret and in Resource Manager's encrypted state: no person
# and no file sees it. It starts with a letter, as the database's rules expect. A secret that already exists (an
# earlier run, seen live) is passed by its OCID and its password is read from the vault instead.
locals {
  new_secret  = var.create_database && var.db_secret_id == ""
  db_password = !var.create_database ? "" : (local.new_secret ? "V${random_password.db[0].result}" : try(base64decode(data.oci_secrets_secretbundle.db[0].secret_bundle_content[0].content), ""))
}

resource "random_password" "db" {
  count            = local.new_secret ? 1 : 0
  length           = 23
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 1
  override_special = "#_-"
}

data "oci_secrets_secretbundle" "db" {
  count     = var.create_database && var.db_secret_id != "" ? 1 : 0
  secret_id = var.db_secret_id
}

resource "oci_vault_secret" "db_admin" {
  count          = local.new_secret ? 1 : 0
  compartment_id = local.compartment_id["security"]
  vault_id       = local.vault_id
  key_id         = local.key_id
  secret_name    = var.db_secret_name != "" ? var.db_secret_name : "${var.name_prefix}-db-admin-password"
  description    = "Admin password of ${var.name_prefix}-db (made by the VASH stack)"
  secret_content {
    content_type = "BASE64"
    content      = base64encode(local.db_password)
  }
}

module "database" {
  count          = var.create_database ? 1 : 0
  depends_on     = [time_sleep.iam, oci_vault_secret.db_admin]
  source         = "../../modules/database"
  compartment_id = local.compartment_id["app"]
  admin_password = local.db_password
  name_prefix    = var.name_prefix
}
