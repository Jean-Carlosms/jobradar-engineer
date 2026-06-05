# Release Notes

## v3.0.0 - Indices de performance e saude do banco

- `CURRENT_SCHEMA_VERSION` elevado para 2.
- Adicionada migracao v2 com indices SQLite idempotentes para jobs, analises e controle de schema.
- Criado `src/services/database_health.py` para diagnosticar tamanho, integridade, tabelas, linhas, indices, freelist e status do schema.
- Adicionados comandos CLI `--db-health` e `--export-db-health`.
- Dashboard passou a exibir a secao `Saude do Banco` na aba `Backups e Banco`.
- README, guia de producao e checklist passaram a documentar verificacao/exportacao de saude do banco.
- Adicionados testes para migracao v2, idempotencia, indices, servico de saude, exportacao e CLI.
- Revisao final de publicacao consolidou README, portfolio, checklist, demo script, post LinkedIn, pitch de entrevista e safety check para a release v3.0.0.

## v2.9.0 - Schema versionado e migracoes controladas

- Criado `src/schema_migrations.py` com `CURRENT_SCHEMA_VERSION`, tabela `schema_migrations` e migração inicial idempotente.
- `JobRepository.init_db()` passou a aplicar migrações de schema durante a inicializacao do banco.
- Adicionados comandos CLI `--schema-status` e `--migrate-schema`.
- A migracao inicial garante tabelas principais, colunas adicionadas em fases anteriores e registro de versao sem apagar dados existentes.
- README, checklist e guia de producao documentam backup antes de migracao e uso dos comandos de schema.
- Adicionados testes para banco novo, banco legado, idempotencia, preservacao de dados, status e migracao via CLI.
- Mantido o desenho local simples, sem Alembic nesta fase.

## v2.8.0 - Revisao de cobertura e modulos experimentais

- Criado `docs/COVERAGE_REVIEW.md` com classificacao de modulos de baixa cobertura por importancia, papel, decisao, acao recomendada e prioridade.
- `SearchEngineSource` foi documentado como fallback experimental por depender de HTML de buscador, challenge/captcha e disponibilidade externa.
- README passou a indicar `GupyPublicSource` como fonte real principal e `BuscaPublica` como fallback experimental.
- Adicionados testes offline para busca publica desativada, challenge sem links, falha de request e wrappers experimentais por dominio.
- Adicionado teste minimo para `scheduler.py` com scheduler fake.
- Fontes placeholder receberam docstrings claras como wrappers experimentais de busca publica.
- Mantido o limite de cobertura em 85%, sem refatoracao grande e sem chamadas reais de rede em pytest.

## v2.7.0 - Limite de cobertura elevado para 85%

- GitHub Actions passou a exigir `--cov-fail-under=85`.
- README e checklist de publicacao passaram a usar o comando local com `--cov-fail-under=85`.
- Mantida cobertura local em torno de 88%, com margem segura acima do novo limite.
- O limite de cobertura nao foi alterado no `pytest.ini`, preservando `python -m pytest` simples para desenvolvimento local.
- Testes documentais passaram a validar o novo limite ativo e evitar referencias operacionais antigas a `--cov-fail-under=80`.

## v2.6.0 - Melhoria de cobertura dos modulos criticos

- Adicionados testes de comportamento para wrappers operacionais em `src/main.py`.
- Cobertos fluxos de relatorio ausente, auditoria sem CSV, backup automatico, lifecycle de backup/verificacao/manutencao/exportacao/limpeza e alertas operacionais.
- Adicionados testes de `EmailSender` para falha SMTP e envio de alerta operacional com SMTP mockado.
- Cobertura de `src/main.py` subiu de 67% para mais de 80%.
- Cobertura total subiu de 86.10% para aproximadamente 89%, mantendo o limite minimo do CI em 80%.
- Nenhuma chamada de rede real foi adicionada aos testes.

## v2.5.0 - Limite minimo de cobertura no CI

- GitHub Actions passou a rodar `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=80`.
- Mantido `python -m pytest` simples para desenvolvimento local rapido.
- README documenta cobertura minima atual de 80% e cobertura local em torno de 86%.
- Checklist de publicacao passou a exigir coverage com `--cov-fail-under=80`.
- Portfolio passou a mencionar politica de cobertura minima.
- Adicionados testes documentais para validar limite de cobertura no CI, README e checklist.

