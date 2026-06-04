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

## Fase 15 - Ajustes automaticos ou semi-automaticos de pesos

- [ ] Gerar sugestoes de novos termos positivos e negativos a partir da auditoria.
- [ ] Usar feedback humano para sugerir ajustes de pesos.
- [ ] Criar modo interativo para marcar falso positivo/falso negativo.
- [ ] Gerar patch sugerido para `profile_keywords.yaml`.
- [ ] Comparar impacto antes/depois do ajuste em uma amostra fixa.
- [ ] Criar metricas de precisao manual por rodada.

## Fase 16 - Enriquecimento por prioridade e dashboard

- [ ] Ajustar dashboard para analisar funil Gupy por empresa e pre-filtro.
- [ ] Criar filtros por `prefilter_score`.
- [ ] Enriquecer detalhes por prioridade combinada de empresa, localidade e pre-filtro.
- [ ] Criar pagina de detalhes da vaga no dashboard.
- [ ] Adicionar controle manual de favoritos/bloqueios.

## Fase 17 - API de busca opcional e sugestoes de slugs

- [ ] Avaliar SerpAPI, Bing Search API ou Google Custom Search API.
- [ ] Gerar sugestoes automaticas de slugs Gupy a partir de empresas-alvo.
- [ ] Criar comando de diagnostico apenas para empresas Gupy.
- [ ] Marcar automaticamente status observado em relatorio separado.
- [ ] Priorizar empresas com vagas tecnicas reais nos ultimos dias.

## Fase 18 - Qualidade das fontes

- [ ] Adicionar clientes para APIs publicas oficiais quando disponiveis.
- [ ] Melhorar coleta Gupy.
- [ ] Melhorar coleta por empresa-alvo.
- [ ] Ampliar empresas-alvo com slugs validos.
- [ ] Melhorar extracao de empresa, local e data nas buscas publicas.
- [ ] Criar limites configuraveis por fonte.
- [ ] Adicionar cache de consultas.
- [ ] Separar resultados de busca por fonte de forma mais precisa.

## Fase 19 - Produto local

- [ ] Adicionar pagina de detalhes da vaga no dashboard.
- [ ] Exportacao Excel.
- [ ] Lista de bloqueio e favoritos.
- [ ] Acao manual para marcar vaga como enviada ou favorita.
- [ ] Editor local do perfil YAML pelo dashboard.
- [ ] Adicionar screenshots reais sanitizados.

## Fase 20 - Operacao

- [ ] Logs rotativos em arquivo.
- [ ] Alertas de falha por fonte.
- [ ] Container Docker opcional.
- [ ] Pipeline de CI com pytest.
- [ ] Adicionar CI GitHub Actions.
- [ ] Criar release v1.0.0.
