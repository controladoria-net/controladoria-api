# Solicitação - Classificador de Documentos

Processa e classifica documentos anexados a uma solicitação, persistindo metadados e o upload no S3.

## Autenticação

- Requer cookie `access_token` válido.

## Requisição

- **Método:** `POST`
- **URL:** `/solicitacao/classificador/processar`
- **Content-Type:** `multipart/form-data`
- **Campos:**
  - `files` — até 15 arquivos (`application/pdf`, `image/png`, `image/jpeg`, `image/tiff`).

## Resposta 200 OK

```json
{
  "data": {
    "solicitation_id": "8f6b4d2c-1d7a-4e41-aa91-6a5e8a304178",
    "groups": [
      {
        "categoria": "CNIS",
        "documentos": [
          {
            "document_id": "018fe2e2-14a6-7c29-bc3f-9f32d41b4ad1",
            "categoria": "CNIS",
            "confianca": 0.94,
            "arquivo": "cnis.pdf",
            "mimetype": "application/pdf"
          }
        ]
      }
    ]
  }
}
```

## Erros Comuns

- `401` — usuário não autenticado.
- `422` — ausência de arquivos, excesso (>15) ou tipo/mimetype não suportado.
- `502` — falha na classificação ou upload em provedores externos.
- `503` — erro ao persistir dados no banco de dados ou S3 indisponível.
- `500` — erro inesperado.
