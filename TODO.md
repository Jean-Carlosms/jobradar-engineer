# TODO

## Fase 1 - MVP

- [x] Estrutura inicial do projeto.
- [x] Fonte simulada.
- [x] Busca publica segura por mecanismo de pesquisa.
- [x] Score por palavras-chave.
- [x] Deduplicacao por URL e identidade da vaga.
- [x] SQLite com SQLAlchemy.
- [x] E-mail em dry-run ou SMTP.
- [x] Testes basicos.

## Fase 2 - Configuracao e aderencia

- [x] Criar `config/profile_keywords.yaml`.
- [x] Carregar palavras-chave, cargos, localidades e limites a partir do YAML.
- [x] Gerar justificativa textual de aderencia.
- [x] Salvar `match_reason`, `priority_company` e `query_used`.
- [x] Adicionar migracao simples para SQLite local.
- [x] Melhorar corpo do e-mail em texto simples.
- [x] Gerar queries publicas por site, cargo e localidade.
- [x] Adicionar CLI com `--dry-run`, `--send-email`, `--source` e `--min-score`.
- [x] Ampliar testes automatizados.

## Fase 3 - Dashboard Local com Streamlit

- [x] Adicionar Streamlit e Pandas.
- [x] Criar `dashboard.py`.
- [x] Carregar vagas de `data/jobs.db`.
- [x] Exibir metricas principais.
- [x] Criar filtros laterais.
- [x] Criar tabela principal com links clicaveis.
- [x] Criar secoes Top Vagas e Empresas Prioritarias.
- [x] Criar graficos simples.
- [x] Adicionar exportacao CSV.
- [x] Tratar banco ausente, banco vazio e filtros sem resultado.
- [x] Documentar `streamlit run dashboard.py`.
- [x] Adicionar testes de carregamento, filtros e transformacao de dados.

## Fase 4 - Comparador Vaga x Perfil/Curriculo

- [x] Criar `config/profile_summary.yaml`.
- [x] Criar analisador local baseado em regras.
- [x] Gerar fit level, fit score, skills encontradas/faltantes, riscos, pontos fortes e mensagem ao recrutador.
- [x] Criar tabela `job_analyses`.
- [x] Criar servicos de analise para vagas novas, por score e reanalise.
- [x] Adicionar CLI com `--analyze`, `--analyze-only`, `--reanalyze` e `--analysis-min-score`.
- [x] Exibir analises no dashboard.
- [x] Exportar analises para CSV.
- [x] Incluir analise no e-mail quando disponivel.
- [x] Adicionar testes automatizados.

## Fase 5 - Agendamento Automatico no Windows

- [x] Criar pasta `scripts/`.
- [x] Criar pasta `logs/`.
- [x] Criar `scripts/run_jobradar_daily.bat`.
- [x] Criar `scripts/run_jobradar_dry_run.bat`.
- [x] Criar `scripts/open_dashboard.bat`.
- [x] Criar `docs/windows_task_scheduler.md`.
- [x] Criar `docs/production_setup.md`.
- [x] Atualizar `.gitignore` para runtime local e credenciais.
- [x] Atualizar README com comandos de agendamento.
- [x] Adicionar testes de scripts, docs e `.gitignore`.

## Fase 6 - Preparacao para GitHub e Portfolio

- [x] Criar `docs/images/`.
- [x] Criar guia de screenshots.
- [x] Criar `examples/sample_jobs.csv` com dados ficticios.
- [x] Criar `scripts/load_sample_data.py`.
- [x] Permitir escolha de banco no dashboard.
- [x] Atualizar `.gitignore` para proteger dados sensiveis e permitir sample DB.
- [x] Melhorar README com formato profissional.
- [x] Criar `PORTFOLIO_SUMMARY.md`.
- [x] Criar `RELEASE_NOTES.md`.
- [x] Criar `SECURITY.md`.
- [x] Adicionar MIT License.
- [x] Adicionar testes de documentacao, sample data e seguranca.

## Fase 7 - Release v0.6.0 e checklist final de publicacao

- [x] Criar `docs/PUBLISHING_CHECKLIST.md`.
- [x] Criar `docs/GITHUB_DESCRIPTION.md`.
- [x] Criar `docs/LINKEDIN_POST.md`.
- [x] Criar `docs/INTERVIEW_PITCH.md`.
- [x] Criar `scripts/check_publication_safety.py`.
- [x] Adicionar testes de documentacao de publicacao.
- [x] Atualizar README com Publicacao e Portfolio.
- [x] Atualizar release notes com v0.7.0.
- [x] Validar safety check e pytest.

