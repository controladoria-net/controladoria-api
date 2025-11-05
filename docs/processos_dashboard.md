# Processos - Dashboard

Retorna agregações para o dashboard operacional de processos.

## Autenticação

- Requer cookie `access_token` válido.

## Requisição

- **Método:** `GET`
- **URL:** `/processos/dashboard`
- **Query params opcionais:**
  - `status[]=...`
  - `priority[]=baixa|media|alta`
  - `tribunal[]=TJSP` (siglas)
  - `date_from=YYYY-MM-DD`
  - `date_to=YYYY-MM-DD`
  - `sort_field` / `sort_dir` (aplicado em destaques)

## Resposta 200 OK

```json
{
  "data": {
    "status_count": {"ativo": 12, "suspenso": 3},
    "by_court": [{"label": "TJSP", "value": 8}],
    "by_period": [{"period": "2024-04", "value": 5}],
    "period_granularity": "monthly",
    "avg_time_between_movements_days": 12.4,
    "top_by_movements": [
      {
        "numero_processo": "123456700202012345",
        "tribunal": "TJSP",
        "movimentacoes": 14,
        "ultima_movimentacao": "2024-04-02T08:30:00+00:00"
      }
    ],
    "last_updated_list": [
      {
        "numero_processo": "987654320202012345",
        "tribunal": "TJSP",
        "movimentacoes": 6,
        "ultima_movimentacao": "2024-04-18T09:15:00+00:00"
      }
    ]
  }
}
```

### Observações

- A granularidade padrão é `monthly`; suportes adicionais (`weekly`, `daily`) podem ser ativados via configuração futura.
- O endpoint aplica filtros diretamente em SQL para performance.
- Em caso de erro de validação de datas é retornado `422`.
