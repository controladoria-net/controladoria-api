# Solicitação - Consulta por ID

Recupera os dados consolidados de uma solicitação, incluindo metadados de documentos, análise/observações e resultado de elegibilidade (quando disponível).

## Autenticação

- Requer cookie `access_token`.

## Requisição

- **Método:** `GET`
- **URL:** `/solicitacoes/{id}`
  - `id`: UUID da solicitação (ex.: `8f6b4d2c-1d7a-4e41-aa91-6a5e8a304178`)

## Resposta 200 OK

```json
{
  "data": {
    "id": "8f6b4d2c-1d7a-4e41-aa91-6a5e8a304178",
    "pescador": {
      "nome": "Maria Oliveira",
      "cpf": "123.456.789-00",
      "rg": "MG-12.345.678"
    },
    "status": "pendente",
    "priority": "baixa",
    "lawyerNotes": "Revisar laudo médico antes da próxima etapa.",
    "analysis": {
      "eligibility": {
        "status": "apto",
        "score_text": "80",
        "pending_items": []
      },
      "lawyerNotes": "Revisar laudo médico antes da próxima etapa."
    },
    "createdAt": "2024-11-05T18:11:02.345Z",
    "updatedAt": "2024-11-05T18:45:19.612Z",
    "documents": [
      {
        "id": "018fe2e2-14a6-7c29-bc3f-9f32d41b4ad1",
        "fileName": "documento.pdf",
        "mimetype": "application/pdf",
        "classification": "CNIS",
        "confidence": 0.94,
        "uploadedAt": "2024-11-05T18:12:45.901Z"
      }
    ]
  }
}
```

- `analysis` é opcional: além de dados persistidos no campo `analysis` da solicitação, agrega o último resultado de elegibilidade (campo `eligibility`).
- `lawyerNotes` reflete o valor detectado em `analysis.lawyerNotes`, facilitando consumo direto pelo frontend.
- `documents` lista apenas metadados (o conteúdo continua armazenado no S3).

## Erros

- `401` — usuário não autenticado.
- `404` — solicitação não encontrada.
- `422` — identificador inválido (não é um UUID).
- `502` — erro de domínio ao montar os dados (falha de infraestrutura).
- `500` — falha inesperada durante o processamento.