## Fase 8 - Diagnostico e melhoria da BuscaPublica

- [x] Adicionar `--debug-search`.
- [x] Registrar query, URL, status HTTP, tamanho de HTML, links e vagas geradas.
- [x] Salvar HTML sanitizado e links extraidos em `logs/search_debug/`.
- [x] Melhorar parser DuckDuckGo com multiplos seletores e fallback `a[href]`.
- [x] Melhorar extracao e limpeza de URLs reais.
- [x] Ampliar filtros para Gupy, LinkedIn, Indeed, InfoJobs, Glassdoor, Catho e Vagas.com.br.
- [x] Adicionar queries fallback mais simples.
- [x] Evitar que uma query com falha interrompa as proximas.
- [x] Adicionar testes de parser, filtros, URL real e debug.

## Fase 9 - Fonte Gupy dedicada

- [x] Criar `config/gupy_companies.yaml`.
- [x] Criar loader de empresas Gupy.
- [x] Separar `MockGupySource` de `GupyPublicSource`.
- [x] Coletar paginas publicas `/` e `/jobs`.
- [x] Extrair links contendo `/jobs/`.
- [x] Extrair vagas de JSON embutido quando disponivel.
- [x] Deduplicar vagas dentro da fonte.
- [x] Adicionar logs por empresa, URL, status, HTML e vagas criadas.
- [x] Adicionar debug em `logs/gupy_debug/`.
- [x] Adicionar `--source gupy`.
- [x] Adicionar `--include-mock-in-all`.
- [x] Adicionar testes da fonte Gupy dedicada.

## Fase 10 - Enriquecimento da vaga Gupy por pagina de detalhe

- [x] Criar parser de detalhe Gupy.
- [x] Abrir paginas publicas de detalhe com timeout e user-agent transparente.
- [x] Extrair titulo, localidade, modalidade, descricao, responsabilidades, requisitos, beneficios, data e ID quando disponiveis.
- [x] Preservar vaga basica quando detalhe falhar.
- [x] Adicionar `GUPY_ENRICH_DETAILS`.
- [x] Adicionar `GUPY_MAX_DETAIL_PAGES`.
- [x] Adicionar `GUPY_DETAIL_REQUEST_DELAY_SECONDS`.
- [x] Adicionar logs de paginas abertas, enriquecidas e falhas.
- [x] Salvar debug de detalhe em `logs/gupy_debug/`.
- [x] Adicionar testes de parser, fallback, limite, enriquecimento e debug.

## Fase 11 - Curadoria de empresas-alvo Gupy

- [x] Atualizar `config/gupy_companies.yaml` com categorias.
- [x] Manter compatibilidade com formato antigo `companies`.
- [x] Adicionar campos opcionais `category`, `priority`, `status` e `notes`.
- [x] Manter Facens e slugs anteriores com status conhecido quando possivel.
- [x] Adicionar empresas candidatas para tecnologia, industria, energia, consultoria e mobilidade.
- [x] Registrar categoria, prioridade, status configurado e notas nos logs.
- [x] Criar relatorio `logs/gupy_debug/companies_status_YYYYMMDD_HHMMSS.csv`.
- [x] Adicionar testes de loader antigo, loader categorizado, campos opcionais, slug invalido e CSV de status.

## Fase 12 - Filtro tecnico avancado e ranking de relevancia

- [x] Criar pre-filtro rapido para vagas Gupy antes do enriquecimento.
- [x] Usar titulo, empresa, localidade, URL, categoria, prioridade e texto basico.
- [x] Adicionar secoes tecnicas e negativas em `config/profile_keywords.yaml`.
- [x] Criar `src/services/job_prefilter.py`.
- [x] Retornar `prefilter_score`, `prefilter_reason`, `should_enrich` e `should_keep`.
- [x] Aplicar pre-filtro na fonte Gupy apos deduplicacao.
- [x] Ordenar vagas mantidas por `prefilter_score`.
- [x] Enriquecer apenas melhores candidatas, respeitando `GUPY_MAX_DETAIL_PAGES`.
- [x] Registrar totais bruto, unico, descartado, mantido e selecionado para enriquecimento.
- [x] Gerar `logs/gupy_debug/prefilter_YYYYMMDD_HHMMSS.csv`.
- [x] Persistir `prefilter_score` e `prefilter_reason`.
- [x] Exibir pre-filtro no dashboard e no e-mail.
- [x] Adicionar testes de regras, ordenacao, motivos e integracao Gupy.

