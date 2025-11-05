# Cron - Atualização de Processos

Job responsável por sincronizar processos desatualizados com fontes externas.

## Agendamento

- **Agendador:** APScheduler (`BackgroundScheduler`).
- **Trigger:** `CronTrigger(day='*/3', hour=0, minute=0)` — executa a cada 3 dias às 00:00 (timezone configurável).

## Fluxo

1. Tenta adquirir lock na tabela `scheduler_locks` (`lock_name = update_legal_cases_cron`).
2. Consulta processos cuja coluna `last_synced_at` esteja nula ou com mais de 3 dias.
3. Para cada processo:
   - Respeita rate limit configurado (`EXTERNAL_RPM`, padrão 60 req/min).
   - Consulta API externa via `FindLegalCaseUseCase`.
   - Aplica diffs nos campos e persiste novas movimentações.
4. Registra métricas (`scheduler_runs`, `scheduler_updated_cases`, `scheduler_errors`).
5. Libera o lock.

## Variáveis de Ambiente

- `SCHED_TIMEZONE` — fuso horário usado pelo agendador (default `America/Sao_Paulo`).
- `CRON_BATCH_SIZE` — quantidade de processos por execução (default `20`).
- `EXTERNAL_RPM` — rate limit para chamadas externas (default `60`).

## Logs

- Todos os logs carregam `request_id` e `user_id` (quando houver).
- Job gera entradas de início, resumo com contagens e erros individuais.

## Métricas

- `legal_cases_checked`, `legal_cases_updated`, `legal_case_new_movements`, `legal_case_update_errors`.
- `scheduler_runs`, `scheduler_updated_cases`, `scheduler_errors`.

As métricas podem ser consultadas em `/metrics` (requer autenticação).
