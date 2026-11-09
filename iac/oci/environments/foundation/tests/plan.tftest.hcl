# Offline plan checks (terraform test with a mocked oci provider: no cloud calls, no credentials).
mock_provider "oci" {}

variables {
  region       = "me-jeddah-1"
  tenancy_ocid = "ocid1.tenancy.oc1..test"
  oci_auth     = "InstancePrincipal"
}

run "nothing_by_default" {
  command = plan
  assert {
    condition     = length(module.compartment) == 0 && length(module.vault) == 0 && length(module.key) == 0
    error_message = "Empty maps must create nothing."
  }
}

run "compartment_vault_and_key" {
  command = plan
  variables {
    compartments = { security = "Vaults and keys of every application" }
    vaults       = { "security-vault" = { compartment_id = "ocid1.compartment.oc1..sec" } }
    keys = {
      "vash-secrets-key" = { compartment_id = "ocid1.compartment.oc1..sec", management_endpoint = "https://test-management.kms.me-jeddah-1.oraclecloud.com" }
    }
  }
  assert {
    condition     = length(module.compartment) == 1 && length(module.vault) == 1 && length(module.key) == 1
    error_message = "One entry in each map must plan one compartment, one vault and one key."
  }
}