## Fase 13 - Auditoria do pre-filtro e ajuste fino de relevancia

- [x] Criar pasta `reports/`.
- [x] Ignorar relatorios gerados mantendo `reports/.gitkeep`.
- [x] Criar `src/services/prefilter_audit.py`.
- [x] Ler CSV de pre-filtro gerado em `logs/gupy_debug/`.
- [x] Classificar `audit_bucket`.
- [x] Gerar `reports/prefilter_audit_YYYYMMDD_HHMMSS.md`.
- [x] Gerar `reports/prefilter_audit_YYYYMMDD_HHMMSS.csv`.
- [x] Adicionar CLI `--audit-prefilter`.
- [x] Adicionar CLI `--audit-prefilter-only`.
- [x] Adicionar `--audit-input`.
- [x] Adicionar secao opcional de auditoria no dashboard.
- [x] Adicionar testes de bucket, leitura, resumo, Markdown, CSV e auditoria isolada.

## Fase 14 - Revisao humana e feedback de relevancia

- [x] Adicionar campos `review_status`, `review_notes`, `is_favorite`, `viewed_at` e `reviewed_at`.
- [x] Criar migracao simples para SQLite.
- [x] Criar `src/services/job_review_service.py`.
- [x] Permitir marcar vaga como visualizada.
- [x] Permitir status `unreviewed`, `relevant`, `irrelevant`, `maybe`, `applied` e `ignored`.
- [x] Permitir favorita e notas de revisao.
- [x] Criar resumo de feedback por status.
- [x] Criar exportacao `reports/job_review_feedback_YYYYMMDD_HHMMSS.csv`.
- [x] Adicionar CLI `--review-summary`.
- [x] Adicionar CLI `--export-review-feedback`.
- [x] Criar secao `Revisao Humana` no dashboard.
- [x] Adicionar metricas e filtros de revisao no dashboard.
- [x] Adicionar testes de migracao, servico, resumo, exportacao e CLI.

## Fase 15 - Consolidacao para release v1.0.0

- [x] Atualizar `RELEASE_NOTES.md` com `v1.0.0 - Primeira versao completa`.
- [x] Atualizar `PORTFOLIO_SUMMARY.md` com pipeline final e status v1.0.0.
- [x] Atualizar `README.md` com status v1.0.0, pipeline final e comandos principais.
- [x] Documentar dados ficticios, Gupy real e revisao humana no dashboard.
- [x] Reforcar que `.env`, `.venv/`, `data/jobs.db`, `logs/` e `reports/` nao sao versionados.
- [x] Atualizar `docs/PUBLISHING_CHECKLIST.md` para v1.0.0.
- [x] Atualizar `docs/LINKEDIN_POST.md` com versao final do post.
- [x] Atualizar `docs/INTERVIEW_PITCH.md` com pitch v1.0.0.
- [x] Atualizar `scripts/check_publication_safety.py` para verificar `reports/`.
- [x] Validar safety check e testes automatizados.

## Roadmap pos-v1.0

### Fase 16A - GitHub Actions CI e qualidade automatizada

- [x] Criar `.github/workflows/ci.yml`.
- [x] Configurar workflow para Ubuntu e Windows.
- [x] Usar Python 3.11.
- [x] Instalar dependencias com `pip install -r requirements.txt`.
- [x] Separar dependencias de desenvolvimento em `requirements-dev.txt`.
- [x] Rodar `python -m ruff check .`.
- [x] Rodar `python scripts/check_publication_safety.py`.
- [x] Rodar `python -m pytest`.
- [x] Atualizar README com badge real do GitHub Actions.
- [x] Atualizar `RELEASE_NOTES.md` com `v1.1.0 - CI e qualidade automatizada`.
- [x] Adicionar testes para garantir que o workflow existe e roda os comandos obrigatorios.

### Fase 16B - Sugestoes de ajuste baseadas em feedback humano

