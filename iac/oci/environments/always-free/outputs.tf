output "runner_ip" { value = module.compute.public_ip }
output "instance_id" { value = module.compute.instance_id }
output "db_id" { value = var.create_database ? module.database[0].db_id : null }
