output "compartment_ids" { value = local.compartment_id }
output "vault_id" { value = local.vault_id }
output "vault_endpoint" { value = local.vault_endpoint }
output "key_id" { value = local.key_id }
output "runner_ip" { value = var.create_vm ? data.oci_core_vnic.runner[0].public_ip_address : null }
output "instance_id" { value = var.create_vm ? module.instance[0].instance_tf_id : null }
output "db_id" { value = var.create_database ? module.database[0].db_id : null }
output "db_password_secret" { value = var.create_database ? oci_vault_secret.db_admin[0].secret_name : null }
