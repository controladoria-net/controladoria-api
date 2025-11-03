# Configuração do provedor AWS
provider "aws" {
  region = var.aws_region
}

# Recurso de Data Source para a AMI do Ubuntu
data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"] # Canonical
}


# Security Group para a instância EC2
resource "aws_security_group" "keycloak_sg" {
  name        = "api-gateway-sg"
  description = "Permite tráfego para SSH, HTTP, HTTPS"
  vpc_id      = data.aws_vpc.default.id

  # Regra para SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip] # Seu IP para SSH
    description = "Acesso SSH"
  }

  # Regra para HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Acesso HTTP (para Certbot e redirecionamento NGINX)"
  }

  # Regra para HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Acesso HTTPS (API Gateway via NGINX)"
  }
  
  # As portas 8081 e 8001 não precisam mais ser abertas publicamente,
  # pois o NGINX no mesmo host irá acessá-las internamente.

  # Permitir todo o tráfego de saída
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "api-gateway-sg"
  }
}

# Elastic IP (EIP)
resource "aws_eip" "keycloak_eip" {
  vpc = true

  tags = {
    Name = "api-gateway-eip"
  }
}

# Instância EC2
resource "aws_instance" "keycloak_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_name
  associate_public_ip_address = false
  vpc_security_group_ids = [aws_security_group.keycloak_sg.id]

  root_block_device {
    volume_size = 50
    volume_type = "gp2"
  }

  tags = {
    Name = "API-Gateway-Server"
  }

  # Script de inicialização (user_data)
  user_data = <<-EOF
    #!/bin/bash
    set -euo pipefail

    # Funções de log
    log_info() {
      echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') \"$@\"" >&2
    }
    log_error() {
      echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') \"$@\"" >&2
      exit 1
    }

    log_info "Iniciando script user_data..."
    apt update -y && apt upgrade -y
    apt install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common nginx ufw certbot python3-certbot-nginx

    log_info "Configurando UFW..."
    ufw allow OpenSSH
    ufw allow 'Nginx Full'
    ufw --force enable

    log_info "Instalando Docker..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update -y
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    usermod -aG docker ubuntu

    # --- MUDANÇA PRINCIPAL: Configuração NGINX para Roteamento por Path ---
    log_info "Configurando NGINX para ${var.domain_name}..."
    if [ -f /etc/nginx/sites-enabled/default ]; then
        unlink /etc/nginx/sites-enabled/default
    fi

    cat <<EOT > /etc/nginx/sites-available/${var.domain_name}.conf
    server {
        listen 80;
        listen [::]:80;
        server_name ${var.domain_name};

        # Regra para verificação do Certbot
        location /.well-known/acme-challenge/ {
            root /var/www/html;
        }

        # Redirecionar todo o resto para HTTPS
        location / {
            return 301 https://\$host\$request_uri;
        }
    }

    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name ${var.domain_name};

        # Placeholder para os certificados SSL que o Certbot irá criar
        ssl_certificate /etc/letsencrypt/live/${var.domain_name}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/${var.domain_name}/privkey.pem;

        # Rota para o Keycloak
        # A barra no final de 'proxy_pass' é crucial para reescrever o path
        location /v1/auth/ {
            proxy_pass http://127.0.0.1:8081/; 
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Rota para a API Python
        # A ordem é importante: a rota mais específica (/v1/auth/) deve vir antes da mais genérica (/v1/)
        location /v1/ {
            proxy_pass http://127.0.0.1:8001/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
EOT

    ln -s /etc/nginx/sites-available/${var.domain_name}.conf /etc/nginx/sites-enabled/
    nginx -t
    
    # Criar diretório para o Certbot
    mkdir -p /var/www/html
    systemctl restart nginx

    log_info "Obtendo certificados SSL com Certbot para ${var.domain_name}..."
    certbot --nginx --agree-tos --redirect -m "${var.certbot_email}" -d "${var.domain_name}" --non-interactive

    # --- MUDANÇA PRINCIPAL: Configuração do Docker Compose ---
    log_info "Criando diretórios para volumes Docker..."
    mkdir -p /opt/api-gateway/postgresql
    mkdir -p /opt/api-gateway/keycloak

    log_info "Criando arquivo docker-compose.yml..."
    cat <<EOT > /opt/api-gateway/docker-compose.yml
    version: '3.8'

    services:
      postgresql:
        image: postgres:15-alpine
        container_name: keycloak-postgresql
        environment:
          POSTGRES_DB: ${var.db_name}
          POSTGRES_USER: ${var.db_user}
          POSTGRES_PASSWORD: ${var.db_password}
        volumes:
          - ./postgresql:/var/lib/postgresql/data
        restart: unless-stopped
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U ${var.db_user} -d ${var.db_name}"]
          interval: 5s
          timeout: 5s
          retries: 5

      keycloak:
        image: quay.io/keycloak/keycloak:23.0
        container_name: keycloak
        environment:
          KC_DB: postgres
          KC_DB_URL: jdbc:postgresql://postgresql:5432/${var.db_name}
          KC_DB_USERNAME: ${var.db_user}
          KC_DB_PASSWORD: ${var.db_password}
          KC_HTTP_PORT: 8081
          KC_PROXY: edge
          KC_HOSTNAME: ${var.domain_name}
          # --- NOVA VARIÁVEL: Diz ao Keycloak que ele roda em um sub-path ---
          KC_HTTP_RELATIVE_PATH: /v1/auth
          KC_ADMIN_USERNAME: ${var.keycloak_admin_user}
          KC_ADMIN_PASSWORD: ${var.keycloak_admin_password}
        ports:
          - "8081:8081"
        volumes:
          - ./keycloak:/opt/keycloak/data
        depends_on:
          postgresql:
            condition: service_healthy
        restart: unless-stopped
        command: start-dev

    #   python-backend:
    #     image: controladoria-api:0.0.1
    #     container_name: controladoria-api
    #     environment:
    #       DATABASE_URL: postgresql://${var.db_user}:${var.db_password}@postgresql:5432/${var.db_name}
    #       KEYCLOAK_URL: https://${var.domain_name}/v1/auth
    #     ports:
    #       # --- NOVA PORTA: A API agora roda na porta 8001 ---
    #       - "8001:8001"
    #     depends_on:
    #       postgresql:
    #         condition: service_healthy
    #     restart: unless-stopped

    log_info "Subindo os containers Docker Compose..."
    cd /opt/api-gateway
    docker compose up -d

    log_info "Script user_data concluído com sucesso."
  EOF
}

# Associa o Elastic IP à instância EC2
resource "aws_eip_association" "eip_assoc" {
  instance_id   = aws_instance.keycloak_server.id
  allocation_id = aws_eip.keycloak_eip.id
}

# Data source para a VPC padrão
data "aws_vpc" "default" {
  default = true
}