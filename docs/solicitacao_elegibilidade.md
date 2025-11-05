# Solicitação - Avaliação de Elegibilidade

Consolida dados extraídos e aplica regras de negócio para determinar o status da solicitação.

## Autenticação

- Requer cookie `access_token`.

## Requisição

- **Método:** `POST`
- **URL:** `/solicitacao/elegibilidade`
- **Body (JSON):**

```json
{
  "solicitation_id": "8f6b4d2c-1d7a-4e41-aa91-6a5e8a304178"
}
```

## Resposta 200 OK

```json
{
  "data": {
    "solicitation_id": "8f6b4d2c-1d7a-4e41-aa91-6a5e8a304178",
    "status": "apto",
    "score_texto": "alto",
    "pendencias": [],
    "evaluated_at": "2024-04-20T12:00:00.000Z"
  }
}
```

## Erros

- `401` — autenticação ausente.
- `404` — solicitação inexistente.
- `422` — dados insuficientes (documentos não extraídos ou ausentes).
- `502` — falha na execução das regras de IA.
- `500` — erro inesperado.