## v2.4.0 - Gerenciamento seguro de SQLite e limpeza de warnings

- Ajustado `JobRepository` para usar `NullPool`, evitando conexoes SQLite retidas pelo pool durante testes.
- Adicionado metodo `close()` e suporte a context manager no repositorio de jobs.
- Corrigidos usos diretos de `sqlite3.connect` no dashboard, script de dados ficticios e testes para fechar conexoes com `contextlib.closing`.
- Adicionados commits explicitos em pontos de escrita SQLite que passaram a fechar a conexao manualmente.
- `python -W default -m pytest` passou sem `ResourceWarning` de SQLite.
- README passou a documentar validacao explicita de warnings.

## v2.3.0 - Cobertura de testes

- Adicionado `pytest-cov` em `requirements-dev.txt`.
- CI passou a rodar `python -m pytest --cov=src --cov-report=term-missing`.
- Documentado comando local com `--cov-report=html`.
- `.gitignore` passou a proteger `htmlcov/`, `.coverage` e `coverage.xml`.
- README recebeu badge estatico `Coverage measured locally` e secao `Cobertura de testes`.
- Checklist de publicacao passou a incluir execucao local de coverage.
- Adicionados testes documentais para dependencia, ignores e documentacao de cobertura.

## v2.2.0 - Retencao automatica de backups e limpeza segura

- Adicionado plano de retencao para backups antigos com dry-run por padrao.
- Limpeza identifica candidatos acima de `BACKUP_RETENTION_DAYS`, protegidos e espaco recuperavel estimado.
- O backup mais recente nunca e removido.
- Manifestos invalidos sao protegidos por padrao.
- Adicionados comandos `--cleanup-db-backups`, `--cleanup-db-backups-dry-run` e `--confirm-cleanup-backups`.
- Limpeza real so remove arquivos com confirmacao explicita.
- Relatorios de limpeza sao gerados em `reports/backup_cleanup_YYYYMMDD_HHMMSS.md` e `.csv`.
- Dashboard `Backups e Banco` passou a mostrar politica de retencao e candidatos acima da retencao.
- Adicionada configuracao `BACKUP_CLEANUP_DRY_RUN`.
- README, guia de producao, checklist e TODO documentam a rotina segura.

## v2.1.0 - Dashboard de backups e manutencao

- Dashboard ganhou aba `Backups e Banco` para visualizar manifestos em `backups/`.
- A aba mostra total de backups, tamanho total, backup mais recente, maior backup e tabela exportavel em CSV.
- Restauracao continua fora do dashboard e exige CLI com `--confirm-restore`.
- `DatabaseMaintenanceService` passou a expor helpers para carregar manifestos, ignorar JSON invalido, resumir backups, formatar tamanho e encurtar SHA-256.
- Adicionado comando `--db-backup-summary`.
- Guia de producao documenta rotina recomendada de backup, verificacao, resumo, exportacao e manutencao mensal.
- Adicionados testes para manifestos, resumo, formato de tamanho, SHA curto, CLI e colunas usadas no dashboard.

## v2.0.0 - Backup e manutencao do banco local

- Adicionado `DatabaseMaintenanceService` para backup, verificacao, restore, exportacao de resumo e VACUUM/ANALYZE.
- Backups sao gerados em `backups/jobs_backup_YYYYMMDD_HHMMSS.db` com manifesto JSON pareado.
- Manifestos registram timestamp, banco de origem, arquivo de backup, tamanho, SHA-256 e motivo.
- Restauracao exige `--confirm-restore` e cria backup automatico do estado atual antes de substituir `data/jobs.db`.
- Adicionados comandos `--backup-db`, `--list-db-backups`, `--verify-db-backup`, `--restore-db-backup`, `--db-maintenance` e `--export-db-summary`.
- Adicionadas configuracoes `AUTO_BACKUP_BEFORE_RUN` e `BACKUP_RETENTION_DAYS`.
- `.gitignore` e safety check passaram a proteger `backups/`, mantendo `backups/.gitkeep`.
- README, guia de producao, checklist, portfolio e TODO documentam backup e restauracao segura.
- Adicionados testes para backup, manifesto, SHA-256, listagem, verificacao, restore, resumo, manutencao e protecao Git.

## v1.9.0 - Dashboard de alertas operacionais

