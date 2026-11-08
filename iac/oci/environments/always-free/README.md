# OCI Always Free

The VASH runner: network, one A1 Flex VM (2 cores, 12 GB by default) and, when `create_database = true`, the free Autonomous Database.

`vash onboard oci` fills `terraform.tfvars.json` and runs it (see `bootstrap/README.md`). By hand: write the variables in `variables.tf`, then run `terraform init` and `terraform plan`.
