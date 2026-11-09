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