- `RunHistoryService` passou a extrair campos `operational_alert_*` dos JSONs em `runs/`.
- Resumos de historico agora incluem total de alertas, alertas enviados, ultimo alerta e failures.
- Adicionado comando `--operational-alerts-summary` para resumo dedicado de alertas.
- Dashboard ganhou aba `Alertas Operacionais` com metricas, filtros e exportacao CSV.
- Alertas podem ser filtrados por tipo, envio, fonte e modo.
- README, checklist, release notes e TODO documentam o novo fluxo visual.
- Adicionados testes para extracao, resumo, CLI e filtros da aba.

## v1.8.0 - Alertas operacionais por e-mail

- Adicionado `OperationalAlertService` para gerar assunto, corpo, tipo e decisao de envio a partir do run report.
- Alertas cobrem falha por fonte, execucao sem vagas, execucao sem vagas elegiveis e resumo opcional de sucesso.
- Adicionadas configuracoes `OPERATIONAL_ALERTS_*` e `OPERATIONAL_DAILY_SUMMARY` ao `.env.example` e `Settings`.
- `EmailSender` passou a enviar alertas operacionais em fluxo separado do e-mail de vagas, respeitando dry-run.
- `src.main` ganhou `--send-operational-alerts`, `--no-operational-alerts` e `--test-operational-alert`.
- Run reports registram tipo, decisao, status e motivo/status do alerta operacional.
- README, guia de producao, checklist e TODO documentam o uso seguro com Agendador do Windows.
- Adicionados testes para templates, configuracao, dry-run, CLI e registro no run report.

## v1.7.0 - Historico operacional no dashboard

- Adicionado `RunHistoryService` para carregar historico estruturado a partir de `runs/run_report_*.json`.
- JSONs invalidos em `runs/` sao ignorados com fallback seguro.
- Dashboard ganhou aba `Historico de Execucoes` com metricas, filtros, detalhes e exportacao CSV.
- Adicionado comando `--run-history-summary` para resumo rapido do historico operacional.
- README, checklist e TODO documentam a diferenca entre `logs/` e `runs/` e o novo fluxo de acompanhamento.
- Adicionados testes para carregamento, ordenacao, resumo, CLI e filtros do dashboard.

## v1.6.0 - Observabilidade local e relatórios de execução

- Adicionado `RunReporter` para gerar relatórios Markdown e JSON em `runs/`.
- Adicionados comandos `--run-report`, `--no-run-report` e `--latest-run-report`.
- Relatórios registram horários, duração, modo, fontes, totais, status de e-mail, erros e relatórios/debug gerados.
- `runs/` passou a ser protegido no `.gitignore`, mantendo `runs/.gitkeep`.
- Scripts Windows de dry-run e produção passaram a usar `--run-report`.
- README e checklist de publicação documentam observabilidade local e proteção de relatórios.

## v1.5.0 - Testes determinísticos e bloqueio de rede

- Adicionada configuracao `pytest.ini` com `testpaths`, marcadores e `--strict-markers`.
- Adicionado bloqueio automatico de rede via `tests/conftest.py` durante `pytest`.
- Chamadas reais via `requests` agora falham por padrao nos testes com mensagem clara.
- Adicionado marcador `network` para liberar rede apenas quando explicitamente necessario.
- Adicionados testes para garantir bloqueio de rede e comportamento do marcador `network`.
- README e checklist de publicacao documentam a diferenca entre testes offline e coleta real via CLI.

## v1.4.0 - Screenshots e README visual

- Adicionados placeholders seguros para os screenshots finais em `docs/images/`.
- README manteve referencias aos PNGs finais e passou a orientar uso do `docs/SCREENSHOTS_GUIDE.md` quando as imagens ainda nao existirem.
- `docs/SCREENSHOTS_GUIDE.md` recebeu passo a passo final e checklist de privacidade antes da publicacao.
- `docs/DEMO_SCRIPT.md` passou a incluir roteiro com as sete imagens esperadas.
- `PORTFOLIO_SUMMARY.md` recebeu secao `Evidencias visuais`.
- TODO atualizado com Fase 18 concluida e roadmap pos-v1.4.

## v1.3.0 - Visual polish e demo para portfolio

