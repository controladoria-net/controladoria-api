Perfeito! Segue um plano de ação enxuto (e executável) para implementar **todos** os passos do vídeo — só que com **PostgreSQL** no lugar de MariaDB — usando **Terraform** e **GitHub Actions**, no **padrão do repositório Build&Run** (com a pasta renomeada para `terraform/`), e configurando o domínio do Keycloak como **`auth.controladoria.net.br`**. Onde o vídeo usa Docker/Compose + NGINX reverse proxy + (MariaDB), aqui mapeio 1:1 para Docker/Compose + NGINX reverse proxy + **Postgres**, provisionados por Terraform numa EC2, e pipeline de IaC no estilo do repo Build&Run. (O vídeo cobre EC2 + Docker + NGINX + Keycloak + banco; manteremos o mesmo fluxo, só trocando o banco. ([YouTube][1]))

# Plano de ação

## 0) Pré-requisitos de conta e domínio

1. **DNS**: tenha a zona hospedada do domínio que aponta para `auth.controladoria.net.br` sob seu controle (idealmente **Route 53**).
2. **AWS OIDC + Remote State (padrão Build&Run)**

   - Criar **GitHub OIDC Provider** na AWS, **IAM Role** com trust policy para GitHub, **S3** (versionado) para o **state** e **DynamoDB** (chave `LockID`) para o **lock**. Isso é exatamente o “Como começar?” do repositório Build&Run. ([GitHub][2])

3. **Certificado**: seguiremos o vídeo com **NGINX + Let’s Encrypt** rodando na própria EC2 (nada de ALB/ACM, para não “mudar os passos sem autorização”). ([YouTube][1])

---

## 1) Estrutura do repositório (padrão Build&Run, com `infra` → `terraform`)

```
/
├─ .github/
│  └─ workflows/
│     ├─ terraform-plan.yml
│     └─ terraform-apply.yml
├─ terraform/              <-- (era "infra" no template)
│  ├─ backend.tf
│  ├─ providers.tf
│  ├─ variables.tf
│  ├─ main.tf              # VPC (opcional), SG, EC2 (Ubuntu), User Data
│  ├─ ec2.tf               # (se preferir separar)
│  ├─ security_groups.tf
│  ├─ route53.tf
│  ├─ outputs.tf
│  └─ files/
│     ├─ docker-compose.yml          # Keycloak + Postgres + Nginx(+certbot)
│     └─ nginx/
│        └─ mydomain.conf            # reverse proxy p/ Keycloak
└─ README.md
```

- **Obs.**: o Build&Run traz `infra/` por padrão; aqui **renomeamos para `terraform/`** conforme seu pedido. Os workflows de Actions seguirão o padrão do repositório Build&Run (plan em PR, apply no merge), ajustando **paths** para `terraform/**`. ([GitHub][2])

---

## 2) GitHub Actions (CI/CD do Terraform)

- Basear-se nos workflows do template Build&Run (plan e apply com OIDC/STS, backend S3/DynamoDB). Ajustes mínimos:

  - `working-directory: ./terraform`
  - Variáveis/segredos: `AWS_ROLE_TO_ASSUME`, `AWS_REGION`, `TF_VAR_keycloak_hostname`, `TF_VAR_email_lets_encrypt`, `TF_VAR_db_password`, etc.
  - `on: pull_request` → `terraform fmt -check`, `init`, `validate`, `plan`; `on: push` (branch main) → `apply`.
    _(Esse padrão é exatamente a proposta do Build&Run para pipeline Terraform.)_ ([GitHub][2])

---

## 3) Terraform – recursos a provisionar (mapeando o vídeo → IaC)

1. **VPC + Subnets** (opcional se já existe): uma pública já atende ao vídeo (EC2 + NGINX público).
2. **Security Group** da EC2:

   - **80/tcp**, **443/tcp** (NGINX)
   - **22/tcp** (SSH) – opcional; se for usar SSM, pode dispensar.

