# Controladoria API

API FastAPI para fluxo de classificação de documentos, extração de dados, dashboards e sincronização de processos judiciais.

## Requisitos

- Python 3.9+
- PostgreSQL 14+
- Dependências listadas em `requirements.txt`

## Variáveis de Ambiente

| Variável | Descrição |
| --- | --- |
| `DATABASE_URL` | String de conexão do PostgreSQL |
| `GOOGLE_API_KEY` | Chave do Gemini para classificação/extração |
| `DATAJUD_URL` / `DATAJUD_API_KEY` | Credenciais para consulta de processos |
| `AWS_REGION` | Região do bucket S3 (default `sa-east-1`) |
| `S3_BUCKET` | Nome do bucket onde os documentos são armazenados |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credenciais de acesso ao S3 |
| `SCHED_TIMEZONE` | Fuso horário do cron (default `America/Sao_Paulo`) |
| `CRON_BATCH_SIZE` | Quantidade de processos atualizados por execução (default `20`) |
| `EXTERNAL_RPM` | Rate limit de chamadas externas (default `60`) |

## Migrações

```bash
alembic upgrade head
```

## Execução em desenvolvimento

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Documentação

- Endpoints detalhados em `docs/*.md`.
- Métricas disponíveis em `/metrics` (requer autenticação).