- [x] Criar `src/services/feedback_insights.py`.
- [x] Ler vagas revisadas no SQLite e gerar insights por status, termos, empresas, titulos, localidades, falsos positivos, falsos negativos e favoritas.
- [x] Criar relatorio Markdown `reports/feedback_insights_YYYYMMDD_HHMMSS.md`.
- [x] Criar relatorio CSV `reports/feedback_insights_YYYYMMDD_HHMMSS.csv`.
- [x] Adicionar colunas `insight_type`, `candidate`, `count`, `evidence`, `recommendation` e `confidence`.
- [x] Adicionar CLI `--feedback-insights`.
- [x] Adicionar CLI `--feedback-insights-min-reviewed`.
- [x] Gerar relatorio mesmo com poucas revisoes e aviso de baixa confianca.
- [x] Adicionar secao opcional `Insights de Feedback` no dashboard.
- [x] Adicionar testes de servico, Markdown, CSV e CLI.
- [x] Atualizar README com fluxo de calibracao assistida.
- [x] Atualizar `RELEASE_NOTES.md` com `v1.2.0 - Feedback insights e calibracao assistida`.
- [x] Garantir que `profile_keywords.yaml` nao e alterado automaticamente.

### Fase 16 - Ajustes automaticos ou semi-automaticos de pesos

- [ ] Gerar sugestoes de novos termos positivos e negativos a partir da auditoria.
- [x] Usar feedback humano para sugerir ajustes de pesos.
- [ ] Criar modo interativo para marcar falso positivo/falso negativo.
- [ ] Gerar patch sugerido para `profile_keywords.yaml`.
- [ ] Comparar impacto antes/depois do ajuste em uma amostra fixa.
- [ ] Criar metricas de precisao manual por rodada.

### Proximas fases sugeridas

- [ ] Aplicar sugestoes manualmente em `profile_keywords.yaml` e comparar resultados.
- [ ] Melhorar schema/migracoes do SQLite.
- [ ] Adicionar mais fontes ou APIs publicas oficiais.
- [ ] Melhorar dashboard com pagina de detalhes da vaga.

### Fase 17 - Melhorias visuais e screenshots finais

- [x] Organizar dashboard em abas com secoes claras.
- [x] Criar visao inicial `Resumo Executivo`.
- [x] Destacar pipeline Coleta -> Pre-filtro -> Match -> Analise -> Revisao.
- [x] Criar secao `Funil de Vagas`.
- [x] Manter secoes `Top Vagas`, `Analise Vaga x Perfil`, `Revisao Humana`, `Auditoria do Pre-filtro`, `Insights de Feedback` e `Exportacoes`.
- [x] Criar helper para padronizar nomes de colunas exibidas.
- [x] Atualizar README com `Demonstracao visual`.
- [x] Atualizar `docs/SCREENSHOTS_GUIDE.md` com checklist final.
- [x] Criar `docs/DEMO_SCRIPT.md`.
- [x] Atualizar `PORTFOLIO_SUMMARY.md` com demo visual e prints recomendados.
- [x] Atualizar `RELEASE_NOTES.md` com `v1.3.0 - Visual polish e demo para portfolio`.
- [x] Adicionar testes para docs visuais e helper de colunas.

### Fase 18 - Screenshots, README visual e publicacao final

- [x] Garantir pasta `docs/images/`.
- [x] Criar placeholders seguros para screenshots esperados.
- [x] Documentar tela, aba, banco ficticio e PNG final em cada placeholder.
- [x] Atualizar README mantendo referencias aos PNGs finais.
- [x] Atualizar `docs/SCREENSHOTS_GUIDE.md` com passo a passo final e checklist de privacidade.
- [x] Atualizar `docs/DEMO_SCRIPT.md` com roteiro de screenshots.
- [x] Atualizar `PORTFOLIO_SUMMARY.md` com `Evidencias visuais`.
- [x] Atualizar `RELEASE_NOTES.md` com `v1.4.0 - Screenshots e README visual`.
- [x] Adicionar testes para placeholders, README visual, screenshots guide e demo script.

### Roadmap pos-v1.4

- [ ] Capturar imagens finais manualmente usando `Dados ficticios`.
- [ ] Criar GIF curto da demo.
- [ ] Publicar post no LinkedIn.
- [ ] Considerar deploy opcional local/cloud.
- [ ] Avaliar fonte adicional via API oficial/opcional.
- [ ] Aplicar sugestoes manualmente em `profile_keywords.yaml` e comparar resultados.
- [ ] Melhorar schema/migracoes do SQLite.

### Fase 19 - Testes determinísticos, anti-rede e estabilidade operacional

