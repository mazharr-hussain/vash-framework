# VASH runner on OCI Always Free.
# Network and VM: Oracle's CD3 Automation Toolkit modules (oracle-devrel/cd3-automation-toolkit,
# UPL-1.0), pinned to release v2026.2.2. Free-tier Autonomous Database: VASH's own module, because the
# CD3 adb module has no is_free_tier option (vendor-first rule, reason in catalog/search-log.md).
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

locals {
  create_network = var.subnet_id == ""
  network_key    = var.name_prefix
  no_options     = { tcp = [], udp = [], icmp = [] }
}

module "vcn" {
  count          = local.create_network ? 1 : 0
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/network/vcn?ref=v2026.2.2"
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "${var.name_prefix}-vcn"
}

module "igw" {
  count          = local.create_network ? 1 : 0
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/network/igw?ref=v2026.2.2"
  compartment_id = var.compartment_id
  vcn_id         = module.vcn[0].vcn_tf_id
  display_name   = "${var.name_prefix}-igw"
  enabled        = true
}

module "route_table" {
  count          = local.create_network ? 1 : 0
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/network/route-table?ref=v2026.2.2"
  compartment_id = var.compartment_id
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
  compartment_id = var.compartment_id
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
  compartment_id               = var.compartment_id
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
  source              = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/compute/instance?ref=v2026.2.2"
  compartment_id      = var.compartment_id
  availability_domain = var.availability_domain
  display_name        = "${var.name_prefix}-runner"
  shape               = "VM.Standard.A1.Flex"
  ocpu_count          = var.ocpus
  memory_in_gbs       = var.memory_in_gbs
  source_type         = "image"
  source_image_id     = var.image_id
  subnet_id           = local.create_network ? module.subnet[0].subnet_tf_id : var.subnet_id
  assign_public_ip    = true
  ssh_public_keys     = var.ssh_public_key
  # The CD3 instance module reads scripts/<cloud_init_script> next to this file; onboarding writes it
  # before terraform runs (git-ignored, it is rendered per run).
  cloud_init_script = var.cloud_init_script
  # Two CD3 defaults break a plain instance (v2026.2.2): plugins_details defaults to null but the module
  # iterates over it, and boot_tf_policy defaults to "" which makes it look up a backup policy named "".
  plugins_details = []
  boot_tf_policy  = null # no boot volume backup policy (backups are paid beyond the free 5)
  launch_options  = null # the module reads element(launch_options, 0), which fails on its default []
  nsg_ids         = null # on its default [] the module sends the NSG "INVALID NSG Name" to OCI
}

data "oci_core_vnic_attachments" "runner" {
  compartment_id = var.compartment_id
  instance_id    = module.instance.instance_tf_id
}

data "oci_core_vnic" "runner" {
  vnic_id = data.oci_core_vnic_attachments.runner.vnic_attachments[0].vnic_id
}

module "database" {
  count          = var.create_database ? 1 : 0
  source         = "../../modules/database"
  compartment_id = var.compartment_id
  admin_password = var.admin_password
  name_prefix    = var.name_prefix
}

# E-mail about the VM: a Notifications topic with the owner's e-mail subscribed (CD3 managementservices
# notification module; Always Free). Onboarding publishes to it when the VM is launched, when VASH is ready
# and when the setup stops. OCI first e-mails a link that must be clicked to confirm the subscription.
# (An Events rule is not used: tenancies can have no Events rules left, seen live as LimitExceeded rule-count.)
locals {
  notify = var.notify_email != ""
}

module "notification" {
  count          = local.notify ? 1 : 0
  source         = "git::https://github.com/oracle-devrel/cd3-automation-toolkit.git//cd3_automation_toolkit/ocicloud/terraform/modules/managementservices/notification?ref=v2026.2.2"
  compartment_id = var.compartment_id
  topic_name     = "${var.name_prefix}-notifications"
  description    = "VASH: e-mails about the runner VM"
  subscriptions  = [{ protocol = "EMAIL", endpoint = var.notify_email }]
}
