# Offline plan checks (mocked providers: no cloud calls, no credentials).
mock_provider "oci" {}
mock_provider "random" {}
mock_provider "time" {}

variables {
  tenancy_ocid        = "ocid1.tenancy.oc1..root"
  region              = "eu-frankfurt-1"
  name_prefix         = "vash"
  availability_domain = "test:EU-FRANKFURT-1-AD-1"
  image_id            = "ocid1.image.oc1..u"
  ssh_public_key      = "ssh-rsa AAAA test"
  admin_cidr          = "198.51.100.1/32"
  cloud_init_script   = "vash-runner.sh"
  compartments = {
    app      = { name = "vash", id = "", description = "VASH" }
    security = { name = "security", id = "", description = "Vaults and keys" }
    network  = { name = "network", id = "", description = "Networks" }
  }
}

run "empty_tenancy_makes_everything" {
  command = plan
  variables {
    create_database  = true
    notify_email     = "owner@example.com"
    budget_email     = "owner@example.com"
    quota_statements = ["zero compute-core quotas in tenancy"]
  }
  assert {
    condition = (length(module.compartment) == 3 && length(module.vault) == 1 && length(module.key) == 1
      && length(module.vcn) == 1 && length(module.instance) == 1 && length(module.database) == 1
    && length(oci_vault_secret.db_admin) == 1 && length(module.quota) == 1 && length(module.notification) == 1)
    error_message = "An empty tenancy must get its 3 compartments, vault, key, network, VM, database and guardrails."
  }
}

run "existing_objects_are_only_referenced" {
  command = plan
  variables {
    compartments = {
      app      = { name = "vash", id = "ocid1.compartment..app", description = "" }
      security = { name = "security", id = "ocid1.compartment..sec", description = "" }
      network  = { name = "network", id = "ocid1.compartment..net", description = "" }
    }
    vault_id       = "ocid1.vault..v"
    vault_endpoint = "https://v-management.kms.eu-frankfurt-1.oraclecloud.com"
    key_id         = "ocid1.key..k"
    subnet_id      = "ocid1.subnet..s"
  }
  assert {
    condition = (length(module.compartment) == 0 && length(module.vault) == 0 && length(module.key) == 0
    && length(module.vcn) == 0 && length(time_sleep.iam) == 0)
    error_message = "Existing compartments, vault, key and subnet must not be made again."
  }
}

run "database_only" {
  command = plan
  variables {
    create_vm       = false
    create_database = true
  }
  assert {
    condition     = length(module.instance) == 0 && length(module.vcn) == 0 && length(module.database) == 1
    error_message = "--database-only makes no VM and no network."
  }
}

run "basic_amd_micro" {
  command = plan
  variables {
    shape         = "VM.Standard.E2.1.Micro"
    ocpus         = 1
    memory_in_gbs = 1
  }
}
