variable "compartment_id" { type = string }
variable "availability_domain" { type = string }
variable "image_id" { type = string }
variable "subnet_id" { type = string }
variable "ssh_public_key" { type = string }
variable "ocpus" {
  type    = number
  default = 2
}
variable "memory_in_gbs" {
  type    = number
  default = 12
}
variable "user_data" {
  type    = string
  default = ""
}