- [x] Criar `pytest.ini` com `testpaths`, markers e `--strict-markers`.
- [x] Adicionar markers `unit`, `integration`, `network` e `slow`.
- [x] Criar `tests/conftest.py`.
- [x] Bloquear `requests.sessions.Session.request` por padrao durante `pytest`.
- [x] Permitir rede apenas com `@pytest.mark.network`.
- [x] Criar mensagem clara para tentativa de rede real em teste.
- [x] Revisar testes de Gupy, busca publica e dashboard para manter mocks/fixtures locais.
- [x] Criar `tests/helpers.py` para mensagem compartilhada do bloqueio.
- [x] Adicionar teste garantindo que rede real e bloqueada.
- [x] Adicionar teste garantindo que marcador `network` libera o bloqueio sem chamada real.
- [x] Atualizar README com testes offline e diferenca entre teste e execucao real.
- [x] Atualizar `docs/PUBLISHING_CHECKLIST.md`.
- [x] Atualizar `RELEASE_NOTES.md` com `v1.5.0 - Testes determinísticos e bloqueio de rede`.

### Roadmap pos-v1.5

- [ ] Adicionar CI com coverage.
- [ ] Revisar cache de dependencias no GitHub Actions.
- [ ] Criar testes de integracao opcionais marcados como `network`.
- [ ] Avaliar deploy/demo opcional.
- [ ] Avaliar SerpAPI, Bing Search API ou Google Custom Search API.
- [ ] Gerar sugestoes automaticas de slugs Gupy a partir de empresas-alvo.
- [ ] Criar comando de diagnostico apenas para empresas Gupy.

### Fase 20 - Observabilidade local e relatório de execução

- [x] Criar `src/services/run_reporter.py`.
- [x] Coletar `run_id`, horarios, duracao, modo, source, fontes, totais, status de e-mail e erros.
- [x] Gerar relatorio Markdown em `runs/run_report_YYYYMMDD_HHMMSS.md`.
- [x] Gerar relatorio JSON em `runs/run_report_YYYYMMDD_HHMMSS.json`.
- [x] Proteger `runs/` no `.gitignore` mantendo `runs/.gitkeep`.
- [x] Integrar `--run-report` em `src/main.py`.
- [x] Integrar `--no-run-report` em `src/main.py`.
- [x] Adicionar `--latest-run-report`.
- [x] Atualizar scripts Windows para usar `--run-report`.
- [x] Adicionar testes de Markdown, JSON, `.gitignore`, CLI e sanitizacao.
- [x] Atualizar README, checklist, release notes e TODO.

### Fase 21 - Dashboard de execucoes e historico operacional

- [x] Criar `src/services/run_history.py`.
- [x] Localizar e carregar JSONs validos em `runs/run_report_*.json`.
- [x] Ignorar JSONs invalidos com fallback seguro.
- [x] Ordenar execucoes da mais recente para a mais antiga.
- [x] Normalizar linhas para dashboard com metricas principais.
- [x] Calcular resumo de execucoes, vagas, e-mails, erros, duracao media e fonte mais usada.
- [x] Criar aba `Historico de Execucoes` no dashboard.
- [x] Adicionar filtros por fonte, modo, e-mail enviado e erro.
- [x] Exibir detalhes da execucao selecionada.
- [x] Adicionar exportacao CSV do historico no dashboard.
- [x] Adicionar CLI `--run-history-summary`.
- [x] Adicionar testes de servico, resumo, CLI e helper do dashboard.
- [x] Atualizar README, checklist, release notes e TODO.

### Fase 22 - Alertas de falha e resumo operacional por e-mail

- [x] Criar `src/services/operational_alerts.py`.
- [x] Gerar `subject`, `body_text` e `should_send` a partir do run report.
- [x] Criar tipos `failure`, `no_jobs`, `no_email_eligible` e `success_summary`.
- [x] Adicionar configuracoes `OPERATIONAL_ALERTS_*` e `OPERATIONAL_DAILY_SUMMARY`.
- [x] Reutilizar SMTP existente em fluxo separado do e-mail de vagas.
- [x] Respeitar dry-run para nao enviar e-mail real.
- [x] Integrar alertas ao final da execucao com `--run-report`.
- [x] Registrar status do alerta operacional no run report.
- [x] Adicionar CLI `--send-operational-alerts` e `--no-operational-alerts`.
- [x] Adicionar CLI `--test-operational-alert`.
- [x] Adicionar testes de tipos de alerta, configuracao, dry-run, CLI e run report.
- [x] Atualizar README, guia de producao, release notes e TODO.

### Fase 23 - Dashboard de alertas operacionais

