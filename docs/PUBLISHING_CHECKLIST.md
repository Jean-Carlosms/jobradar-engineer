# Publishing Checklist

Use esta lista antes de publicar o projeto no GitHub ou compartilhar no portfolio.

## Validacao local

- [ ] Rodar `python -m pytest`.
- [ ] Rodar `python scripts/load_sample_data.py`.
- [ ] Abrir dashboard com dados ficticios.
- [ ] Confirmar que o seletor do dashboard esta em `Dados ficticios` para screenshots.
- [ ] Revisar `README.md`.
- [ ] Revisar `SECURITY.md`.
- [ ] Revisar `PORTFOLIO_SUMMARY.md`.
- [ ] Revisar `RELEASE_NOTES.md`.

## Verificacao Git

- [ ] Rodar `git status`.
- [ ] Rodar `git ls-files`.
- [ ] Confirmar que `.env` nao esta versionado.
- [ ] Confirmar que `data/jobs.db` nao esta versionado.
- [ ] Confirmar que `logs/` nao esta versionado.
- [ ] Confirmar que `.venv/` nao esta versionado.
- [ ] Confirmar que exemplos usam dados ficticios.
- [ ] Confirmar que `data/sample_jobs.db`, se versionado, foi gerado apenas com `examples/sample_jobs.csv`.

## Screenshots

- [ ] Revisar screenshots antes de publicar.
- [ ] Nao expor e-mail real.
- [ ] Nao expor credenciais.
- [ ] Nao expor banco real.
- [ ] Nao expor logs reais.
- [ ] Nao expor links sensiveis.

## Release

- [ ] Rodar `python scripts/check_publication_safety.py`.
- [ ] Criar commit.
- [ ] Criar tag `v0.6.0` se a publicacao for da versao de portfolio.
- [ ] Conferir pagina do repositorio no GitHub.
- [ ] Preencher campo About com `docs/GITHUB_DESCRIPTION.md`.
- [ ] Publicar post somente depois da revisao final.
