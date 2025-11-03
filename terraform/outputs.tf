output "instance_public_ip" {
  description = "O IP público da instância EC2 (Elastic IP)."
  value       = aws_eip.keycloak_eip.public_ip
}

output "keycloak_url" {
  description = "A URL do console de administração do Keycloak."
  value       = "https://${var.domain_name}/v1/auth"
}

output "ssh_command" {
  description = "Comando SSH para se conectar à instância."
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.keycloak_eip.public_ip}"
}