- [x] Extrair `operational_alert_type` dos JSONs de `runs/`.
- [x] Extrair `operational_alert_should_send`, `operational_alert_sent` e `operational_alert_reason`.
- [x] Calcular total de alertas, enviados, por tipo, execucoes sem alerta e ultimo alerta.
- [x] Calcular totais de `failure`, `no_jobs`, `no_email_eligible` e `success_summary`.
- [x] Criar aba `Alertas Operacionais` no dashboard.
- [x] Exibir metricas principais de alertas.
- [x] Exibir tabela filtravel com alertas operacionais.
- [x] Adicionar filtros por tipo, envio, fonte e modo.
- [x] Adicionar exportacao CSV dos alertas filtrados.
- [x] Atualizar `--run-history-summary` com dados de alertas.
- [x] Adicionar CLI `--operational-alerts-summary`.
- [x] Adicionar testes de servico, CLI e helper do dashboard.
- [x] Atualizar README, checklist, release notes e TODO.

### Fase 24 - Backup, restauracao e manutencao do banco local

- [x] Criar pasta `backups/` com `backups/.gitkeep`.
- [x] Proteger `backups/` no `.gitignore`.
- [x] Criar `src/services/database_maintenance.py`.
- [x] Criar backup de `data/jobs.db` em `backups/jobs_backup_YYYYMMDD_HHMMSS.db`.
- [x] Criar manifesto JSON com timestamp, origem, destino, tamanho, SHA-256 e motivo.
- [x] Listar backups disponiveis.
- [x] Verificar integridade de backup com SHA-256 e `PRAGMA integrity_check`.
- [x] Restaurar backup apenas com confirmacao explicita.
- [x] Criar backup automatico do estado atual antes de restaurar.
- [x] Exportar resumo agregado do banco em CSV/JSON.
- [x] Executar `VACUUM` e `ANALYZE` com checagem de integridade.
- [x] Adicionar CLI `--backup-db`, `--backup-reason`, `--list-db-backups`, `--verify-db-backup`, `--restore-db-backup`, `--confirm-restore`, `--db-maintenance` e `--export-db-summary`.
- [x] Adicionar `AUTO_BACKUP_BEFORE_RUN` e `BACKUP_RETENTION_DAYS`.
- [x] Integrar backup automatico antes da coleta principal quando configurado.
- [x] Registrar backup automatico no run report quando houver `--run-report`.
- [x] Atualizar README, guia de producao, checklist, release notes e TODO.
- [x] Adicionar testes de backup, restore, exportacao, manutencao e protecao Git.

### Fase 25 - Dashboard de backups e manutencao do banco

- [x] Criar aba `Backups e Banco` no dashboard.
- [x] Listar manifestos validos em `backups/*.json`.
- [x] Ignorar manifestos invalidos de forma segura.
- [x] Mostrar timestamp, motivo, caminho, tamanho, SHA curto e status de verificacao.
- [x] Mostrar metricas de total, tamanho total, backup mais recente e maior backup.
- [x] Exportar lista de backups para CSV.
- [x] Mostrar comandos recomendados de backup, verificacao, resumo e manutencao.
- [x] Manter restauracao fora do dashboard nesta fase.
- [x] Expor helpers `load_backup_manifest_rows`, `summarize_backups`, `format_backup_size` e `short_sha256`.
- [x] Adicionar CLI `--db-backup-summary`.
- [x] Atualizar README, guia de producao, checklist, release notes e TODO.
- [x] Adicionar testes de manifestos, resumo, helper, CLI e colunas do dashboard.

### Fase 26 - Retencao automatica de backups e limpeza segura

- [x] Criar plano de retencao para `backups/jobs_backup_*.json`.
- [x] Parear manifesto com arquivo `.db`.
- [x] Calcular idade do backup.
- [x] Identificar backups acima de `BACKUP_RETENTION_DAYS`.
- [x] Nunca remover o backup mais recente.
- [x] Proteger manifestos invalidos por padrao.
- [x] Gerar plano com encontrados, candidatos, protegidos, motivos e espaco recuperavel.
- [x] Adicionar CLI `--cleanup-db-backups`.
- [x] Adicionar CLI `--cleanup-db-backups-dry-run`.
- [x] Adicionar CLI `--confirm-cleanup-backups`.
- [x] Gerar relatorios `reports/backup_cleanup_YYYYMMDD_HHMMSS.md` e `.csv`.
- [x] Adicionar `BACKUP_CLEANUP_DRY_RUN`.
- [x] Atualizar dashboard com politica de retencao e candidatos.
- [x] Atualizar README, guia de producao, checklist, release notes e TODO.
- [x] Adicionar testes de plano, dry-run, confirmacao, manifestos invalidos e relatorios.

### Fase 27 - Cobertura de testes e badge de cobertura

