# foundation

Compartments, vaults and keys that `vash onboard oci` creates, built with Oracle's CD3 Automation Toolkit
modules (`identity/iam-compartment`, `security/vault`, `security/key`, release v2026.2.2).

Onboarding writes `terraform.tfvars.json` (maps `compartments`, `vaults`, `keys`) and applies; each new
choice adds one entry, so what already exists is left as it is. Compartments are created with
`enable_delete = false`: `terraform destroy` never removes them. Vaults are virtual (free); keys are
AES-256 in the vault's HSM.
