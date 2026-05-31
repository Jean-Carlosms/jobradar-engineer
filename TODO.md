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

## Fase 8 - Qualidade das fontes

- [ ] Adicionar clientes para APIs publicas oficiais quando disponiveis.
- [ ] Melhorar coleta Gupy.
- [ ] Melhorar extracao de empresa, local e data nas buscas publicas.
- [ ] Criar limites configuraveis por fonte.
- [ ] Adicionar cache de consultas.
- [ ] Separar resultados de busca por fonte de forma mais precisa.

## Fase 9 - Produto local

- [ ] Adicionar pagina de detalhes da vaga no dashboard.
- [ ] Exportacao Excel.
- [ ] Lista de bloqueio e favoritos.
- [ ] Acao manual para marcar vaga como enviada ou favorita.
- [ ] Editor local do perfil YAML pelo dashboard.
- [ ] Adicionar screenshots reais sanitizados.

## Fase 10 - Operacao

- [ ] Logs rotativos em arquivo.
- [ ] Alertas de falha por fonte.
- [ ] Container Docker opcional.
- [ ] Pipeline de CI com pytest.
- [ ] Adicionar CI GitHub Actions.
- [ ] Criar release v1.0.0.