- [x] Adicionar `pytest-cov` em `requirements-dev.txt`.
- [x] Documentar comando `python -m pytest --cov=src --cov-report=term-missing --cov-report=html`.
- [x] Garantir relatorio HTML em `htmlcov/`.
- [x] Ignorar `htmlcov/`, `.coverage` e `coverage.xml`.
- [x] Atualizar GitHub Actions para rodar coverage no CI.
- [x] Manter Ruff e safety check no CI.
- [x] Atualizar README com secao `Cobertura de testes`.
- [x] Adicionar badge estatico de cobertura medida localmente.
- [x] Atualizar checklist, release notes e TODO.
- [x] Adicionar testes documentais para dependencia, ignores e README.

### Fase 28 - Gerenciamento seguro de SQLite e limpeza de warnings

- [x] Rodar `python -W default -m pytest` para identificar `ResourceWarning`.
- [x] Rastrear conexoes SQLite nao fechadas com `PYTHONTRACEMALLOC`.
- [x] Ajustar `JobRepository` para evitar conexoes retidas em pool.
- [x] Adicionar `close()` e context manager ao repositorio.
- [x] Corrigir conexoes diretas no dashboard com `contextlib.closing`.
- [x] Corrigir script de dados ficticios para fechar conexao e commitar explicitamente.
- [x] Corrigir teste de dashboard que criava SQLite temporario.
- [x] Rodar `python -W default -m pytest` sem warnings relevantes.
- [x] Atualizar README, release notes, checklist, portfolio e TODO.

### Fase 29 - Limite minimo de cobertura no CI

- [x] Manter `python -m pytest` simples fora do coverage global.
- [x] Atualizar GitHub Actions com limite minimo inicial de cobertura.
- [x] Atualizar README com cobertura minima atual de 80%.
- [x] Documentar cobertura local em torno de 86%.
- [x] Atualizar checklist com comando de coverage e limite minimo.
- [x] Atualizar release notes, portfolio e TODO.
- [x] Adicionar testes documentais para CI, README e checklist.

### Fase 30 - Melhoria de cobertura dos modulos criticos

- [x] Rodar coverage com o limite vigente para identificar lacunas.
- [x] Priorizar `src/main.py` como modulo critico com maior gap.
- [x] Adicionar testes para relatorio de execucao ausente.
- [x] Adicionar testes para auditoria de pre-filtro sem CSV.
- [x] Adicionar testes para backup automatico antes da execucao.
- [x] Adicionar testes para wrappers de backup, verificacao, manutencao, exportacao e limpeza.
- [x] Adicionar testes para alertas operacionais desativados e falha de envio.
- [x] Adicionar testes para falha SMTP e alerta operacional no `EmailSender`.
- [x] Atualizar README, release notes, portfolio e TODO.

### Fase 31 - Limite minimo de cobertura elevado para 85%

- [x] Atualizar GitHub Actions para `--cov-fail-under=85`.
- [x] Atualizar README com cobertura minima atual de 85%.
- [x] Manter cobertura local aproximada em torno de 88%.
- [x] Atualizar checklist de publicacao com o novo limite.
- [x] Atualizar release notes, portfolio e TODO.
- [x] Atualizar testes documentais para validar o novo limite ativo.
- [x] Garantir que o limite antigo nao aparece em documentacao operacional.

### Fase 32 - Revisao de modulos de baixa cobertura e decisao arquitetural

- [x] Rodar coverage com `--cov-fail-under=85`.
- [x] Classificar modulos de baixa cobertura por importancia e papel.
- [x] Criar `docs/COVERAGE_REVIEW.md`.
- [x] Documentar `SearchEngineSource` como fallback experimental.
- [x] Confirmar testes de parser, challenge, fallback sem links e filtro de dominio.
- [x] Adicionar testes uteis para busca desativada, challenge sem links e falha de request.
- [x] Decidir manter `scheduler.py` como utilitario futuro com teste minimo.
- [x] Decidir manter fontes placeholder como contratos futuros documentados.
- [x] Adicionar docstrings e testes minimos para fontes placeholder.
- [x] Atualizar README, release notes, portfolio e TODO.

### Fase 33 - Schema versionado e migracoes controladas