3. **EC2 (Ubuntu LTS)** com **User Data** que:

   - Instala **Docker** e **Docker Compose** (como no vídeo). ([YouTube][1])
   - Cria `/opt/keycloak/` e grava os arquivos (por **`templatefile`** do Terraform) de:

     - `docker-compose.yml` (**Keycloak + Postgres + NGINX + certbot**)
     - `nginx/mydomain.conf` (reverse proxy para o Keycloak – portas 80/443)

   - Sobe o stack: `docker compose up -d`.

4. **Route 53**: `A`/`ALIAS` para **`auth.controladoria.net.br` → EIP** (ou IP elástico da EC2).
5. **State Backend**: `backend "s3"` + lock no DynamoDB (padrão Build&Run). ([GitHub][2])

> Dica de robustez: Mesmo com Compose, aplique as boas práticas de produção do Keycloak (hostname, proxy, timeouts). ([Keycloak][3])

---

## 4) Docker Compose (vídeo → Postgres)

Troca direta de MariaDB → **PostgreSQL** mantendo o resto igual ao vídeo (Keycloak + NGINX + certbot). Exemplo de `docker-compose.yml` (gerado via `templatefile` no Terraform):

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    networks: [kcnet]

  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    command: ["start", "--optimized"]
    depends_on: [postgres]
    environment:
      KC_DB: postgres
      KC_DB_URL_HOST: postgres
      KC_DB_URL_DATABASE: keycloak
      KC_DB_USERNAME: ${DB_USER}
      KC_DB_PASSWORD: ${DB_PASSWORD}
      KC_HOSTNAME: ${KEYCLOAK_HOSTNAME}          # auth.controladoria.net.br
      KC_PROXY: edge
      KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN}
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
    networks: [kcnet]
    expose:
      - "8080"  # NGINX faz proxy

  nginx:
    image: nginx:1.27
    depends_on: [keycloak]
    volumes:
      - ./nginx/mydomain.conf:/etc/nginx/conf.d/default.conf:ro
      - certs:/etc/letsencrypt
      - certs-data:/var/lib/letsencrypt
    ports:
      - "80:80"
      - "443:443"
    networks: [kcnet]
    restart: unless-stopped

  certbot:
    image: certbot/certbot
    volumes:
      - certs:/etc/letsencrypt
      - certs-data:/var/lib/letsencrypt
      - ./nginx/mydomain.conf:/etc/nginx/conf.d/default.conf:ro
    entrypoint: /bin/sh
    command: -c "
      trap exit TERM;
      while :; do
        certbot renew --non-interactive --agree-tos && nginx -s reload || true;
        sleep 12h;
      done
    "
    networks: [kcnet]

networks:
  kcnet:

volumes:
  pg_data:
  certs:
  certs-data:
