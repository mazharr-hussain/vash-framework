variable "region" { type = string }
variable "tenancy_ocid" { type = string }
variable "oci_auth" {
  type        = string
  default     = "ApiKey"
  description = "Provider auth: ApiKey (config file) or InstancePrincipal (Cloud Shell)."
}
variable "config_file_profile" {
  type    = string
  default = "DEFAULT"
}
variable "compartments" {
  type        = map(string)
  default     = {}
  description = "Compartments to create under the root: name => description."
}
variable "vaults" {
  type        = map(object({ compartment_id = string }))
  default     = {}
  description = "Virtual vaults to create: display name => compartment."
}
variable "keys" {
  type        = map(object({ compartment_id = string, management_endpoint = string }))
  default     = {}
  description = "AES-256 HSM keys to create: display name => compartment and vault management endpoint."
}
variable "quota_statements" {
  type        = list(string)
  default     = []
  description = "Quota policy statements (free-tier guardrail); empty creates no quota policy."
}
variable "budget_email" {
  type        = string
  default     = ""
  description = "E-mail for the free-tier budget alerts; empty creates no budget."
}
variable "budget_amount" {
  type        = number
  default     = 1
  description = "Monthly budget in the account currency; alerts at 1% actual and 100% forecast."
}
