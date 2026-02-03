output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "RDS instance address (hostname)"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "rds_database_name" {
  description = "Name of the database"
  value       = aws_db_instance.postgres.db_name
}

output "rds_username" {
  description = "Master username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "rds_security_group_id" {
  description = "Security group ID for the RDS instance"
  value       = aws_security_group.rds_sg.id
}

output "connection_string" {
  description = "PostgreSQL connection string (without password)"
  value       = "postgresql://${aws_db_instance.postgres.username}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}
