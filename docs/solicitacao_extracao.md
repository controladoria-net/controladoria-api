# Solicitação - Extração de Dados

Aciona a IA para extrair informações estruturadas dos documentos previamente classificados e armazenados.

## Autenticação

- Requer cookie `access_token`.

## Requisição

- **Método:** `POST`
- **URL:** `/solicitacao/extracao`
- **Body (JSON):**

```json
{
  "solicitation_id": "8f6b4d2c-1d7a-4e41-aa91-6a5e8a304178",
  "document_ids": [
    "018fe2e2-14a6-7c29-bc3f-9f32d41b4ad1"
  ]
}
```

## Resposta 200 OK

```json
{
  "data": {
    "solicitation_id": "8f6b4d2c-1d7a-4e41-aa91-6a5e8a304178",
    "items": [
      {
        "document_id": "018fe2e2-14a6-7c29-bc3f-9f32d41b4ad1",
        "document_type": "CNIS",
        "extracted": {
          "nome": "Maria Oliveira",
          "cpf": "123.456.789-00"
        }
      }
    ]
  }
}
```

## Erros

- `401` — usuário não autenticado.
- `404` — documento não localizado.
- `422` — payload inválido ou tipo de documento não suportado.
- `502` — erro na extração via IA.
- `503` — objeto indisponível no storage.
