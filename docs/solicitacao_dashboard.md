# Solicitação - Dashboard

Retorna indicadores sobre o funil das solicitações.

## Autenticação

- Requer cookie `access_token` válido.

## Requisição

- **Método:** `GET`
- **URL:** `/solicitacao/dashboard`
- **Query params opcionais:**
  - `status[]=pendente|aprovada|reprovada|...`
  - `priority[]=baixa|media|alta`
  - `uf[]=SP` — siglas de estado.
  - `city[]=Ilhabela`
  - `date_from`, `date_to` (ISO 8601)

## Resposta 200 OK

```json
{
  "data": {
    "status_count": {"pendente": 4, "aprovada": 6},
    "by_period": [{"period": "2024-04", "count": 5}],
    "period_granularity": "monthly",
    "avg_processing_time_days": 3.5,
    "approval_rate": 0.75,
    "most_missing_documents": []
  }
}
```

## Notas

- A granularidade temporal padrão é mensal.
- `approval_rate` é calculado com base em aprovações versus decisões (aprovada/reprovada).
- Campos de "missing documents" dependem de evolução de regras de negócio.
