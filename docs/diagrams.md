# Diagrams

This document provides architectural diagrams to support the new persistence model and service flows.

## Entity-Relationship Diagram

```mermaid
erDiagram
    legal_cases ||--o{ legal_case_movements : has
    solicitacoes ||--o{ documentos : owns
    documentos ||--|| document_extractions : generates
    solicitacoes ||--|| eligibility_results : produces

    legal_cases {
        uuid id PK
        string numero_processo
        string tribunal
        string orgao_julgador
        string classe_processual
        string assunto
        string situacao
        timestamptz data_ajuizamento
        int movimentacoes
        timestamptz ultima_movimentacao
        string ultima_movimentacao_descricao
        string prioridade
        string status
        timestamptz last_synced_at
        timestamptz created_at
        timestamptz updated_at
    }

    legal_case_movements {
        uuid id PK
        uuid legal_case_id FK
        timestamptz movement_date
        text description
        timestamptz created_at
    }

    solicitacoes {
        uuid id PK
        string status
        string prioridade
        jsonb pescador
        string municipio
        string estado
        jsonb analysis
        timestamptz created_at
        timestamptz updated_at
    }

    documentos {
        uuid id PK
        uuid solicitacao_id FK
        string nome_arquivo
        string mimetype
        string s3_key
        string uploaded_by
        timestamptz uploaded_at
        string classificacao
        float confianca
        string status
        timestamptz created_at
        timestamptz updated_at
    }

    document_extractions {
        uuid id PK
        uuid documento_id FK
        string document_type
        jsonb extracted_payload
        timestamptz created_at
    }

    eligibility_results {
        uuid id PK
        uuid solicitacao_id FK
        string status
        string score_texto
        jsonb pendencias
        timestamptz created_at
    }
```

## Flow & Integration Diagram

```mermaid
flowchart LR
    subgraph Client
        UI[Frontend\n(React/Next)]
    end

    subgraph API["FastAPI Application"]
        direction LR
        SR[Session Router]
        PR[Processos Router]
        SoR[Solicitação Router]
        Cron[Cron Scheduler\n(APScheduler)]
    end

    subgraph UseCases["Domain Use Cases"]
        direction TB
        FindCase[GetLegalCaseById\n/ UpdateStaleLegalCases]
        ProcessDash[BuildProcessDashboard]
        Classify[ClassificarDocumentos]
        Extract[ExtrairDados]
        Eligibility[AvaliarElegibilidade]
        SolicDash[BuildSolicitationDashboard]
    end

    subgraph Infra
        direction TB
        Repos[SQLAlchemy Repositories]
        S3[S3 Client\n(controladoria-backend-docs)]
        Keycloak[Keycloak]
        DataJud[DataJud API]
    end

    Client -->|Cookies access_token| SR -->|AuthenticatedUser| PR
    PR -->|Either result| FindCase
    PR --> ProcessDash
    FindCase -->|Read/Write| Repos
    FindCase -->|Fetch CNJ| DataJud
    ProcessDash --> Repos
    Cron --> FindCase
    Cron --> Repos

    Client --> SoR
    SoR --> Classify --> S3
    Classify --> Repos
    SoR --> Extract --> S3
    Extract --> Repos
    SoR --> Eligibility --> Repos
    SoR --> SolicDash --> Repos

    SR --> Keycloak
```

### Diagram Notes

- **Processos Flow**: `/processos/consultar/{id}` validates the CNJ number, calls `GetLegalCaseByIdUseCase`, persists new cases via repositories, and relies on `FindLegalCaseUseCase` to query DataJud.
- **Cron Job**: The APScheduler job executes `UpdateStaleLegalCasesUseCase` every three days at 00:00 (America/Sao_Paulo), refreshing records whose `last_synced_at` is null or older than three days, persisting only diffs.
- **Solicitação Workflow**: The `/solicitacao` endpoints share repositories. Classification uploads to S3, extraction consumes stored file metadata, and eligibility leverages extracted payloads plus solicitation data.
- **Dashboards**: Both process and solicitation dashboards aggregate using SQLAlchemy functions (e.g., monthly buckets with `date_trunc`) before mapping to DTO responses.

