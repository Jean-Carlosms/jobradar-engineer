# Screenshots Guide

Use este guia para preparar imagens do JobRadar Engineer para GitHub, portfolio e apresentacoes.

## Regra principal

Use somente o banco `Dados ficticios` no dashboard para screenshots publicos.

```bat
python scripts\load_sample_data.py
streamlit run dashboard.py
```

No seletor lateral `Banco de dados`, escolha `Dados ficticios`.

## Resolucao sugerida

- 1366x768 para screenshots compactos.
- 1440x900 para README, portfolio e apresentacoes.

## Arquivos padronizados

Salve os prints em `docs/images/` com estes nomes:

- `dashboard-overview.png`
- `job-funnel.png`
- `top-jobs.png`
- `job-profile-analysis.png`
- `human-review.png`
- `prefilter-audit.png`
- `feedback-insights.png`

## Checklist final de screenshots

- [ ] `dashboard-overview.png`: aba `Resumo Executivo`.
- [ ] `job-funnel.png`: aba `Funil de Vagas`.
- [ ] `top-jobs.png`: aba `Top Vagas`.
- [ ] `job-profile-analysis.png`: aba `Analise Vaga x Perfil`.
- [ ] `human-review.png`: aba `Revisao Humana`.
- [ ] `prefilter-audit.png`: aba `Auditoria do Pre-filtro`.
- [ ] `feedback-insights.png`: aba `Insights de Feedback`.
- [ ] Todos os prints usam `Dados ficticios`.
- [ ] Nenhum print mostra e-mail real, credenciais, tokens ou caminhos locais sensiveis.
- [ ] Nenhum print mostra URLs sensiveis, logs reais ou banco real.

## Cuidados obrigatorios

- Nao exponha `.env`.
- Nao exponha `data/jobs.db`.
- Nao exponha logs reais em `logs/`.
- Nao exponha relatorios reais em `reports/`.
- Oculte e-mails, nomes pessoais, caminhos locais e URLs sensiveis.
- Prefira sempre `data/sample_jobs.db` e dados de `examples/sample_jobs.csv`.

## Fluxo recomendado

1. Gere o banco ficticio:

```bat
python scripts\load_sample_data.py
```

2. Abra o dashboard:

```bat
streamlit run dashboard.py
```

3. Selecione `Dados ficticios`.
4. Capture as abas na ordem do checklist.
5. Salve as imagens em `docs/images/`.
6. Revise cada imagem manualmente antes de publicar.

## Passo a passo final

1. Rode:

```bat
python scripts\load_sample_data.py
```

2. Abra o dashboard:

```bat
streamlit run dashboard.py
```

3. No menu lateral, selecione `Dados ficticios`.
4. Capture cada aba indicada no checklist.
5. Salve os PNGs finais em `docs/images/`.
6. Compare cada PNG com seu placeholder `.placeholder.txt`.
7. Revise se nao ha dado real, e-mail, token, caminho local sensivel, banco real, log real ou URL privada.
8. Rode:

```bat
python scripts\check_publication_safety.py
```

## Checklist de privacidade antes de publicar

- [ ] O dashboard esta em `Dados ficticios`.
- [ ] Nenhuma imagem mostra `.env`.
- [ ] Nenhuma imagem mostra `data/jobs.db`.
- [ ] Nenhuma imagem mostra logs reais.
- [ ] Nenhuma imagem mostra relatorios reais.
- [ ] Nenhuma imagem mostra e-mail real.
- [ ] Nenhuma imagem mostra credenciais, tokens ou senhas.
- [ ] Nenhuma imagem mostra caminhos locais sensiveis.
- [ ] Nenhuma imagem mostra URLs privadas ou sensiveis.
- [ ] `python scripts\check_publication_safety.py` passou antes da publicacao.
