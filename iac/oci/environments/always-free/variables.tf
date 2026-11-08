variable "compartment_id" { type = string }
variable "availability_domain" { type = string }
variable "image_id" { type = string }
variable "admin_cidr" { type = string }
variable "ssh_public_key" { type = string }
variable "admin_password" {
  type      = string
  sensitive = true
}
