output "dashboard_url" {
  description = "URL of the deployed dashboard"
  value       = "http://${aws_lb.nz_habitat.dns_name}:8050"
}

output "prefect_ui_url" {
  description = "URL of the Prefect UI"
  value       = "http://${aws_lb.nz_habitat.dns_name}:4200"
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.nz_habitat.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.nz_habitat.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.nz_habitat_dashboard.name
}

output "s3_data_bucket" {
  description = "S3 bucket for data storage"
  value       = aws_s3_bucket.nz_habitat_data.id
}
