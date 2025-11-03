# Variáveis para a região AWS
variable "aws_region" {
  description = "A região da AWS onde os recursos serão provisionados."
  type        = string
  default     = "us-east-1" # Altere para a sua região desejada
}

# Variáveis para a instância EC2
variable "instance_type" {
  description = "O tipo da instância EC2 (ex: t2.medium)."
  type        = string
  default     = "t2.medium"
}

variable "ami_id" {
  description = "ID da AMI para Ubuntu Server 22.04 LTS."
  type        = string
  default     = "ami-053b0d53c279acc7c" # Ubuntu Server 22.04 LTS (HVM), SSD Volume Type, us-east-1. VERIFIQUE A AMI PARA SUA REGIÃO!
}

variable "key_name" {
  description = "O nome do par de chaves EC2 para acesso SSH."
  type        = string
}

# Variáveis para o Security Group
variable "my_ip" {
  description = "Seu endereço IP público para permitir acesso SSH. Use '0.0.0.0/0' se não tiver um IP fixo, mas não é recomendado para produção."
  type        = string
  default     = "0.0.0.0/0"
}

# Variáveis para o domínio
variable "domain_name" {
  description = "O nome de domínio para o Keycloak (ex: keycloak.seuexemplo.com)."
  type        = string
}

# Variáveis para as credenciais do Keycloak
variable "keycloak_admin_user" {
  description = "Nome de usuário do administrador do Keycloak."
  type        = string
  sensitive   = true
}

variable "keycloak_admin_password" {
  description = "Senha do administrador do Keycloak."
  type        = string
  sensitive   = true
}

# Variáveis para as credenciais do PostgreSQL
variable "db_name" {
  description = "Nome do banco de dados PostgreSQL para o Keycloak."
  type        = string
  default     = "keycloak_db"
}

variable "db_user" {
  description = "Nome de usuário do banco de dados PostgreSQL."
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Senha do banco de dados PostgreSQL."
  type        = string
  sensitive   = true
}

# Variáveis para o email do Certbot
variable "certbot_email" {
  description = "Endereço de e-mail para avisos do Certbot."
  type        = string
}