- [x] Criar `src/schema_migrations.py`.
- [x] Criar tabela `schema_migrations`.
- [x] Definir `CURRENT_SCHEMA_VERSION`.
- [x] Implementar `get_applied_migrations`.
- [x] Implementar `apply_schema_migrations`.
- [x] Criar migracao inicial idempotente.
- [x] Integrar migracoes ao `JobRepository.init_db`.
- [x] Adicionar CLI `--schema-status`.
- [x] Adicionar CLI `--migrate-schema`.
- [x] Adicionar testes para banco novo, legado, idempotencia e CLI.
- [x] Atualizar README, guia de producao, checklist, release notes, portfolio e TODO.

### Fase 34 - Indices de performance e saude do banco

- [x] Elevar `CURRENT_SCHEMA_VERSION` para 2.
- [x] Adicionar migracao v2 para indices SQLite idempotentes.
- [x] Criar indices em colunas relevantes de `jobs`, `job_analyses` e `schema_migrations`.
- [x] Garantir que a migracao v2 nao falha com colunas opcionais ausentes.
- [x] Criar `src/services/database_health.py`.
- [x] Adicionar CLI `--db-health`.
- [x] Adicionar CLI `--export-db-health`.
- [x] Adicionar secao `Saude do Banco` no dashboard.
- [x] Atualizar README, guia de producao, checklist, release notes, portfolio e TODO.
- [x] Adicionar testes para indices, saude do banco, exportacao, CLI e dashboard helper.

### Fase 35 - Release v3.0.0, revisao final e publicacao

- [x] Revisar README com status v3.0.0, 198 testes, 91% coverage, limite 85%, schema versionado e saude do banco.
- [x] Revisar `PORTFOLIO_SUMMARY.md` com pipeline final e metricas finais.
- [x] Revisar `RELEASE_NOTES.md` sem duplicar versoes.
- [x] Revisar `TODO.md` e consolidar ideias futuras no roadmap pos-v3.0.
- [x] Revisar `docs/PUBLISHING_CHECKLIST.md` com comandos finais de validacao.
- [x] Atualizar `docs/DEMO_SCRIPT.md` com historico, alertas, backups e saude do banco.
- [x] Atualizar `docs/LINKEDIN_POST.md` para divulgacao v3.0.0.
- [x] Atualizar `docs/INTERVIEW_PITCH.md` com arquitetura e operacao v3.0.0.
- [x] Reforcar `scripts/check_publication_safety.py` para artefatos de coverage.
- [x] Atualizar testes documentais da release final.

### Roadmap pos-v3.0

- [ ] Avaliar Alembic se o schema crescer.
- [ ] Integrar APIs oficiais de busca de forma opcional.
- [ ] Subir cobertura minima para 90%.
- [ ] Avaliar criptografia opcional de backups.
- [ ] Criar deploy/demo opcional.
- [ ] Fazer melhorias visuais finais e capturar screenshots com dados ficticios.
- [ ] Metricas de crescimento do banco.
- [ ] Dashboard de performance historica.
- [ ] Otimizacao das queries do dashboard.

### Fase 36 - API de busca opcional e sugestoes de slugs

- [ ] Avaliar SerpAPI, Bing Search API ou Google Custom Search API.
- [ ] Gerar sugestoes automaticas de slugs Gupy a partir de empresas-alvo.
- [ ] Criar comando de diagnostico apenas para empresas Gupy.
- [ ] Marcar automaticamente status observado em relatorio separado.
- [ ] Priorizar empresas com vagas tecnicas reais nos ultimos dias.

### Fase 37 - Qualidade das fontes

- [ ] Adicionar clientes para APIs publicas oficiais quando disponiveis.
- [ ] Melhorar coleta Gupy.
- [ ] Melhorar coleta por empresa-alvo.
- [ ] Ampliar empresas-alvo com slugs validos.
- [ ] Melhorar extracao de empresa, local e data nas buscas publicas.
- [ ] Criar limites configuraveis por fonte.
- [ ] Adicionar cache de consultas.
- [ ] Separar resultados de busca por fonte de forma mais precisa.

### Fase 38 - Produto local

- [ ] Adicionar pagina de detalhes da vaga no dashboard.
- [ ] Exportacao Excel.
- [ ] Lista de bloqueio e favoritos.
- [ ] Acao manual para marcar vaga como enviada ou favorita.
- [ ] Editor local do perfil YAML pelo dashboard.
- [ ] Adicionar screenshots reais sanitizados.

### Fase 39 - Operacao

- [ ] Logs rotativos em arquivo.
- [ ] Alertas de falha por fonte.
- [ ] Container Docker opcional.
- [x] Pipeline de CI com pytest.
- [x] Adicionar CI GitHub Actions.
- [x] Criar release documental v3.0.0.
