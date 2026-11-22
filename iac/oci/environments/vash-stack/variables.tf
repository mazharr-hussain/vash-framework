# Resource Manager fills tenancy_ocid and region itself; onboarding sets the rest on the stack.
variable "tenancy_ocid" { type = string }
variable "region" { type = string }
variable "name_prefix" {
  type        = string
  description = "Prefix of every display name: <prefix>-runner, <prefix>-vcn, <prefix>-db ..."
}
variable "compartments" {
  type        = map(object({ name = string, id = string, description = string }))
  description = "app (the VM and the database), security (vault and key), network: an id reuses one, else it is made under the root."
}
variable "vault_id" {
  type    = string
  default = ""
}
variable "vault_endpoint" {
  type    = string
  default = ""
}
variable "vault_name" {
  type    = string
  default = "security-vault"
}
variable "key_id" {
  type    = string
  default = ""
}
variable "key_name" {
  type    = string
  default = "vash-secrets-key"
}
variable "quota_statements" {
  type    = list(string)
  default = []
}
variable "budget_email" {
  type    = string
  default = ""
}
variable "create_vm" {
  type    = bool
  default = true
}
variable "subnet_id" {
  type        = string
  default     = ""
  description = "An existing public subnet; empty makes the VASH network in the network compartment."
}
variable "admin_cidr" {
  type    = string
  default = "0.0.0.0/32"
}
variable "availability_domain" {
  type    = string
  default = ""
}
variable "shape" {
  type    = string
  default = "VM.Standard.A1.Flex"
}
variable "ocpus" {
  type    = number
  default = 2
}
variable "memory_in_gbs" {
  type    = number
  default = 12
}
variable "image_id" {
  type    = string
  default = ""
}
variable "ssh_public_key" {
  type    = string
  default = ""
}
variable "cloud_init_script" {
  type    = string
  default = null
}
variable "notify_email" {
  type    = string
  default = ""
}
variable "create_database" {
  type    = bool
  default = false
}
variable "db_secret_id" {
  type        = string
  default     = ""
  description = "An existing vault secret with the database password (it is read, not changed); empty makes one."
}
variable "db_secret_name" {
  type        = string
  default     = ""
  description = "Name of a new password secret; empty is <prefix>-db-admin-password."
}
