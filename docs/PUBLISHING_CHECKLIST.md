# Publishing Checklist v3.0.0

Use esta lista antes de publicar o projeto no GitHub ou compartilhar no portfolio.

## Validacao local

- [ ] Rodar `python scripts/check_publication_safety.py`.
- [ ] Rodar `python -m ruff check .`.
- [ ] Rodar `python -m pytest`.
- [ ] Rodar `python -W default -m pytest`.
- [ ] Rodar `python -m pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=85`.
- [ ] Confirmar que `python -m pytest` roda sem internet real.
- [ ] Rodar `python scripts/load_sample_data.py`.
- [ ] Abrir dashboard com `streamlit run dashboard.py`.
- [ ] Confirmar que o seletor do dashboard esta em `Dados ficticios` para screenshots.
- [ ] Revisar `docs/DEMO_SCRIPT.md`.
- [ ] Revisar `docs/SCREENSHOTS_GUIDE.md`.
- [ ] Revisar `docs/COVERAGE_REVIEW.md`.
- [ ] Confirmar placeholders em `docs/images/*.placeholder.txt`.
- [ ] Testar coleta segura: `python -m src.main --source mock --analyze --dry-run --min-score 50 --analysis-min-score 50`.
- [ ] Testar comandos de revisao: `python -m src.main --review-summary`.
- [ ] Testar insights de feedback: `python -m src.main --feedback-insights`.
- [ ] Testar relatório de execução: `python -m src.main --source mock --dry-run --run-report`.
- [ ] Testar último relatório: `python -m src.main --latest-run-report`.
- [ ] Testar historico operacional: `python -m src.main --run-history-summary`.
- [ ] Testar resumo de alertas operacionais: `python -m src.main --operational-alerts-summary`.
- [ ] Testar alerta operacional em dry-run: `python -m src.main --test-operational-alert --dry-run`.
- [ ] Testar backup do banco: `python -m src.main --backup-db --backup-reason "checklist"`.
- [ ] Testar listagem de backups: `python -m src.main --list-db-backups`.
- [ ] Testar resumo de backups: `python -m src.main --db-backup-summary`.
- [ ] Testar exportacao de resumo do banco: `python -m src.main --export-db-summary`.
- [ ] Testar manutencao do banco: `python -m src.main --db-maintenance`.
- [ ] Testar limpeza dry-run de backups: `python -m src.main --cleanup-db-backups-dry-run`.
- [ ] Verificar schema do banco: `python -m src.main --schema-status`.
- [ ] Verificar saude do banco: `python -m src.main --db-health`.
- [ ] Rodar `git status`.
- [ ] Rodar `git check-ignore -v .env data/jobs.db logs reports runs backups htmlcov .coverage .venv`.
- [ ] Revisar `README.md`.
- [ ] Revisar `SECURITY.md`.
- [ ] Revisar `PORTFOLIO_SUMMARY.md`.
- [ ] Revisar `RELEASE_NOTES.md`.

## Verificacao Git

- [ ] Rodar `git status`.
- [ ] Rodar `git ls-files`.
- [ ] Confirmar que `.env` nao esta versionado.
- [ ] Confirmar que `.venv/` nao esta versionado.
- [ ] Confirmar que `data/jobs.db` nao esta versionado.
- [ ] Confirmar que `logs/` nao esta versionado.
- [ ] Confirmar que `reports/` nao esta versionado, exceto `reports/.gitkeep`.
- [ ] Confirmar que `runs/` nao esta versionado, exceto `runs/.gitkeep`.
- [ ] Confirmar que `backups/` nao esta versionado, exceto `backups/.gitkeep`.
- [ ] Confirmar que exemplos usam apenas dados ficticios.
- [ ] Confirmar que `data/sample_jobs.db`, se versionado, foi gerado apenas com `examples/sample_jobs.csv`.

## Screenshots e portfolio

- [ ] Usar `data/sample_jobs.db` ou dados sanitizados.
- [ ] Nao expor e-mail real.
- [ ] Nao expor credenciais.
- [ ] Nao expor banco real.
- [ ] Nao expor logs reais.
- [ ] Nao expor relatorios reais.
- [ ] Nao expor relatorios reais de `runs/`.
- [ ] Nao expor backups reais de `backups/`.
- [ ] Nao expor links sensiveis.

## Release v3.0.0

- [ ] Conferir `RELEASE_NOTES.md` com `v3.0.0 - Indices de performance e saude do banco`.
- [ ] Conferir `PORTFOLIO_SUMMARY.md` com pipeline final.
- [ ] Conferir badge do GitHub Actions no `README.md`.
- [ ] Conferir `.github/workflows/ci.yml`.
- [ ] Conferir `docs/GITHUB_DESCRIPTION.md`.
- [ ] Conferir `docs/LINKEDIN_POST.md`.
- [ ] Conferir `docs/INTERVIEW_PITCH.md`.
- [ ] Criar commit final.
- [ ] Criar tag `v3.0.0`.
- [ ] Conferir pagina do repositorio no GitHub.
- [ ] Preencher campo About com `docs/GITHUB_DESCRIPTION.md`.
- [ ] Publicar post somente depois da revisao final.