```

**Observações importantes (fiéis ao vídeo, só com o banco trocado):**

- NGINX atua como **reverse proxy** para o Keycloak (como no vídeo), com **Let’s Encrypt** para SSL. ([YouTube][1])
- Keycloak configurado com **Postgres** (`KC_DB=postgres`), _hostname_ fixo para **`auth.controladoria.net.br`**, e `KC_PROXY=edge` por estar atrás do Nginx. (Boas práticas de produção do Keycloak). ([Keycloak][3])

---

## 5) NGINX `mydomain.conf` (ajuste direto do vídeo para o seu host)

Arquivo semelhante ao do vídeo, apontando para `keycloak:8080` e com server_names para `auth.controladoria.net.br`. Ex.:

- `server { listen 80; server_name auth.controladoria.net.br; ... }` → redireciona para HTTPS e/ou expõe desafio ACME.
- `server { listen 443 ssl; server_name auth.controladoria.net.br; ... proxy_pass http://keycloak:8080; ... }`
  _(O vídeo disponibiliza um conf de exemplo; aqui só adaptamos o host.)_ ([YouTube][1])

---

## 6) User Data da EC2 (instalação e provisionamento — manter passos do vídeo)

No Terraform, use `templatefile` para um shell script que:

1. Instala **Docker** e **Docker Compose** (como no vídeo). ([YouTube][1])
2. Cria `/opt/keycloak/{nginx,}` e grava `docker-compose.yml` + `nginx/mydomain.conf`.
3. Exporta variáveis `.env` (DB_USER/DB_PASSWORD/KEYCLOAK_ADMIN/KEYCLOAK_ADMIN_PASSWORD/KEYCLOAK_HOSTNAME).
4. Executa `docker compose up -d` e agenda `certbot renew` (já embutido no serviço `certbot` acima).

---

## 7) Variáveis/segredos e `tfvars`

- **GitHub Actions (Secrets/Vars)**

  - `AWS_ROLE_TO_ASSUME`, `AWS_REGION`
  - `TF_VAR_keycloak_hostname=auth.controladoria.net.br`
  - `TF_VAR_db_user`, `TF_VAR_db_password`
  - `TF_VAR_keycloak_admin`, `TF_VAR_keycloak_admin_password`
  - `TF_VAR_email_lets_encrypt` (para ACME/Let’s Encrypt)

- **`terraform/variables.tf`**: declare as variáveis acima.
- **`backend.tf`**: aponte para **S3** e **DynamoDB** conforme o padrão Build&Run. ([GitHub][2])

---

## 8) DNS (Route 53) — apontar o hostname para a EC2

- Criar **EIP** (IP elástico) e associar à EC2 (evita mudar IP em reinicializações).
- **Registro A** `auth.controladoria.net.br` → EIP (no mesmo hosted zone).
- (Sem ALB/ACM — mantemos os passos do vídeo com NGINX/Certbot). ([YouTube][1])

---

## 9) Testes de validação (foco no que o vídeo entrega)

1. Acessar `http://auth.controladoria.net.br` → deve redirecionar para **HTTPS**.
2. `https://auth.controladoria.net.br` abre o **Keycloak** (login admin).
3. **Certificado válido** de Let’s Encrypt.
4. **Admin console** acessível; criar um Realm de teste e um cliente público.
5. Logs dos contêineres sem erros (Keycloak se conectando ao **Postgres**).

---

## 10) Considerações (produção responsável sem “mudar os passos”)

- O vídeo é “EC2 + Docker + NGINX + DB” (sem alta disponibilidade). Você pode escalar depois (EKS/ALB/ACM/RDS), mas **não farei alterações de arquitetura sem sua autorização**. ([YouTube][1])
- Mesmo em EC2 única, siga o guia de **produção do Keycloak** (hostname fixo, proxy, cookies/https). ([Keycloak][3])

---

## 11) Entregáveis no repositório

- **`.github/workflows/*`** no padrão Build&Run, só ajustando `working-directory` e nomes de secrets/vars. ([GitHub][2])
- **`terraform/`** com:

  - `main.tf` (IAM instance profile opcional p/ SSM, EC2, EIP, Route53)
  - `security_groups.tf` (80/443/22)
  - `route53.tf` (A record)
  - `user_data.tpl` (instala Docker/Compose e sobe o stack do vídeo)
  - `files/docker-compose.yml` e `files/nginx/mydomain.conf` (adaptados p/ Postgres e hostname)
  - `backend.tf`, `providers.tf`, `variables.tf`, `outputs.tf`.

---

Se quiser, já te entrego os **templates Terraform + workflows prontos** nessa estrutura (com placeholders para os segredos) — é só me dar um “ok” que eu gero os arquivos na lata, sem alterar nenhum passo do vídeo além da troca para **Postgres** e o **hostname** informado.

[1]: https://www.youtube.com/watch?v=ZzSe0EQy9rA&utm_source=chatgpt.com 'Keycloak production deployment using AWS EC2 Server ... - YouTube'
[2]: https://github.com/buildrun-tech/buildrun-infra-terraform-pipeline 'GitHub - buildrun-tech/buildrun-infra-terraform-pipeline: Pipeline de infraestrutura Terraform para implantar recursos na AWS via STS Assume Role'
[3]: https://www.keycloak.org/server/configuration-production?utm_source=chatgpt.com 'Configuring Keycloak for production'