- Dashboard reorganizado em abas para resumo executivo, funil, top vagas, analise, revisao, auditoria, insights e exportacoes.
- Adicionada visao de funil com Coleta -> Pre-filtro -> Match -> Analise -> Revisao.
- Padronizados nomes de colunas exibidas no dashboard.
- README atualizado com secao `Demonstracao visual` e referencias aos screenshots finais.
- `docs/SCREENSHOTS_GUIDE.md` atualizado com checklist, resolucao sugerida e nomes padronizados.
- Criado `docs/DEMO_SCRIPT.md` com roteiro de demonstracao em 3 minutos.
- `PORTFOLIO_SUMMARY.md` atualizado com orientacoes de demo visual e prints recomendados.

## v1.2.0 - Feedback insights e calibracao assistida

- Adicionado servico `FeedbackInsightsService` para analisar revisoes humanas salvas no SQLite.
- Adicionados relatorios Markdown e CSV em `reports/feedback_insights_YYYYMMDD_HHMMSS.*`.
- Adicionados comandos `--feedback-insights` e `--feedback-insights-min-reviewed`.
- Dashboard passou a exibir resumo opcional de insights de feedback.
- Relatorios destacam termos positivos/negativos, empresas, titulos, localidades, falsos positivos, falsos negativos e favoritas.
- Sugestoes sao assistivas e nao alteram `profile_keywords.yaml` automaticamente.
- Adicionados testes para servico, relatorios e CLI.

## v1.1.0 - CI e qualidade automatizada

- Adicionado workflow real de GitHub Actions em `.github/workflows/ci.yml`.
- CI configurado para Ubuntu e Windows com Python 3.11.
- Pipeline passou a instalar dependencias, rodar Ruff, safety check de publicacao e pytest.
- Adicionado `requirements-dev.txt` para dependencias de desenvolvimento.
- README atualizado com badge real do GitHub Actions e comandos locais de qualidade.
- Adicionados testes para garantir a existencia e os comandos obrigatorios do workflow.

## v1.0.0 - Primeira versao completa

- Consolidado pipeline completo: coleta, deduplicacao, pre-filtro tecnico, enriquecimento Gupy, score explicavel, analise vaga x perfil, e-mail e dashboard.
- Adicionada fonte Gupy publica dedicada com empresas categorizadas, debug por empresa e relatorio de status.
- Adicionado enriquecimento de detalhes por pagina publica da Gupy, com limite, timeout e rate limit.
- Adicionado pre-filtro tecnico para reduzir ruido antes do enriquecimento.
- Adicionada auditoria do pre-filtro com relatorios Markdown e CSV em `reports/`.
- Adicionada revisao humana no dashboard, com status, favoritos, notas, resumo e exportacao de feedback.
- Atualizados comandos CLI para auditoria, resumo de feedback e exportacao.
- Reforcada publicacao segura: `.env`, `.venv/`, `data/jobs.db`, `logs/` e `reports/` fora do versionamento.
- Projeto consolidado para portfolio e publicacao como primeira versao completa.

## v0.7.0 - Release e publicacao segura

- Adicionado checklist final de publicacao.
- Adicionada descricao para GitHub About.
- Adicionado rascunho de post para LinkedIn.
- Adicionado pitch para entrevistas.
- Adicionado safety check automatizado para arquivos sensiveis e documentacao obrigatoria.
- README atualizado com referencias de portfolio e publicacao.

## v0.6.0 - Preparacao para GitHub e portfolio

- Adicionado banco ficticio de exemplo.
- Adicionado script para gerar `data/sample_jobs.db`.
- Dashboard passou a permitir escolha entre banco real e banco ficticio.
- Adicionados documentos de portfolio, screenshots, seguranca e release notes.
- README reorganizado com foco profissional.

## v0.5.0 - Agendamento Windows

- Scripts `.bat` para execucao diaria, dry-run e dashboard.
- Logs timestampados em `logs/`.
- Documentacao para Windows Task Scheduler e setup de producao.

## v0.4.0 - Comparador Vaga x Perfil

- Perfil resumido em YAML.
- Analise local baseada em regras.
- Tabela `job_analyses`.
- Dashboard e e-mail com fit level, fit score e resumo da analise.

## v0.3.0 - Dashboard Streamlit

- Dashboard local com metricas, filtros, tabelas, graficos e exportacao CSV.

## v0.2.0 - Perfil YAML e score explicavel

- Perfil configuravel por YAML.
- Score com justificativa textual.
- Campos `match_reason`, `priority_company` e `query_used`.

## v0.1.0 - MVP

- Estrutura inicial.
- Fonte mock e busca publica.
- SQLite, deduplicacao, e-mail dry-run e testes.
