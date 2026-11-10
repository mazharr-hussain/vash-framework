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

run "free_tier_guardrails" {
  command = plan
  variables {
    quota_statements = ["zero compute-core quotas in tenancy", "set compute-core quota standard-a1-core-count to 4 in tenancy"]
    budget_email     = "owner@example.com"
  }
  assert {
    condition     = length(module.quota) == 1 && length(module.budget) == 1 && length(module.budget_alert) == 2
    error_message = "Guardrails must plan one quota policy, one budget and two alert rules."
  }
}

run "no_guardrails_by_default" {
  command = plan
  assert {
    condition     = length(module.quota) == 0 && length(module.budget) == 0 && length(module.budget_alert) == 0
    error_message = "Without statements or an e-mail nothing is created."
  }
}
