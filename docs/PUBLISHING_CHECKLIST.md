# Publishing Checklist v1.3.0

Use esta lista antes de publicar o projeto no GitHub ou compartilhar no portfolio.

## Validacao local

- [ ] Rodar `python scripts/check_publication_safety.py`.
- [ ] Rodar `python -m ruff check .`.
- [ ] Rodar `python -m pytest`.
- [ ] Rodar `python scripts/load_sample_data.py`.
- [ ] Abrir dashboard com `streamlit run dashboard.py`.
- [ ] Confirmar que o seletor do dashboard esta em `Dados ficticios` para screenshots.
- [ ] Revisar `docs/DEMO_SCRIPT.md`.
- [ ] Revisar `docs/SCREENSHOTS_GUIDE.md`.
- [ ] Testar coleta segura: `python -m src.main --source mock --analyze --dry-run --min-score 50 --analysis-min-score 50`.
- [ ] Testar comandos de revisao: `python -m src.main --review-summary`.
- [ ] Testar insights de feedback: `python -m src.main --feedback-insights`.
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
- [ ] Confirmar que exemplos usam apenas dados ficticios.
- [ ] Confirmar que `data/sample_jobs.db`, se versionado, foi gerado apenas com `examples/sample_jobs.csv`.

## Screenshots e portfolio

- [ ] Usar `data/sample_jobs.db` ou dados sanitizados.
- [ ] Nao expor e-mail real.
- [ ] Nao expor credenciais.
- [ ] Nao expor banco real.
- [ ] Nao expor logs reais.
- [ ] Nao expor relatorios reais.
- [ ] Nao expor links sensiveis.

## Release v1.3.0

- [ ] Conferir `RELEASE_NOTES.md` com `v1.3.0 - Visual polish e demo para portfolio`.
- [ ] Conferir `PORTFOLIO_SUMMARY.md` com pipeline final.
- [ ] Conferir badge do GitHub Actions no `README.md`.
- [ ] Conferir `.github/workflows/ci.yml`.
- [ ] Conferir `docs/GITHUB_DESCRIPTION.md`.
- [ ] Conferir `docs/LINKEDIN_POST.md`.
- [ ] Conferir `docs/INTERVIEW_PITCH.md`.
- [ ] Criar commit final.
- [ ] Criar tag `v1.3.0`.
- [ ] Conferir pagina do repositorio no GitHub.
- [ ] Preencher campo About com `docs/GITHUB_DESCRIPTION.md`.
- [ ] Publicar post somente depois da revisao final.
