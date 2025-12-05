output "instance_name" {
  description = "The name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "instance_connection_name" {
  description = "The connection name for Cloud SQL Proxy"
  value       = google_sql_database_instance.main.connection_name
}

output "database_name" {
  description = "The name of the database"
  value       = google_sql_database.database.name
}

output "database_user" {
  description = "The database user name"
  value       = google_sql_user.user.name
}

output "database_password" {
  description = "The database user password"
  value       = random_password.db_password.result
  sensitive   = true
}

output "instance_ip_address" {
  description = "The IPv4 address of the instance"
  value       = google_sql_database_instance.main.public_ip_address
}

output "database_url" {
  description = "Database connection URL for Django"
  value       = "postgres://${google_sql_user.user.name}:${random_password.db_password.result}@//${google_sql_database.database.name}?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
  sensitive   = true
}
