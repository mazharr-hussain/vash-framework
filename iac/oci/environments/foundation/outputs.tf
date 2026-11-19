output "compartment_ids" { value = { for name, m in module.compartment : name => m.compartment_tf_id } }
output "vaults" {
  value = { for name, m in module.vault : name => { id = m.vault_tf_id, management_endpoint = m.management_endpoint_tf_id } }
}
output "key_ids" { value = { for name, m in module.key : name => m.key_tf_id } }

output "databases" {
  value = { for name, db in module.database : name => { id = db.db_id, db_name = db.db_name } }
}
