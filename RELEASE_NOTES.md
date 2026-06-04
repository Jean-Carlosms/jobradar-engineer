# Release Notes

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
