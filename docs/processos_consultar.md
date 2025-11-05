# Processos - Consultar

Endpoint responsável por buscar um processo específico e sincronizar com fontes externas quando necessário.

## Autenticação

- Requer cookie `access_token` válido (Keycloak).

## Requisição

- **Método:** `GET`
- **URL:** `/processos/consultar/{case_number}`
- **Path param:**
  - `case_number` — Número do processo com 20 dígitos (CNJ).

## Respostas

### 200 OK

```json
{
  "data": {
    "numero_processo": "123456700202012345",
    "tribunal": "TJSP",
    "orgao_julgador": "1ª Vara Cível",
    "classe_processual": "Ação ordinária",
    "assunto": "Direito do consumidor",
    "situacao": "Em andamento",
    "data_ajuizamento": "2024-01-10T12:00:00+00:00",
    "movimentacoes": 4,
    "ultima_movimentacao": "2024-04-02T08:30:00+00:00",
    "ultima_movimentacao_descricao": "Concluso para decisão",
    "prioridade": "baixa",
    "status": "ativo",
    "movement_history": [
      {"date": "2024-04-02T08:30:00+00:00", "description": "Concluso para decisão"}
    ]
  }
}
```

### 401 Unauthorized

```json
{"errors": [{"message": "Não autorizado"}]}
```

### 404 Not Found

```json
{"errors": [{"message": "Processo '123456700202012345' não foi encontrado."}]}
```

### 422 Unprocessable Entity

```json
{"errors": [{"message": "Identificador do processo deve conter 20 dígitos."}]}
```

### 429 Too Many Requests

```json
{"errors": [{"message": "Limite de requisições atingido. Tente novamente mais tarde."}]}
```

### 500 Internal Server Error

```json
{"errors": [{"message": "Ocorreu um erro interno inesperado no servidor."}]}
```
